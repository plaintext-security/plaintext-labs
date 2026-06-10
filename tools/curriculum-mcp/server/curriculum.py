#!/usr/bin/env python3
"""Parse and index the Plaintext security curriculum.

This module is the *brains* of the curriculum MCP server, and it is deliberately
**pure standard library** — no `mcp`, no third-party packages. That separation is on
purpose: the parsing/indexing/search logic can be imported, compiled, and smoke-tested
fully offline (see ../tests/smoke_test.py), while server.py is the thin MCP wiring on top.

The curriculum is the Markdown under `plaintext/tracks/`:

    tracks/
      <NN-track>/
        README.md                       # track overview / content map
        modules/<MM-module>/
          README.md                     # concept ("the bridge") + Learn path
          lab.md                        # hands-on project

We index every track, module README, and lab.md, then expose lookup/search/Learn-path
extraction over the result. A small curated snapshot of the curriculum ships in
`data/tracks/` so the lab runs with zero network and zero second clone; point
CURRICULUM_DIR at a full `plaintext/tracks` checkout to tutor over the whole thing.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# tracks/<NN>-<name>  and  modules/<MM>-<name>
_NUM_PREFIX = re.compile(r"^(\d{2})-(.+)$")
# A markdown link:  [text](url)
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# An ATX heading line:  ## Heading
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")


def _strip_num_prefix(name: str) -> str:
    """`12-ai-augmented-ops` -> `ai-augmented-ops`; leaves un-prefixed names alone."""
    m = _NUM_PREFIX.match(name)
    return m.group(2) if m else name


def _slug_to_title(slug: str) -> str:
    """`05-building-mcp-servers` -> `Building Mcp Servers` (display fallback)."""
    m = _NUM_PREFIX.match(slug)
    body = m.group(2) if m else slug
    return body.replace("-", " ").title()


@dataclass
class Resource:
    """One curated link from a module's Learn path."""

    title: str
    url: str
    note: str = ""
    group: str = ""  # the bold sub-topic heading it sat under, if any


@dataclass
class Module:
    track_id: str            # e.g. "12-ai-augmented-ops"
    module_id: str           # e.g. "05-building-mcp-servers"
    number: str              # e.g. "05"
    title: str               # parsed from the README H1, else derived from slug
    readme_path: Path
    lab_path: Path | None
    sections: dict[str, str] = field(default_factory=dict)   # README "## X" -> body
    lab_sections: dict[str, str] = field(default_factory=dict)
    learn: list[Resource] = field(default_factory=list)
    readme_text: str = ""
    lab_text: str = ""

    @property
    def ref(self) -> str:
        """Stable handle a tool caller passes around, e.g. '12-ai-augmented-ops/05-building-mcp-servers'."""
        return f"{self.track_id}/{self.module_id}"

    def summary(self) -> str:
        why = self.sections.get("Why this matters", "").strip()
        obj = self.sections.get("Objective", "").strip()
        return (why or obj or "").split("\n\n")[0].strip()


@dataclass
class Track:
    track_id: str            # "12-ai-augmented-ops"
    number: str              # "12"
    title: str               # parsed from track README H1, else derived
    readme_path: Path | None
    overview: str = ""       # leading prose of the track README
    modules: list[Module] = field(default_factory=list)


