function Invoke-VigilEnrichment {
    <#
    .SYNOPSIS
        Enriches indicators (IPs) against a threat feed CONCURRENTLY, with a throttle
        limit, retry/backoff, and no shared-state races.
    .DESCRIPTION
        Takes indicators - typically the DestinationIp values pulled off VigilEvent
        objects - and looks each one up against an abuse.ch Feodo Tracker snapshot
        (a local CSV, so the lab runs offline and deterministic). Lookups run in
        parallel via ForEach-Object -Parallel with a bounded -ThrottleLimit so a real
        feed API is never hammered.

        The correctness lessons this function exists to teach:
          * $using: is required to read outer-scope variables inside -Parallel.
          * results are collected in a thread-safe [ConcurrentBag], never a plain
            array with += (which races and silently drops results across threads).
          * each lookup is wrapped in bounded retry with exponential backoff, so a
            transient failure retries instead of poisoning the whole run.

        Duplicate indicators are de-duplicated before lookup, so each unique indicator
        is queried exactly once - the cheapest possible rate-limit win.
    .PARAMETER Indicator
        One or more indicator strings (IPs) to enrich. Accepts pipeline input.
    .PARAMETER FeedPath
        Path to the feed snapshot CSV (abuse.ch Feodo Tracker IP blocklist format).
    .PARAMETER ThrottleLimit
        Maximum number of concurrent lookups. Bounds parallelism so a real API is not
        flooded. Defaults to 5.
    .PARAMETER MaxRetry
        Maximum retry attempts per indicator on a transient fault. Defaults to 3.
    .PARAMETER BaseDelayMs
        Base backoff delay in milliseconds; doubles each retry (exponential backoff).
        Defaults to 50.
    .EXAMPLE
        Get-VigilEvent -Path ./data/events.json |
            Select-Object -ExpandProperty DestinationIp |
            Invoke-VigilEnrichment -FeedPath ./data/feodo_ipblocklist.csv |
            Where-Object Malicious
    .NOTES
        To enrich against the LIVE feed instead of the snapshot, download it first and
        point -FeedPath at it (keep network I/O out of the parallel body):
            Invoke-RestMethod 'https://feodotracker.abuse.ch/downloads/ipblocklist.csv' |
                Set-Content ./feodo_live.csv
    #>
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNullOrEmpty()]
        [string[]]$Indicator,

        [Parameter(Mandatory)]
        [ValidateScript({ Test-Path -Path $_ -PathType Leaf })]
        [string]$FeedPath,

        [ValidateRange(1, 32)]
        [int]$ThrottleLimit = 5,

        [ValidateRange(1, 10)]
        [int]$MaxRetry = 3,

        [ValidateRange(1, 5000)]
        [int]$BaseDelayMs = 50
    )

    begin {
        # Accumulate all pipeline input, then enrich once at the end so the whole set
        # is de-duplicated and parallelised together (not one lookup per pipeline item).
        $collected = [System.Collections.Generic.List[string]]::new()
    }

    process {
        foreach ($i in $Indicator) {
            if (-not [string]::IsNullOrWhiteSpace($i)) {
                $collected.Add($i.Trim())
            }
        }
    }

    end {
        # Load the feed ONCE, on this thread, into a plain hashtable keyed by IP.
        # Reading the CSV inside every parallel iteration would be wasteful and racy.
        $feed = @{}
        Import-Csv -Path $FeedPath |
            Where-Object { $_.dst_ip } |
            ForEach-Object {
                $feed[$_.dst_ip] = [pscustomobject]@{
                    Malware   = $_.malware
                    C2Status  = $_.c2_status
                    FirstSeen = $_.first_seen_utc
                }
            }

        # De-duplicate: query each unique indicator exactly once.
        $unique = $collected | Sort-Object -Unique

        # Thread-safe result sink. A plain @() with += races across runspaces and
        # silently loses results; a ConcurrentBag is safe for concurrent Add().
        $bag = [System.Collections.Concurrent.ConcurrentBag[pscustomobject]]::new()

        $unique | ForEach-Object -ThrottleLimit $ThrottleLimit -Parallel {
            # $using: is REQUIRED - the parallel body is a separate runspace and cannot
            # see outer-scope variables without it.
            $ind      = $_
            $feedLdc  = $using:feed
            $sink     = $using:bag
            $maxRetry = $using:MaxRetry
            $baseMs   = $using:BaseDelayMs

            # The lookup, wrapped in bounded retry with exponential backoff. Against the
            # local snapshot this never faults; the retry loop is the shape you keep when
            # -Look is a real HTTP call to the abuse.ch API that can 429 or time out.
            $attempt = 0
            $result  = $null
            while ($true) {
                $attempt++
                try {
                    $hit = $feedLdc[$ind]
                    $result = [pscustomobject]@{
                        Indicator = $ind
                        Malicious = [bool]$hit
                        Malware   = if ($hit) { $hit.Malware } else { $null }
                        C2Status  = if ($hit) { $hit.C2Status } else { $null }
                        FirstSeen = if ($hit) { $hit.FirstSeen } else { $null }
                        Attempts  = $attempt
                        Source    = 'feodotracker-snapshot'
                    }
                    break
                }
                catch {
                    if ($attempt -ge $maxRetry) {
                        $result = [pscustomobject]@{
                            Indicator = $ind
                            Malicious = $false
                            Malware   = $null
                            C2Status  = $null
                            FirstSeen = $null
                            Attempts  = $attempt
                            Source    = 'error'
                        }
                        break
                    }
                    # Exponential backoff: baseMs * 2^(attempt-1).
                    Start-Sleep -Milliseconds ($baseMs * [math]::Pow(2, $attempt - 1))
                }
            }

            $sink.Add($result)
        }

        # Emit in a stable order so output is deterministic across runs.
        $bag.ToArray() | Sort-Object Indicator
    }
}
