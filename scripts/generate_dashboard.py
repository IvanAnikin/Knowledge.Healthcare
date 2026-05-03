#!/usr/bin/env python3
"""
generate_dashboard.py
Generates a static HTML task dashboard from Markdown task/spec files.

Usage:
    python3 scripts/generate_dashboard.py

Output:
    dashboards/task-dashboard.html

The Markdown files remain the source of truth. This script only reads them.
Clicking a task card opens a structured detail modal — no server required.
"""

import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

TASK_DIRS = {
    "inbox":    BASE_DIR / "tasks" / "inbox",
    "triage":   BASE_DIR / "tasks" / "triage",
    "active":   BASE_DIR / "tasks" / "active",
    "backlog":  BASE_DIR / "tasks" / "backlog",
    "done":     BASE_DIR / "tasks" / "done",
    "tested":   BASE_DIR / "tasks" / "tested",
    "deployed": BASE_DIR / "tasks" / "deployed",
}

SPEC_DIRS = {
    "app-1":     BASE_DIR / "specs" / "app-1",
    "app-2":     BASE_DIR / "specs" / "app-2",
    "app-3":     BASE_DIR / "specs" / "app-3",
    "app-4":     BASE_DIR / "specs" / "app-4",
    "cross-app": BASE_DIR / "specs" / "cross-app",
}

CURRENT_PRIORITIES_FILE = BASE_DIR / "current-priorities.md"
OUTPUT_FILE = BASE_DIR / "dashboards" / "task-dashboard.html"

APP_LABELS = {
    "knowledge":  "Knowledge.Healthcare",
    "app-1":     "medical_advisor",
    "app-2":     "ANOTE_mobile",
    "app-3":     "ANOTE-web",
    "app-4":     "Health-Analysis",
    "cross-app": "cross-app",
    "unknown":   "unknown",
}

# Sections to extract from task files.
# Each entry: (field_key, list_of_heading_aliases)
RICH_SECTIONS = [
    ("problem",          ["problem", "summary", "description", "deferral note"]),
    ("desired_outcome",  ["desired outcome", "outcome", "goal"]),
    ("why_it_matters",   ["why it matters", "motivation", "rationale"]),
    ("constraints",      ["constraints", "constraint"]),
    ("affected_areas",   ["suspected affected areas", "affected areas", "affected files", "suspected areas"]),
    ("confirmed_facts",  ["confirmed facts", "facts"]),
    ("assumptions",      ["assumptions", "assumption"]),
    ("open_questions",   ["open questions", "unknowns", "unknown"]),
    ("dependencies",     ["dependencies", "depends on"]),
    ("notes",            ["notes", "note"]),
    ("triage_assessment",["triage assessment", "triage"]),
    ("reasoning",        ["reasoning"]),
    ("cross_app",        ["cross-app considerations", "cross app considerations"]),
]

# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------

