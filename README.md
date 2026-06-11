# youtube-mcp-server

An [MCP](https://modelcontextprotocol.io) server that lets Claude discover **educational content on YouTube** — lectures, tutorials, full courses, and the channels behind them.

It's built for learning-focused discovery:

- **SafeSearch is always strict** — every query, no opt-out.
- **Educational category filters** — Education, Science & Technology, How-to & DIY.
- **Courses, not just clips** — playlists and channels are first-class, so Claude can find a complete lecture series and read its "syllabus", not just a single video.
- **Vetting data included** — duration, view counts, captions availability, and full descriptions so Claude can recommend quality material.

## Tools

| Tool | What it does |
|------|--------------|
| `search_videos` | Search videos with filters: category, length, captions, language, recency, sort order |
| `get_video_details` | Full description, stats, duration, and tags for specific videos |
| `search_playlists` | Find full courses and lecture series |
| `get_playlist_videos` | List a playlist's videos in order (the course syllabus) |
| `search_channels` | Find educational creators and institutions |
| `get_channel_videos` | A channel's most recent uploads |
| `get_trending_educational` | What's trending in YouTube's Education category, by country |

## Requirements (macOS)

1. **Node.js 18 or newer**

   ```bash
   brew install node     # or download from https://nodejs.org
   node --version        # should print v18+ 
   ```

2. **A YouTube Data API v3 key** (free)

   1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
   2. Create a project (or pick an existing one).
   3. Open **APIs & Services → Library**, search for **YouTube Data API v3**, and click **Enable**.
   4. Open **APIs & Services → Credentials → Create credentials → API key** and copy the key.
   5. Recommended: click the key, and under **API restrictions** restrict it to the *YouTube Data API v3* only.

   The free quota is **10,000 units/day**. A search costs 100 units; detail lookups cost ~1. That's roughly 90+ searches per day — plenty for personal use.

## Install

```bash
git clone https://github.com/patrickdaj/youtube-mcp-server.git
cd youtube-mcp-server
npm install
```

Note the absolute path of the checkout — you'll need it below:

```bash
pwd   # e.g. /Users/you/youtube-mcp-server
```

## Add to Claude Desktop

Edit (or create) the config file:

```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add the server under `mcpServers`, using **absolute paths** and your API key:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "node",
      "args": ["/Users/you/youtube-mcp-server/src/index.js"],
      "env": {
        "YOUTUBE_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Then **quit Claude Desktop fully (⌘Q) and reopen it**. You should see the `youtube` server listed under the tools (🔌) icon in a new conversation.

## Add to Claude Code

From any terminal:

```bash
claude mcp add youtube \
  --env YOUTUBE_API_KEY=YOUR_API_KEY_HERE \
  -- node /Users/you/youtube-mcp-server/src/index.js
```

Verify it's connected:

```bash
claude mcp list
```

(or run `/mcp` inside a Claude Code session). Add `--scope user` to the `claude mcp add` command if you want the server available in every project rather than just the current one.

## Try it

Ask Claude things like:

- *"Find me a full university-level course on linear algebra on YouTube, and show me the first ten lectures."*
- *"Search YouTube for short explainers on photosynthesis with captions, suitable for a middle schooler."*
- *"Find the best channels for learning Rust, and show me the latest uploads from the top one."*
- *"What educational videos are trending in the US right now?"*
- *"Compare these two videos and tell me which is the better intro"* (Claude will pull full details for both).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Server doesn't appear in Claude Desktop | Make sure the path in `args` is **absolute**, the JSON is valid (no trailing commas), and you fully quit (⌘Q) and reopened the app. |
| `YOUTUBE_API_KEY environment variable is not set` | The key goes in the `env` block of the config (Desktop) or the `--env` flag (Claude Code), not your shell profile — GUI apps don't read your shell rc files. |
| `spawn node ENOENT` in Desktop logs | Claude Desktop can't find `node` on its PATH. Use the full path to node as the `command` — find it with `which node` (e.g. `/opt/homebrew/bin/node`). |
| `quota` errors | You've used the free 10,000 daily units (≈90 searches). It resets at midnight Pacific Time. |
| `API key not valid` | The YouTube Data API v3 isn't enabled on the key's project, or the key is restricted to other APIs. |

Desktop logs live at `~/Library/Logs/Claude/mcp-server-youtube.log` if you need to dig deeper.

## Notes

- This server is **read-only** — it only calls YouTube's public search/list endpoints. It never posts, rates, or modifies anything, and it doesn't use OAuth or touch your YouTube account.
- Your API key stays local: it's read from the environment and sent only to `googleapis.com`.

## License

[MIT](LICENSE)
