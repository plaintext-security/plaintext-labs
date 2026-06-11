#!/usr/bin/env node
/**
 * youtube-mcp-server — MCP server for discovering educational content on YouTube.
 *
 * Exposes YouTube Data API v3 search and lookup as MCP tools, tuned for an
 * educational use case: SafeSearch is always strict, results can be filtered
 * to educational categories, and playlists/channels are first-class so Claude
 * can find full courses and lecture series, not just one-off videos.
 *
 * Requires the YOUTUBE_API_KEY environment variable (a YouTube Data API v3 key).
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_BASE = "https://www.googleapis.com/youtube/v3";
const API_KEY = process.env.YOUTUBE_API_KEY;

if (!API_KEY) {
  console.error(
    "youtube-mcp-server: the YOUTUBE_API_KEY environment variable is not set.\n" +
      "Create a YouTube Data API v3 key at https://console.cloud.google.com/apis/credentials\n" +
      "and pass it via the `env` block of your Claude MCP configuration (see README.md)."
  );
  process.exit(1);
}

// YouTube category IDs most relevant to learning content.
const CATEGORY_IDS = {
  education: "27",
  science_technology: "28",
  howto_diy: "26",
};

// ---------------------------------------------------------------------------
// YouTube API helpers
// ---------------------------------------------------------------------------

async function yt(endpoint, params) {
  const url = new URL(`${API_BASE}/${endpoint}`);
  url.searchParams.set("key", API_KEY);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error?.message) detail = body.error.message;
    } catch {
      // non-JSON error body; keep the HTTP status
    }
    if (res.status === 403 && /quota/i.test(detail)) {
      detail +=
        " — the YouTube Data API free quota (10,000 units/day) has been used up." +
        " It resets at midnight Pacific Time.";
    }
    throw new Error(`YouTube API error: ${detail}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Transcript helpers (YouTube's public caption endpoint — not the Data API)
// ---------------------------------------------------------------------------

const BROWSER_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.9",
  Cookie: "CONSENT=YES+cb",
};

/** Extract a balanced JSON array assigned to `"key":[...]` inside a blob of HTML/JS. */
function extractJsonArray(html, key) {
  const idx = html.indexOf(`"${key}":[`);
  if (idx === -1) return null;
  const start = html.indexOf("[", idx);
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < html.length; i++) {
    const c = html[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
    } else if (c === '"') {
      inStr = true;
    } else if (c === "[") {
      depth++;
    } else if (c === "]") {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(html.slice(start, i + 1));
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}

async function fetchCaptionTracks(videoId) {
  const res = await fetch(
    `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}&hl=en`,
    { headers: BROWSER_HEADERS }
  );
  if (!res.ok) {
    throw new Error(`Could not load the video page for ${videoId} (HTTP ${res.status}).`);
  }
  const html = await res.text();
  const tracks = extractJsonArray(html, "captionTracks");
  if (!tracks || tracks.length === 0) {
    const status = html.match(/"playabilityStatus":\s*\{\s*"status":"([A-Z_]+)"/)?.[1];
    if (status && status !== "OK") {
      throw new Error(
        `No transcript available: video ${videoId} is not playable (status: ${status}) — ` +
          "it may be private, deleted, age-restricted, or region-locked."
      );
    }
    throw new Error(
      `Video ${videoId} has no captions (neither manual nor auto-generated). ` +
        "Tip: search_videos with captions_required=true finds videos that have transcripts."
    );
  }
  return tracks;
}

/** Pick the best caption track: requested language if given, manual over auto-generated. */
function pickTrack(tracks, language) {
  let pool = tracks;
  if (language) {
    const want = language.toLowerCase().split("-")[0];
    pool = tracks.filter(
      (t) => (t.languageCode ?? "").toLowerCase().split("-")[0] === want
    );
    if (pool.length === 0) {
      const available = tracks
        .map((t) => `${t.languageCode}${t.kind === "asr" ? " (auto)" : ""}`)
        .join(", ");
      throw new Error(
        `No '${language}' transcript for this video. Available: ${available}`
      );
    }
  }
  return pool.find((t) => t.kind !== "asr") ?? pool[0];
}

/** Download a caption track and return [{t: seconds, text}] segments. */
async function fetchTranscriptSegments(track) {
  const url = `${track.baseUrl}${track.baseUrl.includes("?") ? "&" : "?"}fmt=json3`;
  const res = await fetch(url, { headers: BROWSER_HEADERS });
  if (!res.ok) {
    throw new Error(
      `Could not download the transcript (HTTP ${res.status}). YouTube sometimes ` +
        "blocks automated transcript fetches — wait a bit and try again."
    );
  }
  const data = await res.json();
  const segments = [];
  for (const ev of data.events ?? []) {
    if (!ev.segs) continue;
    const t = (ev.tStartMs ?? 0) / 1000;
    const content = ev.segs
      .map((s) => s.utf8 ?? "")
      .join("")
      .replace(/\s+/g, " ")
      .trim();
    if (content) segments.push({ t, text: content });
  }
  return segments;
}

function fmtTimestamp(sec) {
  const s = Math.floor(sec % 60);
  const m = Math.floor(sec / 60) % 60;
  const h = Math.floor(sec / 3600);
  const ss = String(s).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${ss}` : `${m}:${ss}`;
}

/** Fetch full details (duration, stats) for up to 50 video IDs. */
async function fetchVideoDetails(ids) {
  if (ids.length === 0) return new Map();
  const data = await yt("videos", {
    part: "snippet,contentDetails,statistics",
    id: ids.join(","),
    maxResults: ids.length,
  });
  return new Map((data.items ?? []).map((v) => [v.id, v]));
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function fmtDuration(iso) {
  if (!iso) return "unknown length";
  const m = iso.match(/^P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/);
  if (!m) return iso;
  const [, h, min, s] = m;
  const parts = [];
  if (h) parts.push(`${h}h`);
  if (min) parts.push(`${min}m`);
  if (s && !h) parts.push(`${s}s`);
  return parts.length ? parts.join(" ") : "live/0s";
}

function fmtCount(n) {
  const num = Number(n);
  if (!Number.isFinite(num)) return "n/a";
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return String(num);
}

function truncate(text, max) {
  if (!text) return "";
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > max ? `${clean.slice(0, max)}…` : clean;
}

function fmtVideo(id, snippet, details, { fullDescription = false } = {}) {
  const lines = [
    `### ${snippet.title}`,
    `- Video ID: ${id}`,
    `- URL: https://www.youtube.com/watch?v=${id}`,
    `- Channel: ${snippet.channelTitle} (ID: ${snippet.channelId})`,
    `- Published: ${(snippet.publishedAt ?? "").slice(0, 10)}`,
  ];
  if (details?.contentDetails) {
    lines.push(`- Duration: ${fmtDuration(details.contentDetails.duration)}`);
    if (details.contentDetails.caption === "true") {
      lines.push("- Captions: available");
    }
  }
  if (details?.statistics) {
    const { viewCount, likeCount } = details.statistics;
    lines.push(
      `- Views: ${fmtCount(viewCount)}${likeCount ? ` | Likes: ${fmtCount(likeCount)}` : ""}`
    );
  }
  const desc = fullDescription
    ? truncate(details?.snippet?.description ?? snippet.description, 1500)
    : truncate(snippet.description, 200);
  if (desc) lines.push(`- Description: ${desc}`);
  if (fullDescription && details?.snippet?.tags?.length) {
    lines.push(`- Tags: ${details.snippet.tags.slice(0, 10).join(", ")}`);
  }
  return lines.join("\n");
}

function text(s) {
  return { content: [{ type: "text", text: s }] };
}

/** Wrap a tool handler so API errors come back as readable tool errors. */
function safe(handler) {
  return async (args) => {
    try {
      return await handler(args);
    } catch (err) {
      return {
        content: [{ type: "text", text: String(err?.message ?? err) }],
        isError: true,
      };
    }
  };
}

// ---------------------------------------------------------------------------
// Server and tools
// ---------------------------------------------------------------------------

const server = new McpServer({
  name: "youtube-discovery",
  version: "1.0.0",
});

server.registerTool(
  "search_videos",
  {
    title: "Search YouTube videos",
    description:
      "Search YouTube for videos, tuned for educational discovery (lectures, tutorials, " +
      "explainers). SafeSearch is always strict. Filter by educational category, video " +
      "length, caption availability, language, and recency. Results include duration and " +
      "view counts. Use get_video_details for a video's full description.",
    inputSchema: {
      query: z.string().describe("What to search for, e.g. 'linear algebra eigenvalues lecture'"),
      max_results: z.number().int().min(1).max(25).default(10)
        .describe("Number of results to return (1-25, default 10)"),
      category: z.enum(["education", "science_technology", "howto_diy", "any"]).default("any")
        .describe(
          "Restrict to a YouTube category. 'education' = formal lectures/courses, " +
            "'science_technology' = science and tech explainers, 'howto_diy' = practical " +
            "how-to content. 'any' (default) searches all categories — many great " +
            "educational videos are not categorized as Education, so only restrict when " +
            "results are too noisy."
        ),
      duration: z.enum(["any", "short", "medium", "long"]).default("any")
        .describe("Video length: short < 4 min, medium 4-20 min, long > 20 min"),
      captions_required: z.boolean().default(false)
        .describe("Only return videos with closed captions (useful for accessibility and language learners)"),
      order: z.enum(["relevance", "view_count", "rating", "date"]).default("relevance")
        .describe("Sort order for results"),
      published_after: z.string().optional()
        .describe("Only videos published after this date, e.g. '2024-01-01' (useful for fast-moving topics)"),
      language: z.string().optional()
        .describe("Prefer results in this language (ISO 639-1 code, e.g. 'en', 'es')"),
    },
  },
  safe(async ({ query, max_results, category, duration, captions_required, order, published_after, language }) => {
    const params = {
      part: "snippet",
      type: "video",
      safeSearch: "strict",
      q: query,
      maxResults: max_results,
      order: order === "view_count" ? "viewCount" : order,
      relevanceLanguage: language,
    };
    if (category !== "any") params.videoCategoryId = CATEGORY_IDS[category];
    if (duration !== "any") params.videoDuration = duration;
    if (captions_required) params.videoCaption = "closedCaption";
    if (published_after) {
      params.publishedAfter = /^\d{4}-\d{2}-\d{2}$/.test(published_after)
        ? `${published_after}T00:00:00Z`
        : published_after;
    }

    const data = await yt("search", params);
    const items = data.items ?? [];
    if (items.length === 0) {
      return text(`No videos found for "${query}" with those filters. Try category 'any' or fewer filters.`);
    }
    const details = await fetchVideoDetails(items.map((i) => i.id.videoId));
    const body = items
      .map((i) => fmtVideo(i.id.videoId, i.snippet, details.get(i.id.videoId)))
      .join("\n\n");
    return text(`Found ${items.length} video(s) for "${query}":\n\n${body}`);
  })
);

server.registerTool(
  "get_video_details",
  {
    title: "Get video details",
    description:
      "Get full details for one or more YouTube videos by ID: complete description, " +
      "duration, view/like counts, captions availability, and tags. Use this to vet a " +
      "video found via search before recommending it.",
    inputSchema: {
      video_ids: z.array(z.string()).min(1).max(25)
        .describe("YouTube video IDs (the 11-character ID from search results or a watch URL)"),
    },
  },
  safe(async ({ video_ids }) => {
    const data = await yt("videos", {
      part: "snippet,contentDetails,statistics",
      id: video_ids.join(","),
    });
    const items = data.items ?? [];
    if (items.length === 0) return text("No videos found for those IDs.");
    const body = items
      .map((v) => fmtVideo(v.id, v.snippet, v, { fullDescription: true }))
      .join("\n\n");
    const missing = video_ids.filter((id) => !items.some((v) => v.id === id));
    const note = missing.length ? `\n\nNot found (deleted/private?): ${missing.join(", ")}` : "";
    return text(body + note);
  })
);

server.registerTool(
  "get_transcript",
  {
    title: "Get a video's transcript",
    description:
      "Fetch the transcript (captions) of a YouTube video as plain text with periodic " +
      "[mm:ss] timestamps, so you can actually read, summarize, and verify the video's " +
      "content rather than judging it by metadata. Prefers human-made captions and falls " +
      "back to auto-generated ones. Long transcripts are paged — the result tells you the " +
      "offset_seconds to pass to get the next part. Uses YouTube's public caption " +
      "endpoint (not the Data API): costs no API quota, but is best-effort and only works " +
      "for videos that have captions.",
    inputSchema: {
      video_id: z.string()
        .describe("YouTube video ID (the 11-character ID from search results or a watch URL)"),
      language: z.string().optional()
        .describe("Preferred transcript language (ISO 639-1, e.g. 'en', 'es'). Defaults to the video's primary track."),
      offset_seconds: z.number().int().min(0).default(0)
        .describe("Start reading from this point in the video — use the value suggested by a previous truncated call to page through long transcripts"),
      max_chars: z.number().int().min(1000).max(50000).default(12000)
        .describe("Maximum characters of transcript text to return per call (default 12000)"),
    },
  },
  safe(async ({ video_id, language, offset_seconds, max_chars }) => {
    const tracks = await fetchCaptionTracks(video_id);
    const track = pickTrack(tracks, language);
    const segments = await fetchTranscriptSegments(track);
    if (segments.length === 0) {
      return text(`The caption track for ${video_id} exists but is empty.`);
    }

    let startIdx = segments.findIndex((s) => s.t >= offset_seconds);
    if (offset_seconds === 0) startIdx = 0;
    if (startIdx === -1) {
      return text(
        `offset_seconds=${offset_seconds} is past the end of the transcript ` +
          `(it ends around ${fmtTimestamp(segments[segments.length - 1].t)}).`
      );
    }

    let out = "";
    let lastMarker = -Infinity;
    let continueAt = null;
    for (let i = startIdx; i < segments.length; i++) {
      const seg = segments[i];
      let piece = "";
      if (seg.t - lastMarker >= 60) {
        piece += `\n\n[${fmtTimestamp(seg.t)}] `;
      }
      piece += `${seg.text} `;
      if (out.length + piece.length > max_chars) {
        continueAt = Math.floor(seg.t);
        break;
      }
      if (seg.t - lastMarker >= 60) lastMarker = seg.t;
      out += piece;
    }

    const trackLabel = `${track.languageCode}${track.kind === "asr" ? ", auto-generated" : ""}`;
    let header = `Transcript of ${video_id} (${trackLabel})`;
    if (offset_seconds > 0) header += `, from ${fmtTimestamp(offset_seconds)}`;
    const footer =
      continueAt !== null
        ? `\n\n[Transcript continues — call get_transcript again with offset_seconds=${continueAt} for the next part.]`
        : "\n\n[End of transcript.]";
    return text(`${header}:${out}${footer}`);
  })
);

server.registerTool(
  "search_channels",
  {
    title: "Search YouTube channels",
    description:
      "Find YouTube channels by topic, e.g. educational creators or institutions " +
      "('MIT OpenCourseWare', 'organic chemistry teacher'). Returns subscriber and video " +
      "counts so you can gauge an educator's catalog. Follow up with get_channel_videos.",
    inputSchema: {
      query: z.string().describe("Channel topic or name to search for"),
      max_results: z.number().int().min(1).max(25).default(10)
        .describe("Number of channels to return (1-25, default 10)"),
    },
  },
  safe(async ({ query, max_results }) => {
    const data = await yt("search", {
      part: "snippet",
      type: "channel",
      safeSearch: "strict",
      q: query,
      maxResults: max_results,
    });
    const items = data.items ?? [];
    if (items.length === 0) return text(`No channels found for "${query}".`);

    const ids = items.map((i) => i.id.channelId);
    const detailData = await yt("channels", {
      part: "snippet,statistics",
      id: ids.join(","),
    });
    const details = new Map((detailData.items ?? []).map((c) => [c.id, c]));

    const body = items
      .map((i) => {
        const id = i.id.channelId;
        const d = details.get(id);
        const stats = d?.statistics;
        const lines = [
          `### ${i.snippet.title}`,
          `- Channel ID: ${id}`,
          `- URL: https://www.youtube.com/channel/${id}`,
        ];
        if (stats) {
          lines.push(
            `- Subscribers: ${stats.hiddenSubscriberCount ? "hidden" : fmtCount(stats.subscriberCount)} | Videos: ${fmtCount(stats.videoCount)}`
          );
        }
        const desc = truncate(d?.snippet?.description ?? i.snippet.description, 300);
        if (desc) lines.push(`- About: ${desc}`);
        return lines.join("\n");
      })
      .join("\n\n");
    return text(`Found ${items.length} channel(s) for "${query}":\n\n${body}`);
  })
);

server.registerTool(
  "get_channel_videos",
  {
    title: "Get a channel's recent uploads",
    description:
      "List the most recent uploads from a YouTube channel (by channel ID, e.g. from " +
      "search_channels). Quota-efficient way to browse an educator's latest content.",
    inputSchema: {
      channel_id: z.string().describe("The channel ID (starts with 'UC')"),
      max_results: z.number().int().min(1).max(50).default(10)
        .describe("Number of recent uploads to return (1-50, default 10)"),
    },
  },
  safe(async ({ channel_id, max_results }) => {
    const chan = await yt("channels", { part: "snippet,contentDetails", id: channel_id });
    const channel = chan.items?.[0];
    const uploads = channel?.contentDetails?.relatedPlaylists?.uploads;
    if (!uploads) return text(`Channel ${channel_id} not found (channel IDs start with 'UC').`);

    const data = await yt("playlistItems", {
      part: "snippet,contentDetails",
      playlistId: uploads,
      maxResults: max_results,
    });
    const items = data.items ?? [];
    if (items.length === 0) return text(`Channel "${channel.snippet.title}" has no public uploads.`);

    const details = await fetchVideoDetails(items.map((i) => i.contentDetails.videoId));
    const body = items
      .map((i) => fmtVideo(i.contentDetails.videoId, i.snippet, details.get(i.contentDetails.videoId)))
      .join("\n\n");
    return text(`Latest ${items.length} upload(s) from "${channel.snippet.title}":\n\n${body}`);
  })
);

server.registerTool(
  "search_playlists",
  {
    title: "Search YouTube playlists",
    description:
      "Search YouTube for playlists — the best way to find complete courses, lecture " +
      "series, and structured curricula rather than single videos. Returns the video " +
      "count for each playlist. Follow up with get_playlist_videos to see the syllabus.",
    inputSchema: {
      query: z.string().describe("Topic to find a course/series for, e.g. 'intro to statistics full course'"),
      max_results: z.number().int().min(1).max(25).default(10)
        .describe("Number of playlists to return (1-25, default 10)"),
    },
  },
  safe(async ({ query, max_results }) => {
    const data = await yt("search", {
      part: "snippet",
      type: "playlist",
      safeSearch: "strict",
      q: query,
      maxResults: max_results,
    });
    const items = data.items ?? [];
    if (items.length === 0) return text(`No playlists found for "${query}".`);

    const ids = items.map((i) => i.id.playlistId);
    const detailData = await yt("playlists", { part: "contentDetails", id: ids.join(",") });
    const counts = new Map((detailData.items ?? []).map((p) => [p.id, p.contentDetails?.itemCount]));

    const body = items
      .map((i) => {
        const id = i.id.playlistId;
        const lines = [
          `### ${i.snippet.title}`,
          `- Playlist ID: ${id}`,
          `- URL: https://www.youtube.com/playlist?list=${id}`,
          `- Channel: ${i.snippet.channelTitle}`,
        ];
        const count = counts.get(id);
        if (count !== undefined) lines.push(`- Videos: ${count}`);
        const desc = truncate(i.snippet.description, 200);
        if (desc) lines.push(`- Description: ${desc}`);
        return lines.join("\n");
      })
      .join("\n\n");
    return text(`Found ${items.length} playlist(s) for "${query}":\n\n${body}`);
  })
);

server.registerTool(
  "get_playlist_videos",
  {
    title: "List videos in a playlist",
    description:
      "List the videos in a YouTube playlist, in order — effectively the syllabus of a " +
      "course or series found via search_playlists.",
    inputSchema: {
      playlist_id: z.string().describe("The playlist ID (often starts with 'PL')"),
      max_results: z.number().int().min(1).max(50).default(25)
        .describe("Number of videos to return from the start of the playlist (1-50, default 25)"),
    },
  },
  safe(async ({ playlist_id, max_results }) => {
    const data = await yt("playlistItems", {
      part: "snippet,contentDetails",
      playlistId: playlist_id,
      maxResults: max_results,
    });
    const items = data.items ?? [];
    if (items.length === 0) return text(`Playlist ${playlist_id} is empty or not found.`);

    const body = items
      .map((i) => {
        const pos = (i.snippet.position ?? 0) + 1;
        const vid = i.contentDetails.videoId;
        return `${pos}. ${i.snippet.title} — https://www.youtube.com/watch?v=${vid} (ID: ${vid})`;
      })
      .join("\n");
    const total = data.pageInfo?.totalResults;
    const header =
      total && total > items.length
        ? `Showing ${items.length} of ${total} videos in this playlist:`
        : `${items.length} video(s) in this playlist:`;
    return text(`${header}\n\n${body}`);
  })
);

server.registerTool(
  "get_trending_educational",
  {
    title: "Trending educational videos",
    description:
      "Get the videos currently trending in YouTube's Education category for a region. " +
      "Good for 'what are people learning right now' style discovery.",
    inputSchema: {
      region_code: z.string().length(2).default("US")
        .describe("Two-letter country code (ISO 3166-1), e.g. 'US', 'GB', 'IN'"),
      max_results: z.number().int().min(1).max(25).default(10)
        .describe("Number of videos to return (1-25, default 10)"),
    },
  },
  safe(async ({ region_code, max_results }) => {
    const data = await yt("videos", {
      part: "snippet,contentDetails,statistics",
      chart: "mostPopular",
      videoCategoryId: CATEGORY_IDS.education,
      regionCode: region_code.toUpperCase(),
      maxResults: max_results,
    });
    const items = data.items ?? [];
    if (items.length === 0) {
      return text(
        `No trending Education-category videos available for region ${region_code.toUpperCase()}. Try 'US' or use search_videos instead.`
      );
    }
    const body = items.map((v) => fmtVideo(v.id, v.snippet, v)).join("\n\n");
    return text(`Trending educational videos in ${region_code.toUpperCase()}:\n\n${body}`);
  })
);

// ---------------------------------------------------------------------------

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("youtube-mcp-server running on stdio");