def read_file_safe(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def extract_frontmatter_field(text: str, field: str) -> Optional[str]:
    """
    Extract a scalar metadata field. Supports:
      | Field | value |           (table row)
      **Field:** value            (bold label)
      - **Field:** value          (list bold label)
      - **Field**: value          (colon outside bold)
    """
    escaped_field = re.escape(field)
    pattern_table = re.compile(
        r"^\s*\|\s*\*{0,2}" + escaped_field + r"\*{0,2}\s*\|\s*(.+?)\s*\|\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    pattern_label_inside_bold = re.compile(
        r"^\s*[-*]?\s*\*{1,2}" + escaped_field + r":\*{1,2}\s*[|]?\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )
    pattern_label_outside_bold = re.compile(
        r"^\s*[-*]?\s*\*{1,2}" + escaped_field + r"\*{1,2}:\s*[|]?\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )
    for pat in (pattern_table, pattern_label_inside_bold, pattern_label_outside_bold):
        m = pat.search(text)
        if not m:
            continue
        val = m.group(1).strip().strip("|").strip()
        val = re.sub(r"\*+", "", val).strip()
        if val and val.lower() not in ("", "-", "n/a", "none", "tbd"):
            return val
    return None


def extract_h1(text: str) -> Optional[str]:
    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_section_text(text: str, heading_aliases: list[str]) -> Optional[str]:
    """
    Extract body text of the first section whose heading matches any alias.
    Returns raw Markdown text, or None if not found.
    """
    alias_pattern = "|".join(re.escape(a) for a in heading_aliases)
    section_re = re.compile(
        r"^(#{2,4})\s+(?:" + alias_pattern + r")\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    m = section_re.search(text)
    if not m:
        return None
    level = len(m.group(1))
    start = m.end()
    end_re = re.compile(r"^#{1," + str(level) + r"}\s", re.MULTILINE)
    end_m = end_re.search(text, start)
    body = text[start: end_m.start() if end_m else len(text)].strip()
    return body if body else None


def section_to_lines(raw: Optional[str]) -> list[str]:
    """Convert raw section text to a list of cleaned bullet strings."""
    if not raw:
        return []
    items = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or re.match(r"^\|[-| ]+\|$", s):
            continue
        # Strip leading list markers (-, *, 1., 2., ...)
        s = re.sub(r"^[-*]\s+", "", s)
        s = re.sub(r"^\d+\.\s+", "", s)
        # Strip markdown formatting for plain-text display
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"~~(.+?)~~", r"\1", s)
        if s and s not in ("-", "—"):
            items.append(s)
    return items


def clean_summary_text(raw: str) -> str:
    """
    Convert a raw section body (typically ## Problem) into a clean 1–2 sentence
    summary suitable for a card preview.

    Strategy:
    - Skip lines that look like metadata bullets ("**Key:** value")
    - Skip markdown table lines
    - Take the first substantive prose sentence(s) up to ~180 chars
    """
    lines = raw.splitlines()
    prose_lines = []
    for line in lines:
        s = line.strip()
        if not s:
            if prose_lines:
                break          # first blank line after content = end of first para
            continue
        # Skip headings, table rows, horizontal rules
        if s.startswith("#") or s.startswith("---") or s.startswith("|"):
            continue
        # Skip pure metadata bullets: "- **Key:** value"
        if re.match(r"^[-*]\s*\*\*[^*]+\*\*\s*:", s):
            continue
        # Strip leading list markers
        s = re.sub(r"^[-*]\s+", "", s)
        s = re.sub(r"^\d+\.\s+", "", s)
        # Strip inline formatting
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"~~(.+?)~~", r"\1", s)
        if s:
            prose_lines.append(s)

    if not prose_lines:
        return ""
    combined = " ".join(prose_lines)
    # Truncate cleanly at sentence boundary where possible
    if len(combined) <= 180:
        return combined
    # Find last '. ' or '! ' or '? ' before 180 chars
    cut = combined[:180]
    for punct in (". ", "! ", "? "):
        idx = cut.rfind(punct)
        if idx > 60:
            return cut[:idx + 1]
    return cut.rstrip() + "…"


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalise_status(raw: str) -> str:
    s = raw.strip().lower()
    # Strip trailing parenthetical / bracketed qualifiers so values like
    # "tested (Playwright snapshot refreshed 2026-04-29...)" still normalise.
    s = re.sub(r"\s*[\(\[].*$", "", s).strip()
    mapping = {
        "inbox": "inbox",
        "triaged": "triage", "triage": "triage",
        "active": "active", "in-progress": "active", "in progress": "active",
        "review": "review", "in review": "review",
        "blocked": "blocked",
        "backlog": "backlog", "deferred": "backlog",
        "done": "done", "complete": "done", "completed": "done", "closed": "done",
        "tested": "tested", "validated": "tested",
        "deployed": "deployed", "released": "deployed", "live": "deployed",
    }
    if s in mapping:
        return mapping[s]
    # Fall back to the first whitespace-delimited token (handles trailing prose
    # like "tested - awaiting deploy" or "done. shipped on ...").
    first = re.split(r"[\s,;:/|–—-]", s, maxsplit=1)[0].strip()
    return mapping.get(first, first)


def normalise_priority(raw: str) -> str:
    s = raw.strip().lower()
    return s if s in ("critical", "high", "medium", "low") else "unspecified"


def normalise_app(raw: str) -> str:
    s = raw.strip().lower()
    compact = re.sub(r"\s+", "-", s)

    if compact in APP_LABELS:
        return compact

    canonical_values = {"knowledge", "app-1", "app-2", "app-3", "app-4", "cross-app"}
    token_values = {
        re.sub(r"[^a-z0-9-]+", "", token)
        for token in re.split(r"[\s,;:/()]+", compact)
        if token
    }
    exact_canonical = canonical_values & token_values
    if len(exact_canonical) == 1:
        return next(iter(exact_canonical))

    aliases = {
        "knowledge.healthcare": "knowledge",
        "knowledge-healthcare": "knowledge",
        "knowledge repository": "knowledge",
        "knowledge-repository": "knowledge",
        "knowledge repo": "knowledge",
        "knowledge-repo": "knowledge",
        "knowledge layer": "knowledge",
        "control layer": "knowledge",
        "app 1": "app-1",
        "app-1": "app-1",
        "medical_advisor": "app-1",
        "medical-advisor": "app-1",
        "app 2": "app-2",
        "app-2": "app-2",
        "anote_mobile": "app-2",
        "anote-mobile": "app-2",
        "anote mobile": "app-2",
        "app 3": "app-3",
        "app-3": "app-3",
        "anote-web": "app-3",
        "anote web": "app-3",
        "app 4": "app-4",
        "app-4": "app-4",
        "health-analysis": "app-4",
        "health analysis": "app-4",
        "cross-app": "cross-app",
        "cross app": "cross-app",
    }

    if compact in aliases:
        return aliases[compact]

    if "cross-app" in compact or "cross app" in s:
        return "cross-app"

    for alias, app_key in aliases.items():
        if alias in s or alias in compact:
            return app_key

    return "unknown"


# ---------------------------------------------------------------------------
# Spec index
# ---------------------------------------------------------------------------

def build_spec_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for app_key, spec_dir in SPEC_DIRS.items():
        if not spec_dir.exists():
            continue
        for f in sorted(spec_dir.iterdir()):
            if f.suffix == ".md":
                m = re.match(r"(TASK-\d+)", f.name, re.IGNORECASE)
                if m:
                    tid = m.group(1).upper()
                    index.setdefault(tid, []).append(f.name)
    return index


# ---------------------------------------------------------------------------
# Task parser
# ---------------------------------------------------------------------------

def parse_task_file(path: Path, folder_status: str) -> tuple[Optional[dict], Optional[str]]:
    text = read_file_safe(path)
    if text is None:
        return None, f"{path.name}: could not read file"

    task: dict = {
        "file":     path.name,
        "rel_path": str(path.relative_to(BASE_DIR)).replace("\\", "/"),
        "abs_path": str(path),
    }

    # ── Scalar metadata ──────────────────────────────────────────────────

    task_id = extract_frontmatter_field(text, "id") or extract_frontmatter_field(text, "task id")
    if not task_id:
        m = re.match(r"(TASK-\d+)", path.stem, re.IGNORECASE)
        task_id = m.group(1).upper() if m else path.stem
    task["id"] = task_id.upper()

    title = (
        extract_frontmatter_field(text, "title")
        or extract_h1(text)
        or path.stem
    )
    title = re.sub(r"^(?:task[:\s\-–]+|TASK-\d+[:\s\-–]+)", "", title, flags=re.IGNORECASE).strip()
    task["title"] = title or path.stem

    raw_status = extract_frontmatter_field(text, "status")
    task["status"] = normalise_status(raw_status) if raw_status else folder_status

    raw_app = (
        extract_frontmatter_field(text, "app")
        or extract_frontmatter_field(text, "app(s)")
        or extract_frontmatter_field(text, "apps")
    )
    task["app"] = normalise_app(raw_app) if raw_app else "unknown"

    raw_priority = extract_frontmatter_field(text, "priority")
    task["priority"] = normalise_priority(raw_priority) if raw_priority else "unspecified"

    raw_type = extract_frontmatter_field(text, "type")
    task["type"] = raw_type.lower().strip() if raw_type else "unspecified"

    task["repo"]    = extract_frontmatter_field(text, "repo")    or ""
    task["created"] = extract_frontmatter_field(text, "created") or extract_frontmatter_field(text, "created date") or ""
    task["author"]  = extract_frontmatter_field(text, "author")  or ""

    task["related_spec"] = (
        extract_frontmatter_field(text, "related spec")
        or extract_frontmatter_field(text, "technical spec")
        or extract_frontmatter_field(text, "spec")
        or ""
    )
    task["related_handoff"] = (
        extract_frontmatter_field(text, "related handoff")
        or extract_frontmatter_field(text, "handoff")
        or ""
    )

    # ── Rich sections ────────────────────────────────────────────────────

    for field_key, aliases in RICH_SECTIONS:
        raw = extract_section_text(text, aliases)
        task[field_key] = raw or ""

    # ── Card summary — clean prose, not metadata noise ───────────────────
    # Prefer Problem section; fall back to first real paragraph of file.
    if task["problem"]:
        task["summary"] = clean_summary_text(task["problem"])
    else:
        # Build a simple fallback from raw file text
        lines = text.splitlines()
        prose = []
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("|") or s.startswith("---"):
                if prose:
                    break
                continue
            if re.match(r"^[-*]\s*\*\*[^*]+\*\*\s*:", s):
                continue          # metadata bullet
            s = re.sub(r"^[-*]\s+", "", s)
            s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
            s = re.sub(r"`([^`]+)`", r"\1", s)
            if s:
                prose.append(s)
        task["summary"] = " ".join(prose)[:180].rstrip() if prose else ""

    # ── Derived list fields ───────────────────────────────────────────────
    task["open_questions_list"] = section_to_lines(task["open_questions"])[:6]
    task["dependencies_list"]   = section_to_lines(task["dependencies"])[:6]
    task["affected_areas_list"] = section_to_lines(task["affected_areas"])[:8]
    task["constraints_list"]    = section_to_lines(task["constraints"])[:6]

    return task, None


def load_all_tasks(spec_index: dict[str, list[str]]) -> tuple[list[dict], list[str]]:
    tasks: list[dict] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()

    for folder_name, folder_path in TASK_DIRS.items():
        if not folder_path.exists():
            continue
        for md_file in sorted(folder_path.glob("*.md")):
            # Skip non-task files (e.g. README.md)
            if not re.match(r"TASK-\d+", md_file.stem, re.IGNORECASE):
                continue
            task, warn = parse_task_file(md_file, folder_name)
            if warn:
                warnings.append(warn)
            if task is None:
                continue
            tid = task["id"]
            if tid in seen_ids:
                warnings.append(f"{md_file.name}: duplicate task ID '{tid}' — skipped")
                continue
            seen_ids.add(tid)
            task["spec_files"] = spec_index.get(tid, [])
            task["has_spec"]   = bool(task["spec_files"])
            if not task["related_spec"] and task["spec_files"]:
                task["related_spec"] = ", ".join(task["spec_files"])
            tasks.append(task)

    return tasks, warnings


# ---------------------------------------------------------------------------
# Current priorities parser
# ---------------------------------------------------------------------------

def load_current_priorities() -> str:
    text = read_file_safe(CURRENT_PRIORITIES_FILE)
    if not text:
        return "<p><em>current-priorities.md not found or unreadable.</em></p>"

    lines = text.splitlines()
    html_parts: list[str] = []
    in_list = False

    for line in lines:
        s = line.strip()
        if not s:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
        if s.startswith("# "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
        elif s.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<h4 class="priorities-heading">{_esc(s[3:].strip())}</h4>')
        elif s.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<h5 class="priorities-subheading">{_esc(s[4:].strip())}</h5>')
        elif s.startswith(("- ", "* ")):
            if not in_list:
                html_parts.append('<ul class="priorities-list">')
                in_list = True
            item = s[2:].strip()
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"`([^`]+)`", r"<code>\1</code>", item)
            html_parts.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            line_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            line_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", line_html)
            html_parts.append(f"<p>{line_html}</p>")

    if in_list:
        html_parts.append("</ul>")
    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


PRIORITY_CLASS = {
    "critical":    "badge-priority-critical",
    "high":        "badge-priority-high",
    "medium":      "badge-priority-medium",
    "low":         "badge-priority-low",
    "unspecified": "badge-priority-unspecified",
}
APP_CLASS = {
    "knowledge": "badge-app-knowledge",
    "app-1":     "badge-app-1",
    "app-2":     "badge-app-2",
    "app-3":     "badge-app-3",
    "app-4":     "badge-app-4",
    "cross-app": "badge-app-cross",
    "unknown":   "badge-app-unknown",
}
STATUS_LABEL = {
    "inbox":    "Inbox",
    "triage":   "Triaged",
    "active":   "Active",
    "review":   "Review",
    "blocked":  "Blocked",
    "backlog":  "Backlog",
    "done":     "Done",
    "tested":   "Tested",
    "deployed": "Deployed",
}
STATUS_CLASS = {
    "inbox":    "badge-status-inbox",
    "triage":   "badge-status-triage",
    "active":   "badge-status-active",
    "review":   "badge-status-review",
    "blocked":  "badge-status-blocked",
    "backlog":  "badge-status-backlog",
    "done":     "badge-status-done",
    "tested":   "badge-status-tested",
    "deployed": "badge-status-deployed",
}
COLUMN_ORDER = ["inbox", "triage", "active", "backlog", "done", "tested", "deployed"]


def render_badge(text: str, css_class: str, title: str = "") -> str:
    ta = f' title="{_esc(title)}"' if title else ""
    return f'<span class="badge {css_class}"{ta}>{_esc(text)}</span>'


# ---------------------------------------------------------------------------
# Task card
# ---------------------------------------------------------------------------

def render_task_card(task: dict) -> str:
    tid      = task["id"]
    title    = task["title"]
    app      = task["app"]
    priority = task["priority"]
    ttype    = task["type"]
    status   = task["status"]
    summary  = task["summary"]
    has_spec = task["has_spec"]
    rel_path = task["rel_path"]

    app_label  = APP_LABELS.get(app, app)
    app_badge  = render_badge(app_label, APP_CLASS.get(app, "badge-app-unknown"))
    prio_badge = render_badge(priority,  PRIORITY_CLASS.get(priority, "badge-priority-unspecified"))
    type_badge = render_badge(ttype,     "badge-type")
    spec_ind   = (
        '<span class="spec-indicator spec-yes" title="Spec available">spec ✓</span>'
        if has_spec else
        '<span class="spec-indicator spec-no" title="No spec">no spec</span>'
    )

    summary_html = ""
    if summary:
        # Display at most ~160 chars of clean prose
        preview = summary[:160] + ("…" if len(summary) > 160 else "")
        summary_html = f'<p class="card-summary">{_esc(preview)}</p>'

    src_link   = "../" + rel_path
    data_attrs = (
        f'data-app="{_esc(app)}" '
        f'data-priority="{_esc(priority)}" '
        f'data-status="{_esc(status)}" '
        f'data-type="{_esc(ttype)}" '
        f'data-id="{_esc(tid)}" '
        f'data-title="{_esc(title)}"'
    )

    return f"""
<div class="task-card" {data_attrs} role="button" tabindex="0" aria-label="Open details for {_esc(tid)}">
  <div class="card-header">
    <a class="card-id" href="{_esc(src_link)}" title="Open source file" onclick="event.stopPropagation()">{_esc(tid)}</a>
    <div class="card-badges">
      {app_badge}
      {prio_badge}
      {type_badge}
      {spec_ind}
    </div>
  </div>
  <div class="card-title">{_esc(title)}</div>
  {summary_html}
  <div class="card-footer">
    <span class="card-path" title="{_esc(rel_path)}">{_esc(rel_path)}</span>
    <span class="card-open-hint">details ›</span>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# JSON task-detail blob
# ---------------------------------------------------------------------------

def build_task_json(tasks: list[dict]) -> str:
    data: dict[str, dict] = {}
    for t in tasks:
        tid = t["id"]
        data[tid] = {
            "id":               t["id"],
            "title":            t["title"],
            "status":           t["status"],
            "app":              t["app"],
            "app_label":        APP_LABELS.get(t["app"], t["app"]),
            "priority":         t["priority"],
            "type":             t["type"],
            "repo":             t["repo"],
            "created":          t["created"],
            "author":           t["author"],
            "rel_path":         t["rel_path"],
            "has_spec":         t["has_spec"],
            "spec_files":       t["spec_files"],
            "related_spec":     t["related_spec"],
            "related_handoff":  t["related_handoff"],
            "summary":          t["summary"],
            "problem":          t["problem"],
            "desired_outcome":  t["desired_outcome"],
            "why_it_matters":   t["why_it_matters"],
            "constraints_list": t["constraints_list"],
            "affected_areas_list": t["affected_areas_list"],
            "dependencies_list":   t["dependencies_list"],
            "open_questions_list": t["open_questions_list"],
            "notes":            t["notes"],
            "confirmed_facts":  t["confirmed_facts"],
            "assumptions":      t["assumptions"],
            "reasoning":        t["reasoning"],
            "cross_app":        t["cross_app"],
        }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Kanban
# ---------------------------------------------------------------------------

def render_kanban(tasks: list[dict]) -> str:
    columns: dict[str, list[dict]] = {s: [] for s in COLUMN_ORDER}
    for task in tasks:
        col = task["status"] if task["status"] in columns else "inbox"
        columns[col].append(task)

    prio_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unspecified": 4}
    for col in columns:
        columns[col].sort(key=lambda t: prio_order.get(t["priority"], 9))

    deployed_group_size = 5

    always_visible = {"inbox", "active", "backlog", "done"}
    html_parts = ['<div class="kanban-board" id="kanban-board">']
    for status in COLUMN_ORDER:
        col_tasks = columns[status]
        if not col_tasks and status not in always_visible:
            continue
        label     = STATUS_LABEL.get(status, status.title())
        count     = len(col_tasks)
        done_cls  = " kanban-col-done" if status in ("done", "tested", "deployed") else ""

        if status == "deployed" and col_tasks:
            deployed_chunks = [
                col_tasks[i:i + deployed_group_size]
                for i in range(0, len(col_tasks), deployed_group_size)
            ]
            for chunk_index, chunk in enumerate(deployed_chunks, start=1):
                chunk_label = label if chunk_index == 1 else f"{label} {chunk_index}"
                cards_html = "".join(render_task_card(t) for t in chunk)
                html_parts.append(f"""
<div class="kanban-col glass{done_cls} deployed-col" data-col-status="{status}" data-deployed-group="{chunk_index}">
  <div class="kanban-col-header">
    <span class="col-label">{_esc(chunk_label)}</span>
    <span class="col-count">{len(chunk)}</span>
  </div>
  <div class="kanban-cards">
    {cards_html}
  </div>
</div>""")
            continue

        cards_html = "".join(render_task_card(t) for t in col_tasks)
        empty_html = '<div class="kanban-empty">No tasks</div>' if not col_tasks else ""
        html_parts.append(f"""
<div class="kanban-col glass{done_cls}" data-col-status="{status}">
  <div class="kanban-col-header">
    <span class="col-label">{_esc(label)}</span>
    <span class="col-count">{count}</span>
  </div>
  <div class="kanban-cards">
    {cards_html}
    {empty_html}
  </div>
</div>""")
    html_parts.append("</div>")
    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# Summary cards
# ---------------------------------------------------------------------------

def render_summary_cards(tasks: list[dict]) -> tuple[str, str]:
    """Return (status_html, app_html) — two separate compact stat strips for the top bar."""
    total           = len(tasks)
    active_count    = sum(1 for t in tasks if t["status"] == "active")
    done_count      = sum(1 for t in tasks if t["status"] == "done")
    tested_count    = sum(1 for t in tasks if t["status"] == "tested")
    deployed_count  = sum(1 for t in tasks if t["status"] == "deployed")
    backlog_count   = sum(1 for t in tasks if t["status"] == "backlog")
    inbox_count     = sum(1 for t in tasks if t["status"] == "inbox")
    needs_spec      = sum(1 for t in tasks if not t["has_spec"] and t["status"] not in ("done", "tested", "deployed"))

    app_counts: dict[str, int] = {}
    for t in tasks:
        app_counts[t["app"]] = app_counts.get(t["app"], 0) + 1

    def card(value: int, label: str, css: str = "") -> str:
        return (
            f'<div class="stat-card {css}">'
            f'<div class="stat-value">{value}</div>'
            f'<div class="stat-label">{_esc(label)}</div>'
            f'</div>'
        )

    status_html = (
        card(total, "Total")
        + card(active_count, "Active", "stat-active")
        + card(inbox_count, "Inbox", "stat-inbox")
        + card(backlog_count, "Backlog", "stat-backlog")
        + card(done_count, "Done", "stat-done")
        + card(tested_count, "Tested", "stat-tested")
        + card(deployed_count, "Deployed", "stat-deployed")
        + card(needs_spec, "Need Spec", "stat-warn")
    )

    app_html = ""
    for app_key in ["knowledge", "app-1", "app-2", "app-3", "app-4", "cross-app", "unknown"]:
        n  = app_counts.get(app_key, 0)
        al = APP_LABELS.get(app_key, app_key)
        bc = APP_CLASS.get(app_key, "badge-app-unknown")
        app_html += (
            f'<div class="stat-card stat-app">'
            f'<div class="stat-value">{n}</div>'
            f'<div class="stat-label"><span class="badge {bc}">{_esc(al)}</span></div>'
            f'</div>'
        )

    return status_html, app_html


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def render_filters() -> str:
    return """
<div class="filters-bar glass" id="filters-bar">
  <div class="filters-row">
    <input type="text" id="search-input" class="filter-input"
           placeholder="Search by ID or title…" aria-label="Search tasks" />
    <select id="filter-app" class="filter-select" aria-label="Filter by app">
      <option value="">All apps</option>
      <option value="knowledge">Knowledge.Healthcare</option>
      <option value="app-1">medical_advisor</option>
      <option value="app-2">ANOTE_mobile</option>
      <option value="app-3">ANOTE-web</option>
      <option value="app-4">Health-Analysis</option>
      <option value="cross-app">cross-app</option>
      <option value="unknown">unknown</option>
    </select>
    <select id="filter-priority" class="filter-select" aria-label="Filter by priority">
      <option value="">All priorities</option>
      <option value="critical">Critical</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
      <option value="unspecified">Unspecified</option>
    </select>
    <select id="filter-status" class="filter-select" aria-label="Filter by status">
      <option value="">All statuses</option>
      <option value="inbox">Inbox</option>
      <option value="triage">Triaged</option>
      <option value="active">Active</option>
      <option value="backlog">Backlog</option>
      <option value="done">Done</option>
      <option value="tested">Tested</option>
      <option value="deployed">Deployed</option>
    </select>
    <select id="filter-type" class="filter-select" aria-label="Filter by type">
      <option value="">All types</option>
      <option value="bug">Bug</option>
      <option value="feature">Feature</option>
      <option value="refactor">Refactor</option>
      <option value="infra">Infra</option>
      <option value="docs">Docs</option>
      <option value="investigation">Investigation</option>
    </select>
    <label class="toggle-label">
      <input type="checkbox" id="hide-done" />
      Hide done / tested / deployed
    </label>
    <button id="reset-filters" class="btn-reset">Reset filters</button>
  </div>
  <div id="filter-count" class="filter-count"></div>
</div>"""


# ---------------------------------------------------------------------------
# Parser warnings
# ---------------------------------------------------------------------------

def render_warnings(warnings: list[str]) -> str:
    if not warnings:
        return '<p class="no-warnings">No parser warnings.</p>'
    items = "".join(f"<li><code>{_esc(w)}</code></li>" for w in warnings)
    return f'<ul class="warnings-list">{items}</ul>'


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

INLINE_CSS = """
/* ═══════════════════════════════════════════════════════════
   Theme tokens
   ═══════════════════════════════════════════════════════════ */

:root,
html[data-theme="light"] {
  --page-bg:       #eef1f6;
  --bg:            #f4f5f7;
  --surface:       #ffffff;
  --surface-2:     #f6f8fb;
  --surface-3:     #eef2f7;
  --border:        rgba(15, 20, 30, 0.10);
  --border-light:  rgba(15, 20, 30, 0.06);
  --text:          #1a1d23;
  --text-muted:    #4a5160;
  --text-faint:    #7a8396;
  --accent:        #3b82f6;
  --accent-dim:    #eff6ff;

  --glass-bg:        rgba(255, 255, 255, 0.55);
  --glass-bg-strong: rgba(255, 255, 255, 0.72);
  --glass-bg-solid:  #ffffffee;
  --glass-border:    rgba(15, 20, 30, 0.10);
  --glass-shadow:    0 8px 32px rgba(20, 30, 50, 0.10), inset 0 1px 0 rgba(255,255,255,.55);

  --blob-1: rgba(139, 92, 246, .32);
  --blob-2: rgba(59, 130, 246, .28);
  --blob-3: rgba(14, 165, 233, .26);
  --blob-4: rgba(236, 72, 153, .24);

  --col-inbox:   #6366f1;
  --col-triage:  #8b5cf6;
  --col-active:  #059669;
  --col-review:  #d97706;
  --col-blocked: #dc2626;
  --col-backlog: #6b7280;
  --col-done:    #9ca3af;
  --col-tested:  #0284c7;
  --col-deployed:#15803d;
  --p-high:      #ea580c;

  --radius-lg:   16px;
  --radius-md:   12px;
  --radius-sm:   10px;
  --radius-xs:   6px;

  --shadow-card: 0 2px 8px rgba(20,30,50,.08);
  --shadow-modal:0 24px 64px rgba(0,0,0,.25), 0 4px 16px rgba(0,0,0,.12);
}

html[data-theme="dark"] {
  --page-bg:       #0b0d12;
  --bg:            #0b0d12;
  --surface:       #161a22;
  --surface-2:     #1a1f29;
  --surface-3:     #202634;
  --border:        rgba(255, 255, 255, 0.08);
  --border-light:  rgba(255, 255, 255, 0.05);
  --text:          #e6e8ef;
  --text-muted:    #9aa3b2;
  --text-faint:    #6b7280;
  --accent:        #6ea8ff;
  --accent-dim:    rgba(110, 168, 255, 0.15);

  --glass-bg:        rgba(22, 26, 34, 0.55);
  --glass-bg-strong: rgba(22, 26, 34, 0.72);
  --glass-bg-solid:  #171b24f2;
  --glass-border:    rgba(255, 255, 255, 0.09);
  --glass-shadow:    0 10px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255,255,255,.05);

  --blob-1: rgba(139, 92, 246, .55);
  --blob-2: rgba(59, 130, 246, .50);
  --blob-3: rgba(14, 165, 233, .46);
  --blob-4: rgba(236, 72, 153, .44);

  --col-inbox:   #818cf8;
  --col-triage:  #a78bfa;
  --col-active:  #34d399;
  --col-review:  #fbbf24;
  --col-blocked: #f87171;
  --col-backlog: #9ca3af;
  --col-done:    #d1d5db;
  --col-tested:  #38bdf8;
  --col-deployed:#4ade80;
  --p-high:      #fb923c;

  --shadow-card: 0 2px 10px rgba(0,0,0,.35);
  --shadow-modal:0 32px 80px rgba(0,0,0,.70), 0 8px 24px rgba(0,0,0,.45);
}

/* ═══════════════════════════════════════════════════════════
   Base
   ═══════════════════════════════════════════════════════════ */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { color-scheme: dark light; }
html[data-theme="light"] { color-scheme: light; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--page-bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.55;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}
body.modal-open { overflow: hidden; }

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12px;
  background: var(--border-light);
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--text);
}

