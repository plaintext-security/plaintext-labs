# Bundled curriculum snapshot

`tracks/` is a **committed snapshot** of the Markdown curriculum from the
[`plaintext`](https://github.com/plaintext-security/plaintext) repo (`tracks/`) — only the
`README.md` (track + module concept/Learn) and `lab.md` files, no build output. It ships here
so the curriculum MCP server runs with **zero network and no second clone**.

It will drift from the live curriculum over time. To tutor over the latest, point the server
at a fresh checkout instead of this snapshot:

```bash
export CURRICULUM_DIR=/path/to/plaintext/tracks
```

To refresh the snapshot from a sibling `../plaintext` checkout, re-copy the `*.md` files
preserving the `<track>/{README.md,modules/<module>/{README,lab}.md}` layout.
