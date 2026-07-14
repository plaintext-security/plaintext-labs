# Pester v5 tests for the Vigil MCP surface. `make demo` runs these on a clean runner to prove:
#   (a) a well-formed tools/call returns typed objects,
#   (b) each hostile/malformed tool argument is REJECTED BY VALIDATION (not by luck),
#   (c) no state-changing verb is exposed by the surface.
# All offline: no live LLM, no network - the handler is driven directly with JSON-RPC payloads.

BeforeAll {
    Import-Module "$PSScriptRoot/Vigil/Vigil.psd1" -Force
}

Describe 'Vigil MCP surface - happy path' {
    It 'lists only the two read-only tools' {
        $resp = Invoke-VigilMcpRequest -Json '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | ConvertFrom-Json
        $names = $resp.result.tools.name
        $names | Should -Contain 'Get-VigilEvent'
        $names | Should -Contain 'Read-VigilEnrichment'
        $names.Count | Should -Be 2
    }

    It 'returns objects (not an error) for a well-formed Get-VigilEvent call' {
        $call = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"Get-VigilEvent","arguments":{"source":"sample","severity":"Suspicious"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -BeNullOrEmpty
        $resp.result.isError | Should -BeFalse
        # The tool result carries the three suspicious events from the sample, as objects.
        $events = $resp.result.content[0].text | ConvertFrom-Json
        ($events | Where-Object Suspicious).Count | Should -Be 3
    }

    It 'enriches a known-malicious indicator as a typed verdict' {
        $call = '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"Read-VigilEnrichment","arguments":{"indicator":"185.220.101.7"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -BeNullOrEmpty
        $verdict = $resp.result.content[0].text | ConvertFrom-Json
        $verdict.Verdict | Should -Be 'malicious'
    }
}

Describe 'Vigil MCP surface - hostile arguments are rejected by validation' {
    It 'rejects a path-traversal source with a JSON-RPC error (not a file read)' {
        $call = '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"Get-VigilEvent","arguments":{"source":"../../etc/passwd"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -Not -BeNullOrEmpty
        $resp.result | Should -BeNullOrEmpty
    }

    It 'rejects an out-of-set severity (injection-looking value)' {
        $call = '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"Get-VigilEvent","arguments":{"source":"sample","severity":"''; Remove-Item"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -Not -BeNullOrEmpty
    }

    It 'rejects an indicator carrying a path/command shape' {
        $call = '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"Read-VigilEnrichment","arguments":{"indicator":"../../secret; Remove-Item"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -Not -BeNullOrEmpty
    }

    It 'rejects a tools/call for a state-changing verb (not registered)' {
        $call = '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"Remove-VigilEvent","arguments":{"source":"sample"}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -Not -BeNullOrEmpty
        $resp.error.message | Should -Match 'unknown or non-exposed tool'
    }

    It 'rejects a missing required argument' {
        $call = '{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"Get-VigilEvent","arguments":{}}}'
        $resp = Invoke-VigilMcpRequest -Json $call | ConvertFrom-Json
        $resp.error | Should -Not -BeNullOrEmpty
    }
}

Describe 'Vigil MCP surface - the surface is read-only by construction' {
    It 'exposes no state-changing verb in the tool registry' {
        InModuleScope Vigil {
            foreach ($toolName in $script:VigilTools.Keys) {
                $toolName | Should -Not -Match $script:VigilForbiddenVerbPattern
            }
        }
    }

    It 'confines a validated path to the allowed data root' {
        InModuleScope Vigil {
            { Resolve-VigilSafePath -Candidate 'sample.json' } | Should -Not -Throw
            { Resolve-VigilSafePath -Candidate '../Vigil/Vigil.psm1' } | Should -Throw
            { Resolve-VigilSafePath -Candidate '/etc/passwd' } | Should -Throw
        }
    }
}