/* ═══════════════════════════════════════════════════════════
   Background "lights" — blurred drifting blobs
   ═══════════════════════════════════════════════════════════ */

.bg-blobs {
  position: fixed;
  inset: -10vmax;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(40vmax 40vmax at 12% 18%, var(--blob-1), transparent 60%),
    radial-gradient(42vmax 42vmax at 85% 10%, var(--blob-2), transparent 60%),
    radial-gradient(46vmax 46vmax at 72% 85%, var(--blob-3), transparent 60%),
    radial-gradient(38vmax 38vmax at 18% 92%, var(--blob-4), transparent 60%);
  filter: blur(60px) saturate(125%);
  will-change: transform;
  animation: blob-drift 55s ease-in-out infinite alternate;
}
@keyframes blob-drift {
  0%   { transform: translate3d(0, 0, 0)      scale(1); }
  50%  { transform: translate3d(-3vw, 2vh, 0) scale(1.08); }
  100% { transform: translate3d(4vw, -2vh, 0) scale(1.03); }
}

/* ═══════════════════════════════════════════════════════════
   Glass container mixin (applied via .glass class)
   ═══════════════════════════════════════════════════════════ */

.glass {
  background: var(--glass-bg);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
          backdrop-filter: blur(18px) saturate(140%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass { background: var(--glass-bg-solid); }
}

/* ═══════════════════════════════════════════════════════════
   Layout
   ═══════════════════════════════════════════════════════════ */

.page-wrap { max-width: 1440px; margin: 0 auto; padding: 0 24px 32px; }

.section { margin-bottom: 24px; }
.section-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .8px; color: var(--text-faint);
  margin: 0 4px 10px;
}