def _parse_sections(text: str) -> dict[str, str]:
    """Split Markdown into a {H2-heading-text: body} map (H2 == '## ')."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 2:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            # Drop a trailing "(~N hrs)" / "(~N min)" time-box so callers can match on a clean key.
            current = re.sub(r"\s*\(~?[^)]*\)\s*$", "", m.group(2)).strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _parse_h1(text: str, fallback: str) -> str:
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 1:
            # "# Module 05 — Building MCP Servers" -> keep as-is, it's already a title.
            return m.group(2).strip()
    return fallback


def _parse_learn(learn_body: str) -> list[Resource]:
    """Extract curated links from a Learn section, keeping the bold sub-topic grouping."""
    resources: list[Resource] = []
    group = ""
    for raw in learn_body.splitlines():
        line = raw.strip()
        if not line:
            continue
        # A bold-only line is a sub-topic group header: **Agent architecture (~1 hr)**
        bold = re.fullmatch(r"\*\*(.+?)\*\*", line)
        if bold:
            group = re.sub(r"\s*\(~?[^)]*\)\s*$", "", bold.group(1)).strip()
            continue
        link = _MD_LINK.search(line)
        if link:
            title, url = link.group(1), link.group(2)
            # The note is the prose after the link, typically "] — why it earns the time".
            after = line[link.end():]
            note = after.lstrip(" —-:").strip()
            resources.append(Resource(title=title, url=url, note=note, group=group))
    return resources


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


class Curriculum:
    """An in-memory index of the Plaintext curriculum, built once at startup."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).resolve()
        self.tracks: list[Track] = []
        self._modules_by_ref: dict[str, Module] = {}
        self._load()

    # ---- loading -------------------------------------------------------

    def _load(self) -> None:
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"curriculum directory not found: {self.root} "
                f"(set CURRICULUM_DIR to a plaintext/tracks checkout)"
            )
        for track_dir in sorted(self.root.glob("[0-9][0-9]-*")):
            if not track_dir.is_dir():
                continue
            self.tracks.append(self._load_track(track_dir))

    def _load_track(self, track_dir: Path) -> Track:
        m = _NUM_PREFIX.match(track_dir.name)
        number = m.group(1) if m else ""
        readme = track_dir / "README.md"
        readme_text = _read(readme) if readme.is_file() else ""
        title = _parse_h1(readme_text, _slug_to_title(track_dir.name))
        # Track overview = prose between the H1 and the first H2.
        overview = ""
        if readme_text:
            sections_split = re.split(r"^## ", readme_text, maxsplit=1, flags=re.M)
            head = sections_split[0]
            overview = re.sub(r"^#.*$", "", head, count=1, flags=re.M).strip()

        track = Track(
            track_id=track_dir.name,
            number=number,
            title=title,
            readme_path=readme if readme.is_file() else None,
            overview=overview,
        )

        modules_dir = track_dir / "modules"
        if modules_dir.is_dir():
            for module_dir in sorted(modules_dir.glob("[0-9][0-9]-*")):
                if module_dir.is_dir():
                    mod = self._load_module(track, module_dir)
                    track.modules.append(mod)
                    self._modules_by_ref[mod.ref] = mod
        return track

    def _load_module(self, track: Track, module_dir: Path) -> Module:
        m = _NUM_PREFIX.match(module_dir.name)
        number = m.group(1) if m else ""
        readme = module_dir / "README.md"
        lab = module_dir / "lab.md"
        readme_text = _read(readme)
        lab_text = _read(lab) if lab.is_file() else ""

        sections = _parse_sections(readme_text)
        lab_sections = _parse_sections(lab_text) if lab_text else {}
        title = _parse_h1(readme_text, _slug_to_title(module_dir.name))

        learn: list[Resource] = []
        for key, body in sections.items():
            if key.lower().startswith("learn"):
                learn = _parse_learn(body)
                break

        return Module(
            track_id=track.track_id,
            module_id=module_dir.name,
            number=number,
            title=title,
            readme_path=readme,
            lab_path=lab if lab.is_file() else None,
            sections=sections,
            lab_sections=lab_sections,
            learn=learn,
            readme_text=readme_text,
            lab_text=lab_text,
        )

    # ---- query ---------------------------------------------------------

    def all_modules(self) -> list[Module]:
        return [mod for tr in self.tracks for mod in tr.modules]

    def get_track(self, track_ref: str) -> Track | None:
        track_ref = track_ref.strip()
        for tr in self.tracks:
            if tr.track_id == track_ref or tr.number == track_ref:
                return tr
        # Loose match, ranked: prefer the id (the slug after the number) over the title,
        # and a word-boundary hit over a mid-word one ("ai" should pick ai-augmented-ops,
        # not "Cont-ai-ner Security"). Deterministic: ties break on track number.
        low = track_ref.lower()
        best: tuple[int, str, Track] | None = None
        for tr in self.tracks:
            slug = _strip_num_prefix(tr.track_id).lower()  # "ai-augmented-ops"
            title = tr.title.lower()
            rank = 0
            if re.search(rf"\b{re.escape(low)}", slug):
                rank = 4
            elif low in slug:
                rank = 3
            elif re.search(rf"\b{re.escape(low)}", title):
                rank = 2
            elif low in title:
                rank = 1
            if rank and (best is None or rank > best[0]):
                best = (rank, tr.number, tr)
        return best[2] if best else None

    def get_module(self, ref: str) -> Module | None:
        """Resolve a module by 'track/module' ref, or a loose 'track module' / number pair."""
        ref = ref.strip()
        if ref in self._modules_by_ref:
            return self._modules_by_ref[ref]
        # Accept "12-ai-augmented-ops/5", "ai/05", "ai-augmented-ops/building-mcp".
        if "/" in ref:
            track_part, mod_part = (p.strip() for p in ref.split("/", 1))
            track = self.get_track(track_part)
            if track:
                hit = self._match_module_in_track(track, mod_part)
                if hit:
                    return hit
        return None

    @staticmethod
    def _match_module_in_track(track: Track, mod_part: str) -> Module | None:
        mp = mod_part.lower()
        num = mp.zfill(2) if mp.isdigit() else None
        for mod in track.modules:
            if mod.module_id == mod_part or (num and mod.number == num):
                return mod
        for mod in track.modules:
            if mp in mod.module_id.lower() or mp in mod.title.lower():
                return mod
        return None

    def search(self, query: str, limit: int = 10) -> list[tuple[Module, int, str]]:
        """Keyword search across module titles, prose, Learn links, and labs.

        Returns (module, score, snippet) tuples, best first. Pure substring/term
        scoring — deterministic and offline, no embeddings.
        """
        terms = [t for t in re.split(r"\s+", query.lower().strip()) if t]
        if not terms:
            return []
        scored: list[tuple[Module, int, str]] = []
        for mod in self.all_modules():
            title = mod.title.lower()
            body = (mod.readme_text + "\n" + mod.lab_text).lower()
            score = 0
            for term in terms:
                # Title hits are worth more than body hits.
                score += 5 * title.count(term)
                score += body.count(term)
            if score:
                scored.append((mod, score, self._snippet(mod, terms)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    @staticmethod
    def _snippet(mod: Module, terms: list[str]) -> str:
        haystack = mod.readme_text
        low = haystack.lower()
        for term in terms:
            idx = low.find(term)
            if idx != -1:
                start = max(0, idx - 80)
                end = min(len(haystack), idx + 120)
                frag = haystack[start:end].replace("\n", " ").strip()
                return ("…" if start else "") + frag + ("…" if end < len(haystack) else "")
        return mod.summary()[:200]

    def suggest_next(self, ref: str) -> Module | None:
        """The next module in the same track, by number (a simple learning path)."""
        mod = self.get_module(ref)
        if not mod:
            return None
        track = self.get_track(mod.track_id)
        if not track:
            return None
        ordered = track.modules
        for i, m in enumerate(ordered):
            if m.ref == mod.ref and i + 1 < len(ordered):
                return ordered[i + 1]
        return None

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict[str, int]:
        mods = self.all_modules()
        return {
            "tracks": len(self.tracks),
            "modules": len(mods),
            "labs": sum(1 for m in mods if m.lab_path),
            "learn_resources": sum(len(m.learn) for m in mods),
        }


def default_curriculum_dir() -> Path:
    """Resolve the curriculum source, in priority order.

    1. CURRICULUM_DIR env var (a full `plaintext/tracks` checkout — best, whole curriculum).
    2. The bundled snapshot shipped beside this server (`../data/tracks`) — zero-setup default.
    """
    env = os.environ.get("CURRICULUM_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "tracks"


def load_default() -> Curriculum:
    return Curriculum(default_curriculum_dir())