/* ═══════════════════════════════════════════════════════════
   Top stat bar (replaces old header)
   ═══════════════════════════════════════════════════════════ */

.top-bar {
  margin: 20px auto 22px;
  max-width: 1440px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.top-bar-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-width: 0;
}
.stats-row {
  display: flex;
  align-items: stretch;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}
.stats-row::-webkit-scrollbar { height: 4px; }
.stats-divider {
  width: 1px;
  align-self: stretch;
  background: var(--glass-border);
  margin: 4px 4px;
  flex-shrink: 0;
}

.stat-card {
  flex: 0 0 auto;
  min-width: 72px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border);
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  transition: transform .18s ease, border-color .18s ease;
}
.stat-card:hover { transform: translateY(-1px); border-color: var(--accent); }
.stat-value {
  font-size: 20px; font-weight: 700; color: var(--text); line-height: 1;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: 10px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .5px;
  display: flex; justify-content: center; align-items: center; gap: 4px;
}
.stat-app .stat-label .badge { font-size: 10px; padding: 1px 6px; }

.stat-active   .stat-value { color: var(--col-active); }
.stat-inbox    .stat-value { color: var(--col-inbox); }
.stat-backlog  .stat-value { color: var(--col-backlog); }
.stat-done     .stat-value { color: var(--col-done); }
.stat-tested   .stat-value { color: var(--col-tested); }
.stat-deployed .stat-value { color: var(--col-deployed); }
.stat-warn     .stat-value { color: var(--p-high); }

/* Theme toggle button */
.theme-toggle {
  flex-shrink: 0;
  width: 38px; height: 38px;
  border-radius: 50%;
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border);
  color: var(--text);
  cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  transition: transform .2s ease, border-color .2s ease, background .2s ease;
  position: relative;
}
.theme-toggle:hover { transform: rotate(12deg); border-color: var(--accent); }
.theme-toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.theme-toggle svg { width: 18px; height: 18px; }
.theme-toggle .icon-sun  { display: none; }
.theme-toggle .icon-moon { display: block; }
html[data-theme="light"] .theme-toggle .icon-sun  { display: block; }
html[data-theme="light"] .theme-toggle .icon-moon { display: none; }

/* ═══════════════════════════════════════════════════════════
   Badges
   ═══════════════════════════════════════════════════════════ */

.badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 999px; white-space: nowrap; letter-spacing: .2px;
}
html[data-theme="dark"] .badge-app-knowledge { background: rgba(244,114,182,.22); color: #f9a8d4; }
html[data-theme="dark"] .badge-app-1       { background: rgba(59,130,246,.22);  color: #93c5fd; }
html[data-theme="dark"] .badge-app-2       { background: rgba(168,85,247,.22);  color: #d8b4fe; }
html[data-theme="dark"] .badge-app-3       { background: rgba(16,185,129,.22);  color: #6ee7b7; }
html[data-theme="dark"] .badge-app-4       { background: rgba(45,212,191,.22);  color: #99f6e4; }
html[data-theme="dark"] .badge-app-cross   { background: rgba(234,179,8,.22);   color: #fde68a; }
html[data-theme="dark"] .badge-app-unknown { background: rgba(148,163,184,.22); color: #cbd5e1; }

html[data-theme="dark"] .badge-priority-critical    { background: rgba(239,68,68,.22);  color: #fca5a5; }
html[data-theme="dark"] .badge-priority-high        { background: rgba(249,115,22,.22); color: #fdba74; }
html[data-theme="dark"] .badge-priority-medium      { background: rgba(234,179,8,.20);  color: #fde68a; }
html[data-theme="dark"] .badge-priority-low         { background: rgba(34,197,94,.22);  color: #86efac; }
html[data-theme="dark"] .badge-priority-unspecified { background: rgba(148,163,184,.20); color: #cbd5e1; }

html[data-theme="dark"] .badge-status-inbox    { background: rgba(99,102,241,.22); color: #c7d2fe; }
html[data-theme="dark"] .badge-status-triage   { background: rgba(139,92,246,.22); color: #ddd6fe; }
html[data-theme="dark"] .badge-status-active   { background: rgba(16,185,129,.22); color: #6ee7b7; }
html[data-theme="dark"] .badge-status-review   { background: rgba(245,158,11,.22); color: #fde68a; }
html[data-theme="dark"] .badge-status-blocked  { background: rgba(239,68,68,.22);  color: #fca5a5; }
html[data-theme="dark"] .badge-status-backlog  { background: rgba(148,163,184,.20); color: #cbd5e1; }
html[data-theme="dark"] .badge-status-done     { background: rgba(148,163,184,.20); color: #cbd5e1; }
html[data-theme="dark"] .badge-status-tested   { background: rgba(56,189,248,.22); color: #7dd3fc; }
html[data-theme="dark"] .badge-status-deployed { background: rgba(34,197,94,.22);  color: #86efac; }

/* Light-mode colors (kept from original palette) */
html[data-theme="light"] .badge-app-knowledge { background: #fce7f3; color: #9d174d; }
html[data-theme="light"] .badge-app-1      { background: #dbeafe; color: #1d4ed8; }
html[data-theme="light"] .badge-app-2      { background: #f3e8ff; color: #7e22ce; }
html[data-theme="light"] .badge-app-3      { background: #d1fae5; color: #065f46; }
html[data-theme="light"] .badge-app-4      { background: #ccfbf1; color: #115e59; }
html[data-theme="light"] .badge-app-cross  { background: #fef9c3; color: #854d0e; }
html[data-theme="light"] .badge-app-unknown{ background: #f1f5f9; color: #475569; }
html[data-theme="light"] .badge-priority-critical   { background: #fee2e2; color: #991b1b; }
html[data-theme="light"] .badge-priority-high       { background: #ffedd5; color: #9a3412; }
html[data-theme="light"] .badge-priority-medium     { background: #fefce8; color: #854d0e; }
html[data-theme="light"] .badge-priority-low        { background: #dcfce7; color: #166534; }
html[data-theme="light"] .badge-priority-unspecified{ background: #f1f5f9; color: #64748b; }
html[data-theme="light"] .badge-status-inbox    { background: #eef2ff; color: #4338ca; }
html[data-theme="light"] .badge-status-triage   { background: #f5f3ff; color: #6d28d9; }
html[data-theme="light"] .badge-status-active   { background: #d1fae5; color: #065f46; }
html[data-theme="light"] .badge-status-review   { background: #fffbeb; color: #92400e; }
html[data-theme="light"] .badge-status-blocked  { background: #fee2e2; color: #991b1b; }
html[data-theme="light"] .badge-status-backlog  { background: #f1f5f9; color: #475569; }
html[data-theme="light"] .badge-status-done     { background: #f1f5f9; color: #64748b; }
html[data-theme="light"] .badge-status-tested   { background: #e0f2fe; color: #0369a1; }
html[data-theme="light"] .badge-status-deployed { background: #dcfce7; color: #15803d; }

.badge-type {
  background: var(--surface-2); color: var(--text-muted);
  border: 1px solid var(--glass-border);
}

.spec-indicator {
  font-size: 10px; font-weight: 600; padding: 2px 7px;
  border-radius: 999px; white-space: nowrap;
}
html[data-theme="dark"] .spec-yes { background: rgba(34,197,94,.22); color: #86efac; }
html[data-theme="dark"] .spec-no  { background: rgba(148,163,184,.18); color: #94a3b8; }
html[data-theme="light"] .spec-yes { background: #d1fae5; color: #065f46; }
html[data-theme="light"] .spec-no  { background: #f1f5f9; color: #94a3b8; }

/* ═══════════════════════════════════════════════════════════
   Filters
   ═══════════════════════════════════════════════════════════ */

.filters-bar {
  padding: 14px 18px;
  margin-bottom: 4px;
}
.filters-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.filter-input {
  flex: 1 1 220px; min-width: 180px; padding: 9px 12px;
  border: 1px solid var(--glass-border); border-radius: var(--radius-sm);
  font-size: 13px; background: var(--glass-bg-strong); color: var(--text); outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.filter-input::placeholder { color: var(--text-faint); }
.filter-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-dim); }
.filter-select {
  flex: 0 0 auto; padding: 9px 12px; border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm); font-size: 13px; background: var(--glass-bg-strong);
  color: var(--text); cursor: pointer; outline: none;
  transition: border-color .15s;
}
.filter-select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-dim); }
.toggle-label {
  font-size: 13px; color: var(--text-muted); cursor: pointer;
  display: flex; align-items: center; gap: 6px; white-space: nowrap; user-select: none;
}
.toggle-label input[type="checkbox"] { accent-color: var(--accent); }
.btn-reset {
  padding: 9px 14px; background: var(--glass-bg-strong); border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm); font-size: 13px; cursor: pointer;
  color: var(--text-muted); white-space: nowrap;
  transition: color .15s, border-color .15s, transform .15s;
}
.btn-reset:hover { color: var(--text); border-color: var(--accent); transform: translateY(-1px); }
.filter-count { margin-top: 10px; font-size: 12px; color: var(--text-muted); min-height: 16px; }

/* ═══════════════════════════════════════════════════════════
   Kanban
   ═══════════════════════════════════════════════════════════ */

.kanban-board {
  display: flex; gap: 14px; overflow-x: auto;
  padding: 4px 2px 12px; align-items: flex-start;
}
.kanban-col {
  flex: 0 0 268px;
  padding: 0;
  overflow: hidden;
  position: relative;
}
.deployed-col { flex-basis: 268px; }
.kanban-col-done { opacity: .92; }
.kanban-col-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 11px 14px;
  border-bottom: 2px solid var(--glass-border);
  background: var(--glass-bg-strong);
}
.col-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; color: var(--text); }
.col-count {
  background: var(--surface-2); color: var(--text-muted);
  border-radius: 999px; padding: 2px 8px; font-size: 11px; font-weight: 700;
  border: 1px solid var(--glass-border);
  font-variant-numeric: tabular-nums;
}
.kanban-cards { padding: 10px; display: flex; flex-direction: column; gap: 10px; }
.kanban-empty { text-align: center; color: var(--text-faint); font-size: 12px; padding: 20px 0; }

[data-col-status="inbox"]    .kanban-col-header { border-bottom-color: var(--col-inbox); }
[data-col-status="triage"]   .kanban-col-header { border-bottom-color: var(--col-triage); }
[data-col-status="active"]   .kanban-col-header { border-bottom-color: var(--col-active); }
[data-col-status="review"]   .kanban-col-header { border-bottom-color: var(--col-review); }
[data-col-status="blocked"]  .kanban-col-header { border-bottom-color: var(--col-blocked); }
[data-col-status="backlog"]  .kanban-col-header { border-bottom-color: var(--col-backlog); }
[data-col-status="done"]     .kanban-col-header { border-bottom-color: var(--col-done); }
[data-col-status="tested"]   .kanban-col-header { border-bottom-color: var(--col-tested); }
[data-col-status="deployed"] .kanban-col-header { border-bottom-color: var(--col-deployed); }

/* ═══════════════════════════════════════════════════════════
   Task card
   ═══════════════════════════════════════════════════════════ */

.task-card {
  background: var(--glass-bg-strong);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
          backdrop-filter: blur(14px) saturate(140%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 11px 13px;
  box-shadow: var(--shadow-card);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  cursor: pointer;
}
.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0,0,0,.18);
  border-color: var(--accent);
}
.task-card:focus-visible{ outline: 2px solid var(--accent); outline-offset: 2px; }
.task-card.hidden       { display: none; }

.card-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 6px; margin-bottom: 5px;
}
.card-id {
  font-size: 11px; font-weight: 700; color: var(--accent);
  font-family: "SFMono-Regular", Consolas, monospace; white-space: nowrap;
}
.card-badges { display: flex; flex-wrap: wrap; gap: 4px; justify-content: flex-end; }
.card-title  { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.4; margin-bottom: 5px; }
.card-summary{
  font-size: 12px; color: var(--text-muted); line-height: 1.55;
  margin-bottom: 6px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.card-footer {
  margin-top: 6px; border-top: 1px solid var(--border-light);
  padding-top: 6px; display: flex; justify-content: space-between; align-items: center;
}
.card-path {
  font-size: 10px; color: var(--text-faint);
  font-family: "SFMono-Regular", Consolas, monospace;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-open-hint {
  font-size: 10px; color: var(--text-faint); white-space: nowrap;
  margin-left: 6px; flex-shrink: 0; opacity: 0; transition: opacity .15s;
}
.task-card:hover .card-open-hint { opacity: 1; }

/* ═══════════════════════════════════════════════════════════
   Priorities
   ═══════════════════════════════════════════════════════════ */

.priorities-content {
  padding: 22px 26px;
  max-width: 960px;
}
.priorities-heading {
  font-size: 14px; font-weight: 700; color: var(--text);
  margin: 18px 0 8px; padding-bottom: 5px;
  border-bottom: 1px solid var(--border-light);
}
.priorities-heading:first-child { margin-top: 0; }
.priorities-subheading { font-size: 12px; font-weight: 600; color: var(--text-muted); margin: 10px 0 4px; }
.priorities-list { padding-left: 22px; margin: 4px 0 8px; }
.priorities-list li { margin-bottom: 5px; font-size: 13px; color: var(--text); line-height: 1.6; }
.priorities-content p { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.priorities-content strong { color: var(--text); }

/* ═══════════════════════════════════════════════════════════
   Warnings
   ═══════════════════════════════════════════════════════════ */

.warnings-section {
  padding: 16px 20px;
  border-color: rgba(252,211,77,.45);
}
html[data-theme="dark"] .warnings-section { background: rgba(120, 90, 10, .28); }
html[data-theme="light"] .warnings-section { background: rgba(255, 251, 235, .75); }
.warnings-list { padding-left: 22px; margin-top: 6px; }
.warnings-list li { margin-bottom: 4px; font-size: 12px; color: var(--text); }
.no-warnings { font-size: 13px; color: var(--text-muted); font-style: italic; }

/* ═══════════════════════════════════════════════════════════
   Page footer
   ═══════════════════════════════════════════════════════════ */

.page-footer {
  margin: 24px auto 12px;
  max-width: 1440px;
  padding: 10px 24px;
  text-align: center;
  font-size: 11px;
  color: var(--text-faint);
  line-height: 1.5;
}
.page-footer code { font-size: 10.5px; }
.page-footer .warn-inline {
  display: inline-block; margin-left: 8px;
  background: rgba(252,211,77,.25); color: var(--text);
  border: 1px solid rgba(252,211,77,.55); border-radius: 10px;
  padding: 1px 8px; font-size: 10.5px; font-weight: 600;
}

/* ═══════════════════════════════════════════════════════════
   Scrollbar
   ═══════════════════════════════════════════════════════════ */

::-webkit-scrollbar { height: 8px; width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148,163,184,.35); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,.55); }

/* ═══════════════════════════════════════════════════════════
   Load-in animations
   ═══════════════════════════════════════════════════════════ */

@keyframes rise-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
.top-bar  { animation: rise-in .32s ease both; }
.section  { animation: rise-in .32s ease both; }
.section:nth-of-type(1) { animation-delay: .04s; }
.section:nth-of-type(2) { animation-delay: .10s; }
.section:nth-of-type(3) { animation-delay: .16s; }
.section:nth-of-type(4) { animation-delay: .22s; }

/* ═══════════════════════════════════════════════════════════
   Reduced motion
   ═══════════════════════════════════════════════════════════ */

@media (prefers-reduced-motion: reduce) {
  .bg-blobs { animation: none; }
  .top-bar, .section { animation: none; }
  .task-card:hover { transform: none; }
  .stat-card:hover { transform: none; }
  .theme-toggle:hover { transform: none; }
  .btn-reset:hover { transform: none; }
  * { transition: none !important; }
}

/* ═══════════════════════════════════════════════════════════
   Small screens — let stat bar wrap
   ═══════════════════════════════════════════════════════════ */

@media (max-width: 900px) {
  .page-wrap { padding: 0 14px 24px; }
  .top-bar { margin: 12px 14px 16px; padding: 10px 12px; }
  .stat-card { min-width: 64px; padding: 7px 10px; }
  .stat-value { font-size: 18px; }
}

/* ═══════════════════════════════════════════════════════════
   MODAL
   ═══════════════════════════════════════════════════════════ */

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(6, 10, 18, 0.62);
  -webkit-backdrop-filter: blur(8px);
          backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 28px 16px;
  opacity: 0;
  pointer-events: none;
  transition: opacity .22s ease;
}
.modal-overlay.modal-visible {
  opacity: 1;
  pointer-events: auto;
}

.modal-panel {
  background: var(--glass-bg-strong);
  -webkit-backdrop-filter: blur(22px) saturate(150%);
          backdrop-filter: blur(22px) saturate(150%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  width: 100%;
  max-width: 720px;
  max-height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  transform: translateY(12px) scale(.985);
  transition: transform .25s ease;
  overflow: hidden;
}
.modal-overlay.modal-visible .modal-panel {
  transform: translateY(0) scale(1);
}

.modal-header {
  padding: 22px 24px 16px;
  border-bottom: 1px solid var(--glass-border);
  flex-shrink: 0;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.modal-header-left { flex: 1; min-width: 0; }

.modal-task-id {
  font-size: 11px; font-weight: 700;
  color: var(--accent);
  font-family: "SFMono-Regular", Consolas, monospace;
  margin-bottom: 5px;
  display: flex; align-items: center; gap: 10px;
}
.modal-task-id .modal-src-link {
  font-size: 10px; font-weight: 600;
  color: var(--text-faint); opacity: .85;
  text-decoration: none; border: 1px solid var(--glass-border);
  border-radius: 6px; padding: 2px 6px;
}
.modal-task-id .modal-src-link:hover { color: var(--accent); border-color: var(--accent); opacity: 1; }

.modal-title {
  font-size: 19px; font-weight: 700; color: var(--text);
  line-height: 1.3; margin-bottom: 12px;
  word-break: break-word;
}

.modal-badges { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }

.modal-close {
  flex-shrink: 0;
  background: none; border: none; cursor: pointer;
  color: var(--text-muted); padding: 6px;
  border-radius: var(--radius-xs);
  font-size: 18px; line-height: 1;
  transition: color .15s, background .15s;
  margin-top: -2px;
}
.modal-close:hover { color: var(--text); background: var(--surface-2); }

.modal-body {
  overflow-y: auto;
  padding: 20px 24px 28px;
  flex: 1;
}

.modal-facts-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 8px;
  margin-bottom: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border-light);
}
.modal-fact {
  background: var(--surface-2);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xs);
  padding: 8px 10px;
}
.modal-fact-label {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .5px; color: var(--text-faint); margin-bottom: 4px;
}
.modal-fact-value { font-size: 12px; color: var(--text); }
.modal-fact-value code { font-size: 11px; }

.modal-link-row {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 9px 12px;
  border-radius: var(--radius-xs);
  margin-bottom: 10px;
  font-size: 12px;
  border: 1px solid var(--glass-border);
}
html[data-theme="dark"] .modal-link-row.source-row  { background: rgba(59,130,246,.14);  color: #bfdbfe; }
html[data-theme="dark"] .modal-link-row.source-row a{ color: #93c5fd; font-weight: 600; }
html[data-theme="dark"] .modal-link-row.spec-row    { background: rgba(34,197,94,.14);  color: #bbf7d0; }
html[data-theme="dark"] .modal-link-row.spec-row a  { color: #86efac; font-weight: 600; }
html[data-theme="dark"] .modal-link-row.handoff-row { background: rgba(234,179,8,.14);  color: #fde68a; }

html[data-theme="light"] .modal-link-row.source-row  { background: #eff6ff; color: #1e40af; }
html[data-theme="light"] .modal-link-row.source-row a{ color: #1d4ed8; font-weight: 600; }
html[data-theme="light"] .modal-link-row.spec-row    { background: #f0fdf4; color: #166534; }
html[data-theme="light"] .modal-link-row.spec-row a  { color: #15803d; font-weight: 600; }
html[data-theme="light"] .modal-link-row.handoff-row { background: #fefce8; color: #854d0e; }

.modal-link-row .row-icon { font-size: 13px; flex-shrink: 0; margin-top: 1px; }
.modal-link-row code { font-size: 11px; }

.modal-section {
  margin-bottom: 10px;
  border-radius: var(--radius-xs);
  overflow: hidden;
  border: 1px solid var(--glass-border);
}
.modal-section-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 9px 14px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--glass-border);
  cursor: default;
}
.modal-section-header.collapsible { cursor: pointer; user-select: none; }
.modal-section-header.collapsible:hover { background: var(--surface-3); }
.modal-section-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .55px; color: var(--text-muted);
}
.modal-section-toggle {
  font-size: 11px; color: var(--text-faint);
  transition: transform .2s;
  flex-shrink: 0;
}
.modal-section.collapsed .modal-section-toggle { transform: rotate(-90deg); }
.modal-section-body {
  padding: 13px 16px;
  font-size: 13.5px; color: var(--text);
  line-height: 1.7;
}
.modal-section.collapsed .modal-section-body { display: none; }

.modal-section-body p { margin-bottom: 8px; }
.modal-section-body p:last-child { margin-bottom: 0; }
.modal-section-body ul,
.modal-section-body ol { padding-left: 22px; margin: 6px 0 8px; }
.modal-section-body li           { margin-bottom: 5px; line-height: 1.6; }
.modal-section-body li:last-child{ margin-bottom: 0; }
.modal-section-body strong       { font-weight: 600; color: var(--text); }
.modal-section-body code         { font-size: 12px; }
.modal-section-body del          { color: var(--text-faint); text-decoration: line-through; }
.modal-section-body .subsection-heading {
  font-size: 12px; font-weight: 700; color: var(--text-muted);
  margin: 12px 0 4px; text-transform: uppercase; letter-spacing: .4px;
}
.modal-section-body .subsection-heading:first-child { margin-top: 0; }
"""

# ---------------------------------------------------------------------------
# JavaScript — improved renderText + collapsibles + filters + modal
# ---------------------------------------------------------------------------

INLINE_JS = r"""
// ── Utilities ────────────────────────────────────────────
function esc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

var PRIORITY_CLASS = {
  critical:'badge-priority-critical', high:'badge-priority-high',
  medium:'badge-priority-medium', low:'badge-priority-low',
  unspecified:'badge-priority-unspecified'
};
var APP_CLASS = {
  'knowledge':'badge-app-knowledge','app-1':'badge-app-1','app-2':'badge-app-2','app-3':'badge-app-3','app-4':'badge-app-4',
  'cross-app':'badge-app-cross','unknown':'badge-app-unknown'
};
var APP_LABEL = {
  'knowledge':'Knowledge.Healthcare','app-1':'medical_advisor','app-2':'ANOTE_mobile','app-3':'ANOTE-web','app-4':'Health-Analysis',
  'cross-app':'cross-app','unknown':'unknown'
};
var STATUS_CLASS = {
  inbox:'badge-status-inbox', triage:'badge-status-triage', active:'badge-status-active',
  review:'badge-status-review', blocked:'badge-status-blocked',
  backlog:'badge-status-backlog', done:'badge-status-done',
  tested:'badge-status-tested', deployed:'badge-status-deployed'
};
var STATUS_LABEL = {
  inbox:'Inbox', triage:'Triaged', active:'Active', review:'Review',
  blocked:'Blocked', backlog:'Backlog', done:'Done',
  tested:'Tested', deployed:'Deployed'
};

function badge(text, cls, title) {
  var ta = title ? ' title="' + esc(title) + '"' : '';
  return '<span class="badge ' + esc(cls) + '"' + ta + '>' + esc(text) + '</span>';
}

// ── Markdown-like renderer ────────────────────────────────
// Supports: paragraphs, unordered lists, ordered lists,
//           bold, inline code, strikethrough, subheadings (###).
// No external library; handles the patterns that appear in these task files.
function renderText(raw) {
  if (!raw || !raw.trim()) return '';

  // Inline formatting helper
  function inlineFmt(s) {
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/`([^`\n]+)`/g,   '<code>$1</code>');
    s = s.replace(/~~(.+?)~~/g,      '<del>$1</del>');
    return s;
  }

  var lines  = raw.split('\n');
  var html   = '';
  var state  = 'none'; // 'none' | 'ul' | 'ol' | 'p'
  var pLines = [];      // accumulate paragraph lines

  function flushPara() {
    if (!pLines.length) return;
    html += '<p>' + inlineFmt(pLines.join(' ').trim()) + '</p>';
    pLines = [];
  }
  function closeList() {
    if (state === 'ul') { html += '</ul>'; state = 'none'; }
    if (state === 'ol') { html += '</ol>'; state = 'none'; }
  }

  for (var i = 0; i < lines.length; i++) {
    var raw_line = lines[i];
    var line = raw_line.trim();

    // Blank line — flush paragraph; close list already closed inline
    if (!line) {
      if (state === 'p') { flushPara(); state = 'none'; }
      else if (state !== 'none') { /* leave lists open for next item */ }
      continue;
    }

    // Skip markdown table separator rows
    if (/^\|[-| :]+\|$/.test(line)) continue;

    // ### Sub-section heading within body
    if (/^###\s+/.test(line)) {
      if (state === 'p') { flushPara(); state = 'none'; }
      closeList();
      html += '<p class="subsection-heading">' + esc(line.replace(/^###\s+/, '')) + '</p>';
      continue;
    }

    // Markdown table row — render cells as plain text separated by ·
    if (/^\|/.test(line) && !/^\|[-| :]+\|$/.test(line)) {
      if (state === 'p') { flushPara(); state = 'none'; }
      closeList();
      var cells = line.split('|').map(function(c){ return c.trim(); }).filter(Boolean);
      if (cells.length) {
        html += '<p style="color:var(--text-muted);font-size:12.5px">'
              + cells.map(function(c){ return inlineFmt(esc(c)); }).join(' &middot; ')
              + '</p>';
      }
      continue;
    }

    // Ordered list item: "1. text", "12. text"
    if (/^\d+\.\s+/.test(line)) {
      if (state === 'p') { flushPara(); state = 'none'; }
      if (state === 'ul') { closeList(); }
      if (state !== 'ol') { html += '<ol>'; state = 'ol'; }
      var item = line.replace(/^\d+\.\s+/, '');
      html += '<li>' + inlineFmt(item) + '</li>';
      continue;
    }

    // Unordered list item: "- text" or "* text"
    if (/^[-*]\s+/.test(line)) {
      if (state === 'p') { flushPara(); state = 'none'; }
      if (state === 'ol') { closeList(); }
      if (state !== 'ul') { html += '<ul>'; state = 'ul'; }
      var item = line.replace(/^[-*]\s+/, '');
      html += '<li>' + inlineFmt(item) + '</li>';
      continue;
    }

    // Plain paragraph text — close lists first
    if (state === 'ul' || state === 'ol') {
      closeList();
    }
    state = 'p';
    pLines.push(line);
  }

  // Flush remainder
  if (state === 'p') flushPara();
  closeList();

  return html;
}

function listHtml(items) {
  if (!items || !items.length) return '';
  return '<ul>' + items.map(function(i){ return '<li>' + esc(i) + '</li>'; }).join('') + '</ul>';
}

// Build a named section block (non-collapsible)
function section(heading, contentHtml) {
  if (!contentHtml || !contentHtml.trim()) return '';
  return '<div class="modal-section">'
       + '<div class="modal-section-header">'
       +   '<span class="modal-section-title">' + esc(heading) + '</span>'
       + '</div>'
       + '<div class="modal-section-body">' + contentHtml + '</div>'
       + '</div>';
}

// Build a collapsible section block (starts collapsed)
function collapsibleSection(heading, contentHtml, startOpen) {
  if (!contentHtml || !contentHtml.trim()) return '';
  var collapsed = startOpen ? '' : ' collapsed';
  return '<div class="modal-section' + collapsed + '">'
       + '<div class="modal-section-header collapsible" onclick="toggleSection(this)">'
       +   '<span class="modal-section-title">' + esc(heading) + '</span>'
       +   '<span class="modal-section-toggle">▾</span>'
       + '</div>'
       + '<div class="modal-section-body">' + contentHtml + '</div>'
       + '</div>';
}

function toggleSection(headerEl) {
  var sec = headerEl.closest('.modal-section');
  if (sec) sec.classList.toggle('collapsed');
}

function factItem(label, valueHtml) {
  if (!valueHtml || !valueHtml.trim()) return '';
  return '<div class="modal-fact">'
       + '<div class="modal-fact-label">' + esc(label) + '</div>'
       + '<div class="modal-fact-value">' + valueHtml + '</div>'
       + '</div>';
}

// ── Modal core ────────────────────────────────────────────
var overlay = document.getElementById('task-modal-overlay');

function openModal(taskId) {
  var t = TASK_DATA[taskId];
  if (!t) return;

  var srcLink  = '../' + t.rel_path;
  var appLbl   = APP_LABEL[t.app]   || t.app;
  var appCls   = APP_CLASS[t.app]   || 'badge-app-unknown';
  var prioCls  = PRIORITY_CLASS[t.priority] || 'badge-priority-unspecified';
  var statLbl  = STATUS_LABEL[t.status] || t.status;
  var statCls  = STATUS_CLASS[t.status] || 'badge-status-backlog';
  var specInd  = t.has_spec
    ? '<span class="spec-indicator spec-yes">spec ✓</span>'
    : '<span class="spec-indicator spec-no">no spec</span>';

  // Header
  document.getElementById('modal-task-id').innerHTML =
    '<span>' + esc(t.id) + '</span>'
    + '<a class="modal-src-link" href="' + esc(srcLink) + '" target="_blank" '
    + 'title="Open source Markdown file">↗ source</a>';
  document.getElementById('modal-title').textContent = t.title;
  document.getElementById('modal-badges').innerHTML =
    badge(appLbl, appCls)
    + ' ' + badge(t.priority, prioCls)
    + ' ' + badge(statLbl, statCls)
    + ' ' + badge(t.type, 'badge-type')
    + ' ' + specInd;

  // Body
  var body = '';

  // ── Link rows ──
  body += '<div class="modal-link-row source-row">'
        + '<span class="row-icon">📄</span>'
        + '<span>Source: <a href="' + esc(srcLink) + '" target="_blank"><code>'
        + esc(t.rel_path) + '</code></a></span>'
        + '</div>';

  if (t.related_spec) {
    var specLinks = '';
    if (t.spec_files && t.spec_files.length) {
      var guessApp = (t.app && t.app !== 'unknown') ? t.app : 'app-3';
      specLinks = t.spec_files.map(function(f) {
        var p = '../specs/' + guessApp + '/' + f;
        return '<a href="' + esc(p) + '" target="_blank">' + esc(f) + '</a>';
      }).join(', ');
    } else {
      specLinks = esc(t.related_spec);
    }
    body += '<div class="modal-link-row spec-row">'
          + '<span class="row-icon">📋</span>'
          + '<span><strong>Spec:</strong> ' + specLinks + '</span>'
          + '</div>';
  }

  if (t.related_handoff) {
    body += '<div class="modal-link-row handoff-row">'
          + '<span class="row-icon">🔗</span>'
          + '<span><strong>Handoff:</strong> ' + esc(t.related_handoff) + '</span>'
          + '</div>';
  }

  // ── Quick facts grid ──
  var factsHtml = '';
  factsHtml += factItem('App',      badge(appLbl, appCls));
  factsHtml += factItem('Priority', badge(t.priority, prioCls));
  factsHtml += factItem('Status',   badge(statLbl, statCls));
  factsHtml += factItem('Type',     badge(t.type, 'badge-type'));
  factsHtml += factItem('Spec',     specInd);
  if (t.repo)    factsHtml += factItem('Repo',    '<code>' + esc(t.repo) + '</code>');
  if (t.created) factsHtml += factItem('Created', esc(t.created));
  if (t.author)  factsHtml += factItem('Author',  esc(t.author));
  body += '<div class="modal-facts-strip">' + factsHtml + '</div>';

  // ── Primary sections (always open) ──
  body += section('Problem / Summary',          renderText(t.problem || t.summary));
  body += section('Desired Outcome',            renderText(t.desired_outcome));
  body += section('Why It Matters',             renderText(t.why_it_matters));
  body += section('Constraints',                listHtml(t.constraints_list));
  body += section('Suspected Affected Areas',   listHtml(t.affected_areas_list));
  body += section('Open Questions / Unknowns',  listHtml(t.open_questions_list));
  body += section('Dependencies',               listHtml(t.dependencies_list));

  // ── Secondary sections (collapsible, start collapsed) ──
  body += collapsibleSection('Confirmed Facts', renderText(t.confirmed_facts), false);
  body += collapsibleSection('Assumptions',     renderText(t.assumptions),     false);
  body += collapsibleSection('Notes',           renderText(t.notes),           false);
  body += collapsibleSection('Reasoning',       renderText(t.reasoning),       false);
  body += collapsibleSection('Cross-App Considerations', renderText(t.cross_app), false);

  document.getElementById('modal-body').innerHTML = body;

  overlay.classList.add('modal-visible');
  document.body.classList.add('modal-open');
  document.getElementById('modal-close-btn').focus();
}

function closeModal() {
  overlay.classList.remove('modal-visible');
  document.body.classList.remove('modal-open');
}

overlay.addEventListener('click', function(e) {
  if (e.target === overlay) closeModal();
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});
document.getElementById('modal-close-btn').addEventListener('click', closeModal);

// Card → modal
document.querySelectorAll('.task-card').forEach(function(card) {
  card.addEventListener('click', function(e) {
    if (e.target.closest('.card-id')) return;
    openModal(card.dataset.id);
  });
  card.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openModal(card.dataset.id);
    }
  });
});

// ── Filters ──────────────────────────────────────────────
var searchInput    = document.getElementById('search-input');
var filterApp      = document.getElementById('filter-app');
var filterPriority = document.getElementById('filter-priority');
var filterStatus   = document.getElementById('filter-status');
var filterType     = document.getElementById('filter-type');
var hideDoneChk    = document.getElementById('hide-done');
var resetBtn       = document.getElementById('reset-filters');
var filterCount    = document.getElementById('filter-count');
var allCards       = Array.from(document.querySelectorAll('.task-card'));
var allCols        = Array.from(document.querySelectorAll('.kanban-col'));

function applyFilters() {
  var q        = searchInput.value.trim().toLowerCase();
  var app      = filterApp.value;
  var priority = filterPriority.value;
  var status   = filterStatus.value;
  var type     = filterType.value;
  var hideDone = hideDoneChk.checked;
  var visible  = 0;

  allCards.forEach(function(card) {
    var match = true;
    if (app      && card.dataset.app      !== app)      match = false;
    if (priority && card.dataset.priority !== priority) match = false;
    if (status   && card.dataset.status   !== status)   match = false;
    if (type     && card.dataset.type     !== type)      match = false;
    if (hideDone && card.dataset.status   === 'done')     match = false;
    if (hideDone && card.dataset.status   === 'tested')   match = false;
    if (hideDone && card.dataset.status   === 'deployed') match = false;
    if (q) {
      var id    = (card.dataset.id    || '').toLowerCase();
      var title = (card.dataset.title || '').toLowerCase();
      if (id.indexOf(q) === -1 && title.indexOf(q) === -1) match = false;
    }
    card.classList.toggle('hidden', !match);
    if (match) visible++;
  });

  allCols.forEach(function(col) {
    var cs = col.dataset.colStatus;
    if (hideDone && cs === 'done')     { col.style.display = 'none'; return; }
    if (hideDone && cs === 'tested')   { col.style.display = 'none'; return; }
    if (hideDone && cs === 'deployed') { col.style.display = 'none'; return; }
    col.style.display = '';
    var shown   = col.querySelectorAll('.task-card:not(.hidden)').length;
    var countEl = col.querySelector('.col-count');
    if (countEl) countEl.textContent = shown;
    var emptyEl = col.querySelector('.kanban-empty');
    if (emptyEl) emptyEl.style.display = shown === 0 ? '' : 'none';
  });

  var total = allCards.length;
  filterCount.textContent = visible === total
    ? 'Showing all ' + total + ' task' + (total !== 1 ? 's' : '')
    : 'Showing ' + visible + ' of ' + total + ' tasks';
}

function resetFilters() {
  searchInput.value = '';
  filterApp.value = filterPriority.value = filterStatus.value = filterType.value = '';
  hideDoneChk.checked = false;
  applyFilters();
}

searchInput.addEventListener('input',    applyFilters);
filterApp.addEventListener('change',     applyFilters);
filterPriority.addEventListener('change',applyFilters);
filterStatus.addEventListener('change',  applyFilters);
filterType.addEventListener('change',    applyFilters);
hideDoneChk.addEventListener('change',   applyFilters);
resetBtn.addEventListener('click',       resetFilters);

applyFilters();

// ── Theme toggle ─────────────────────────────────────────
(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  function sync() {
    var t = document.documentElement.getAttribute('data-theme');
    btn.setAttribute('aria-pressed', String(t === 'dark'));
  }
  sync();
  btn.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('kh-theme', next); } catch (e) {}
    sync();
  });
})();
"""

# ---------------------------------------------------------------------------
# Modal HTML skeleton (starts hidden; JS manages visibility)
# ---------------------------------------------------------------------------

MODAL_HTML = """
<!-- Task detail modal — starts hidden; opened by JS on card click -->
<div id="task-modal-overlay" class="modal-overlay"
     role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div id="task-modal-panel" class="modal-panel glass">
    <div class="modal-header">
      <div class="modal-header-left">
        <div class="modal-task-id" id="modal-task-id"></div>
        <div class="modal-title"   id="modal-title"></div>
        <div class="modal-badges"  id="modal-badges"></div>
      </div>
      <button class="modal-close" id="modal-close-btn" aria-label="Close detail panel">&#x2715;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
"""

# ---------------------------------------------------------------------------
# Full HTML assembly
# ---------------------------------------------------------------------------

def build_html(tasks: list[dict], warnings: list[str], priorities_html: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    warn_count = len(warnings)
    warn_inline = (
        f'<span class="warn-inline">⚠ {warn_count} warning{"s" if warn_count != 1 else ""}</span>'
        if warn_count else ""
    )

    status_summary_html, app_summary_html = render_summary_cards(tasks)
    filters_html  = render_filters()
    kanban_html   = render_kanban(tasks)
    warnings_html = render_warnings(warnings)

    task_json = build_task_json(tasks)
    task_json_safe = task_json.replace("</", "<\\/")
    js_with_data = f"var TASK_DATA = {task_json_safe};\n" + INLINE_JS

    theme_init_script = (
        "<script>"
        "(function(){"
        "try{var t=localStorage.getItem('kh-theme');"
        "document.documentElement.setAttribute('data-theme',t==='light'?'light':'dark');}"
        "catch(e){document.documentElement.setAttribute('data-theme','dark');}"
        "})();"
        "</script>"
    )

    theme_toggle_html = (
        '<button id="theme-toggle" class="theme-toggle" type="button" '
        'aria-label="Toggle color theme" aria-pressed="true" title="Toggle light/dark">'
        '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
        '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
        '</svg>'
        '</button>'
    )

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Knowledge.Healthcare — Task Dashboard</title>
  {theme_init_script}
  <style>
{INLINE_CSS}
  </style>
</head>
<body>

<div class="bg-blobs" aria-hidden="true"></div>

<header class="top-bar glass" aria-label="Overview">
  <div class="top-bar-inner">
    <div class="stats-row" role="list">
      {status_summary_html}
      <span class="stats-divider" aria-hidden="true"></span>
      {app_summary_html}
    </div>
    {theme_toggle_html}
  </div>
</header>

<div class="page-wrap">

  <section class="section">
    <div class="section-title">Filters</div>
    {filters_html}
  </section>

  <section class="section">
    <div class="section-title">Task Board &mdash; click a card to view details</div>
    {kanban_html}
  </section>

  <section class="section">
    <div class="section-title">Current Priorities</div>
    <div class="priorities-content glass">
      {priorities_html}
    </div>
  </section>

  <section class="section">
    <div class="section-title">Parser Warnings</div>
    <div class="warnings-section glass">
      {warnings_html}
    </div>
  </section>

</div>

<footer class="page-footer">
  Generated: {_esc(now)} &middot; Regenerate: <code>python3 scripts/generate_dashboard.py</code>{warn_inline}
</footer>

{MODAL_HTML}

<script>
{js_with_data}
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Knowledge.Healthcare Dashboard Generator ===")

    print("Building spec index…")
    spec_index = build_spec_index()
    print(f"  Found specs for tasks: {sorted(spec_index.keys()) or 'none'}")

    print("Loading tasks…")
    tasks, warnings = load_all_tasks(spec_index)
    print(f"  Loaded {len(tasks)} task(s), {len(warnings)} warning(s)")
    if warnings:
        for w in warnings:
            print(f"    ⚠  {w}")

    print("Loading current priorities…")
    priorities_html = load_current_priorities()

    print("Rendering HTML…")
    html = build_html(tasks, warnings, priorities_html)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"\n✓ Dashboard written to: {OUTPUT_FILE}")
    print(f"  Open with: open '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
