#!/usr/bin/env python3
"""Mechanical enforcement for the /r request protocol.

The model writes one canonical Report. This helper validates that Report and
extracts the only text allowed on screen: the Report's Lead.

Typical use:
    r_protocol.py init --history .requests/<file>.md --rname <rname> --opened <timestamp>

Normal turn (validate + append exact Report + emit exact Lead):
    r_protocol.py commit /tmp/r-report.md \
        --history .requests/20260908-134638-pod-drift-recheck.md \
        --human /tmp/r-human.md

Deliverable permission is durable request state set only at init:
    r_protocol.py init ... --deliverable

Exit status is non-zero on every protocol violation. `render` and `commit`
write NOTHING to stdout unless validation succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

GIST_MAX_WORDS = 50
COMPLETED_MAX_BULLETS = 4
NEEDS_MAX_BULLETS = 4
NEXT_MAX_BULLETS = 3
BODY_BULLET_MAX_WORDS = 40

DELIVERABLE_H = "**Deliverable**"
COMPLETED_H = "**Completed**"
NEEDS_H = "**Needs Attention**"
NEXT_H = "**Next Steps**"

RNAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
STATUS_RE = re.compile(
    r"^(?P<rname>[a-z0-9]+(?:-[a-z0-9]+)+) \| "
    r"(?P<rcode>(?:R--|0[0-9.][0p/\-])) \| "
    r"(?P<message>[A-Z ]+)$"
)
TURN_RE = re.compile(r"^## Turn (\d+)$", re.MULTILINE)
REPORT_STATUS_RE = re.compile(r"^\*\*Report:\*\*\s*\n\n([^\n]+)", re.MULTILINE)


class ProtocolError(Exception):
    pass


@dataclass(frozen=True)
class ParsedReport:
    raw: str
    status_line: str
    rname: str
    rcode: str
    rmessage: str
    gist_raw: str
    gist_plain: str
    lead: str
    deliverable: str | None
    completed: list[str] | None
    needs_attention: list[str] | None
    next_steps: list[str] | None
    needs_is_none: bool
    is_open: bool
    is_rejected: bool


def fail(errors: Iterable[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProtocolError(f"cannot read {path}: {exc}") from exc


def word_count(text: str) -> int:
    # Markdown punctuation does not count as words; versions/paths remain one token.
    return len(re.findall(r"\S+", text.strip()))


def plain_markdown(text: str) -> str:
    text = text.strip()
    # Enough normalization for deterministic Gist-prefix checks.
    text = re.sub(r"^\*\*(.+?)\*\*", r"\1", text)
    return text.replace("**", "").strip()




def validate_rname(rname: str) -> list[str]:
    errors: list[str] = []
    if not RNAME_RE.fullmatch(rname):
        errors.append("rname must be a lowercase semantic slug with at least two hyphen-separated parts")
    if len(rname) > 25:
        errors.append("rname exceeds 25 characters")
    return errors


def tcount_value(ch: str) -> int | None:
    if ch == ".":
        return None
    return int(ch)


def expected_tchar(value: int) -> str:
    return "." if value >= 10 else str(value)


def history_rname(text: str) -> str | None:
    first = text.splitlines()[0].strip() if text.splitlines() else ""
    if first.startswith("# "):
        return first[2:].strip()
    return None


def history_deliverable_enabled(text: str) -> bool:
    """Read durable Deliverable permission from the request header.

    Histories created before this field existed are treated as Deliverable-disabled.
    This is the safe default: a Deliverable may never be enabled implicitly.
    """
    for raw in text.splitlines()[:10]:
        line = raw.strip()
        if line.startswith("Deliverable:"):
            value = line.split(":", 1)[1].strip().lower()
            if value == "yes":
                return True
            if value == "no":
                return False
            raise ProtocolError("history header Deliverable field must be 'yes' or 'no'")
    return False


def previous_report_status(text: str) -> str | None:
    matches = REPORT_STATUS_RE.findall(text)
    return matches[-1].strip() if matches else None


def validate_transition(current_history: str, parsed: "ParsedReport", preserve: bool) -> list[str]:
    errors: list[str] = []
    hrname = history_rname(current_history)
    if hrname != parsed.rname:
        errors.append(f"history rname {hrname!r} does not match Report rname {parsed.rname!r}")

    prev_line = previous_report_status(current_history)
    if prev_line is None:
        if preserve:
            errors.append("a preserved-TCOUNT turn requires an already-open previous turn")
            return errors
        if parsed.is_rejected:
            return errors
        turns = parsed.rcode[1]
        if parsed.is_open:
            if turns != "1":
                errors.append("first open response must carry TCOUNT=1")
        elif turns != "0":
            errors.append("first closing response must carry TCOUNT=0")
        return errors

    m = STATUS_RE.fullmatch(prev_line)
    if not m:
        errors.append("cannot parse previous Report status bar from history")
        return errors

    prev_rcode = m.group("rcode")
    if prev_rcode == "R--" or not prev_rcode.endswith("-"):
        errors.append("cannot commit another turn after the request has closed")
        return errors

    if parsed.is_rejected:
        errors.append("an already-active accepted request cannot become R--")
        return errors

    prev_t = tcount_value(prev_rcode[1])
    cur_t = parsed.rcode[1]

    if preserve:
        if not parsed.is_open:
            errors.append("a preserved-TCOUNT turn (event or protocol-error) cannot close the request")
        if cur_t != prev_rcode[1]:
            errors.append("a preserved-TCOUNT turn (event or protocol-error) must leave TCOUNT unchanged")
        return errors

    if prev_t is None:
        if cur_t != ".":
            errors.append("once TCOUNT reaches '.', later turns must keep '.'")
        return errors

    expected = prev_t + (1 if parsed.is_open else 0)
    exp_char = expected_tchar(expected)
    if cur_t != exp_char:
        action = "increment" if parsed.is_open else "preserve"
        errors.append(
            f"TCOUNT transition invalid: previous {prev_rcode[1]}, current {cur_t}; "
            f"an {'open' if parsed.is_open else 'closing'} response must {action} TCOUNT to {exp_char}"
        )
    return errors

def expected_message(rcode: str) -> str:
    if rcode == "R--":
        return "REJECTED"

    turns = rcode[1]
    closure = rcode[2]

    if closure == "-":
        if turns == "0":
            raise ProtocolError("rcode 00- is forbidden")
        return "NEEDS HUMAN"
    if closure == "0":
        return "OK" if turns == "0" else "RESOLVED"
    if closure == "p":
        return "PARTIALLY RESOLVED"
    if closure == "/":
        return "UNRESOLVED"
    raise ProtocolError(f"unsupported closure character in rcode {rcode}")


def split_lead(text: str) -> tuple[str, str, list[str]]:
    """Return status line, raw gist paragraph, lines after gist."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Canonical Report starts immediately with the status bar.
    if not lines or not lines[0].strip():
        raise ProtocolError("Report must start with the status bar; no blank/header may precede it")
    status = lines[0].rstrip()

    if len(lines) < 3 or lines[1].strip() != "":
        raise ProtocolError("status bar must be followed by exactly one blank line before the Gist")

    gist_lines: list[str] = []
    i = 2
    while i < len(lines) and lines[i].strip() != "":
        gist_lines.append(lines[i].strip())
        i += 1

    if not gist_lines:
        raise ProtocolError("Gist is missing")

    gist_raw = " ".join(gist_lines).strip()
    rest = lines[i + 1 :] if i < len(lines) else []
    return status, gist_raw, rest


def nonblank(lines: list[str]) -> list[str]:
    return [line.rstrip() for line in lines if line.strip()]


def find_last(lines: list[str], heading: str, before: int | None = None) -> int:
    end = len(lines) if before is None else before
    for i in range(end - 1, -1, -1):
        if lines[i].strip() == heading:
            return i
    return -1


def parse_prefix_as_deliverable(prefix_lines: list[str], errors: list[str]) -> str | None:
    p = prefix_lines[:]
    while p and not p[0].strip():
        p.pop(0)
    while p and not p[-1].strip():
        p.pop()
    if not p:
        return None
    if p[0].strip() != DELIVERABLE_H:
        errors.append(
            f"unexpected content between Gist and Body; only optional {DELIVERABLE_H} is allowed"
        )
        return None
    content = "\n".join(p[1:]).strip()
    if not content:
        errors.append("Deliverable heading exists but the Deliverable is empty")
        return ""
    return content


def parse_bullets(
    lines: list[str],
    section_name: str,
    max_bullets: int,
    errors: list[str],
    *,
    allow_none: bool = True,
) -> tuple[list[str], bool]:
    rows = nonblank(lines)
    if not rows:
        errors.append(f"{section_name} must contain a bullet list")
        return [], False

    if rows == ["- None."]:
        if not allow_none:
            errors.append(f"{section_name} cannot be None for an open request")
        return [], True

    if any(row != row.lstrip() for row in rows):
        errors.append(f"{section_name} contains an indented/nested or continuation line")

    bullets: list[str] = []
    for row in rows:
        if not row.startswith("- "):
            errors.append(
                f"{section_name} must contain only top-level one-line bullets; invalid line: {row!r}"
            )
            continue
        body = row[2:].strip()
        if not body:
            errors.append(f"{section_name} contains an empty bullet")
            continue
        if word_count(body) > BODY_BULLET_MAX_WORDS:
            errors.append(
                f"{section_name} bullet exceeds {BODY_BULLET_MAX_WORDS} words: {body!r}"
            )
        bullets.append(body)

    if len(bullets) > max_bullets:
        errors.append(
            f"{section_name} has {len(bullets)} bullets; maximum is {max_bullets}"
        )
    return bullets, False


def parse_report(
    text: str, *, deliverable_enabled: bool = False, is_event: bool = False
) -> ParsedReport:
    # An event turn stays open in its status bar but reports rather than waits, so it takes
    # the closing Body shape and the closing Gist-opener rules. Forcing the open-turn shape
    # on it would demand an 'Action required:' Gist for work that needs nothing.
    errors: list[str] = []
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"

    try:
        status_line, gist_raw, rest = split_lead(text)
    except ProtocolError as exc:
        raise ProtocolError(str(exc)) from exc

    m = STATUS_RE.fullmatch(status_line)
    if not m:
        errors.append(
            "invalid status bar; expected '<semantic-name> | <rcode> | <rmessage>'"
        )
        # Continue with safe placeholders so all useful errors can be reported.
        rname, rcode, rmessage = "invalid-name", "R--", "REJECTED"
    else:
        rname = m.group("rname")
        rcode = m.group("rcode")
        rmessage = m.group("message")
        errors.extend(validate_rname(rname))
        try:
            exp = expected_message(rcode)
            if rmessage != exp:
                errors.append(
                    f"rmessage {rmessage!r} does not match rcode {rcode}; expected {exp!r}"
                )
        except ProtocolError as exc:
            errors.append(str(exc))

    if gist_raw.startswith(("#", "- ", "* ", ">", "```")):
        errors.append("Gist must be a plain paragraph, not a heading/list/quote/code block")
    if word_count(gist_raw) > GIST_MAX_WORDS:
        errors.append(
            f"Gist has {word_count(gist_raw)} words; maximum is {GIST_MAX_WORDS}"
        )

    gist_plain = plain_markdown(gist_raw)
    is_rejected = rcode == "R--"
    is_open = (not is_rejected) and rcode.endswith("-")
    # Body shape and Gist opener follow the closing rules on an event turn (see above);
    # is_open still governs state, TCOUNT, and the transition check.
    open_shape = is_open and not is_event

    # Parse Body from the bottom so a Deliverable may contain arbitrary markdown.
    deliverable: str | None = None
    completed: list[str] | None = None
    needs: list[str] | None = None
    next_steps: list[str] | None = None
    needs_is_none = False

    if open_shape:
        needs_i = find_last(rest, NEEDS_H)
        if needs_i < 0:
            errors.append(f"open Report must contain exactly one {NEEDS_H} section")
            prefix, needs_lines = rest, []
        else:
            prefix, needs_lines = rest[:needs_i], rest[needs_i + 1 :]
        deliverable = parse_prefix_as_deliverable(prefix, errors)
        needs, needs_is_none = parse_bullets(
            needs_lines,
            "Needs Attention",
            NEEDS_MAX_BULLETS,
            errors,
            allow_none=False,
        )

        # Closing-only headings after/around the open body are forbidden.
        for heading in (COMPLETED_H, NEXT_H):
            if any(line.strip() == heading for line in rest):
                errors.append(f"open Report must not contain {heading}")
    else:
        next_i = find_last(rest, NEXT_H)
        needs_i = find_last(rest, NEEDS_H, before=next_i if next_i >= 0 else None)
        completed_i = find_last(rest, COMPLETED_H, before=needs_i if needs_i >= 0 else None)

        if next_i < 0:
            errors.append(f"closing Report must contain {NEXT_H}")
            next_i = len(rest)
        if needs_i < 0:
            errors.append(f"closing Report must contain {NEEDS_H}")
            needs_i = next_i
        if completed_i < 0:
            errors.append(f"closing Report must contain {COMPLETED_H}")
            completed_i = needs_i

        if not (completed_i < needs_i < next_i):
            errors.append("closing Body sections must be ordered Completed → Needs Attention → Next Steps")

        prefix = rest[:completed_i]
        completed_lines = rest[completed_i + 1 : needs_i]
        needs_lines = rest[needs_i + 1 : next_i]
        next_lines = rest[next_i + 1 :] if next_i < len(rest) else []

        deliverable = parse_prefix_as_deliverable(prefix, errors)
        completed, _ = parse_bullets(
            completed_lines, "Completed", COMPLETED_MAX_BULLETS, errors, allow_none=True
        )
        needs, needs_is_none = parse_bullets(
            needs_lines, "Needs Attention", NEEDS_MAX_BULLETS, errors, allow_none=True
        )
        next_steps, _ = parse_bullets(
            next_lines, "Next Steps", NEXT_MAX_BULLETS, errors, allow_none=True
        )

    # Deliverable permission is durable request-level state, never a per-turn choice.
    if deliverable and not deliverable_enabled:
        errors.append("Report contains a Deliverable, but this request was not opened with -d")

    # A -d request may remain open before its sidecar artifact is ready. Fully or
    # partially resolved closure must contain it; rejected/unresolved closure may omit it.
    if deliverable_enabled and not deliverable and not is_open and not is_rejected:
        closure = rcode[2] if len(rcode) == 3 else "?"
        if closure in ("0", "p"):
            errors.append("request was opened with -d, so resolved/partial closure requires a Deliverable")

    # Gist/state consistency.
    prefix = gist_plain.lower()
    if is_rejected:
        if not prefix.startswith("rejected:"):
            errors.append("R-- Gist must start with 'Rejected:'")
    elif open_shape:
        if not prefix.startswith("action required:"):
            errors.append("open request Gist must start with 'Action required:'")
    else:
        closure = rcode[2] if len(rcode) == 3 else "?"
        if needs_is_none:
            required = {
                "0": "complete:",
                "p": "partially complete:",
                "/": "unresolved:",
                # An event turn stays open ('-'); with nothing owed, what completed is the
                # delegated work the event reports.
                "-": "complete:",
            }.get(closure)
            if required and not prefix.startswith(required):
                errors.append(f"Gist must start with {required!r} for this closure state")
        else:
            if not prefix.startswith("action required:"):
                errors.append(
                    "Needs Attention is non-empty, so Gist must start with 'Action required:'"
                )

    if errors:
        raise ProtocolError("\n".join(errors))

    lead = f"{status_line}\n\n{gist_raw}"
    return ParsedReport(
        raw=text.rstrip() + "\n",
        status_line=status_line,
        rname=rname,
        rcode=rcode,
        rmessage=rmessage,
        gist_raw=gist_raw,
        gist_plain=gist_plain,
        lead=lead,
        deliverable=deliverable,
        completed=completed,
        needs_attention=needs,
        next_steps=next_steps,
        needs_is_none=needs_is_none,
        is_open=is_open,
        is_rejected=is_rejected,
    )



CONFIG_LINE_RE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<value>.*)$")


def _read_config_file(path: Path) -> dict[str, str]:
    """Flat key: value pairs. The config is one level deep; a full YAML parser would only
    add a dependency and accept nesting this format does not have."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = CONFIG_LINE_RE.match(line)
        if m:
            out[m.group("key")] = m.group("value").strip().strip("\"'")
    return out


def resolve_config(skill_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return the effective config and, per key, which file it came from.

    config.yaml is committed and mandatory — it is the schema of record, so a key absent
    from it is not a setting. config.local.yaml is gitignored, optional, and per-machine;
    any key it defines wins.
    """
    base_path = skill_dir / "config.yaml"
    if not base_path.is_file():
        raise ProtocolError(f"config.yaml is required and was not found at {base_path}")

    effective = _read_config_file(base_path)
    source = dict.fromkeys(effective, "config.yaml")

    local_path = skill_dir / "config.local.yaml"
    if local_path.is_file():
        for key, value in _read_config_file(local_path).items():
            if key not in effective:
                raise ProtocolError(
                    f"config.local.yaml sets unknown key {key!r}; "
                    "every key must be declared in config.yaml first"
                )
            effective[key] = value
            source[key] = "config.local.yaml"

    return effective, source


def cmd_config(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).resolve().parent
    try:
        effective, source = resolve_config(skill_dir)
    except (ProtocolError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if args.key:
        if args.key not in effective:
            print(f"ERROR: no such key {args.key!r} in config.yaml", file=sys.stderr)
            return 3
        value = effective[args.key]
        # A path is relative to the directory holding config.yaml unless it is already
        # absolute or ~-anchored, so a shared location survives every worktree.
        if args.key.endswith("_path") and not value.startswith(("/", "~")):
            value = str((skill_dir / value).resolve())
        elif args.key.endswith("_path"):
            value = str(Path(value).expanduser())
        print(value)
        return 0

    for key in sorted(effective):
        print(f"{key}: {effective[key]}    # {source[key]}")
    return 0


def _session_id() -> str:
    """$CLAUDE_CODE_SESSION_ID scopes the pointer to one running session. Concurrent
    sessions sharing a worktree therefore still get distinct pointer files."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID", "default")


def _pointer_path(skill_dir: Path) -> Path:
    """Local per-worktree, deliberately independent of `history_path`: history_path may be
    repointed at a directory shared across worktrees/machines (config.local.yaml), and a
    pointer stored there would reintroduce the exact cross-session collision it exists to
    prevent. This path always resolves inside THIS worktree's checkout of the skill."""
    return skill_dir / ".active" / f"{_session_id()}.txt"


def _write_pointer(skill_dir: Path, *, rname: str, history: str, opened: str, tchar: str) -> None:
    path = _pointer_path(skill_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"rname: {rname}\nhistory: {history}\nopened: {opened}\ntcount: {tchar}\n",
            encoding="utf-8",
        )
    except OSError:
        pass  # best-effort convenience state; the history file remains authoritative


def _clear_pointer(skill_dir: Path) -> None:
    try:
        _pointer_path(skill_dir).unlink(missing_ok=True)
    except OSError:
        pass


def _read_pointer(skill_dir: Path) -> dict[str, str] | None:
    path = _pointer_path(skill_dir)
    if not path.is_file():
        return None
    try:
        return _read_config_file(path)
    except OSError:
        return None


def cmd_active(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).resolve().parent
    pointer = _read_pointer(skill_dir)
    if pointer is None:
        print("ERROR: no active request for this session", file=sys.stderr)
        return 1
    for key in ("rname", "history", "opened", "tcount"):
        print(f"{key}: {pointer.get(key, '')}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    errors = validate_rname(args.rname)
    if not args.opened.strip():
        errors.append("--opened must be non-empty")
    if errors:
        fail(errors)
        return 2

    history = Path(args.history)
    if history.exists():
        print(f"ERROR: history file already exists: {history}", file=sys.stderr)
        return 3
    try:
        history.parent.mkdir(parents=True, exist_ok=True)
        history.write_text(
            f"# {args.rname}\n\nOpened: {args.opened.strip()}\n\n"
            f"Deliverable: {'yes' if args.deliverable else 'no'}\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: cannot create history file: {exc}", file=sys.stderr)
        return 3

    skill_dir = Path(__file__).resolve().parent
    _write_pointer(
        skill_dir,
        rname=args.rname,
        history=str(history),
        opened=args.opened.strip(),
        tchar="0",
    )
    return 0


def _standalone_deliverable_enabled(history_path: str | None) -> bool:
    if not history_path:
        return False
    history = Path(history_path)
    if not history.exists():
        raise ProtocolError(f"history file does not exist: {history}")
    return history_deliverable_enabled(history.read_text(encoding="utf-8"))


def cmd_check(args: argparse.Namespace) -> int:
    try:
        parsed = parse_report(
            read_text(args.report),
            deliverable_enabled=_standalone_deliverable_enabled(args.history),
        )
    except (ProtocolError, OSError) as exc:
        fail(str(exc).splitlines())
        return 2
    print(
        f"OK: {parsed.rname} {parsed.rcode}; Gist={word_count(parsed.gist_raw)} words; "
        f"Deliverable={'yes' if parsed.deliverable else 'no'}",
        file=sys.stderr,
    )
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        parsed = parse_report(
            read_text(args.report),
            deliverable_enabled=_standalone_deliverable_enabled(args.history),
        )
    except (ProtocolError, OSError) as exc:
        fail(str(exc).splitlines())
        return 2
    # HARD RULE: stdout is the exact user-visible response and nothing else.
    sys.stdout.write(parsed.lead + "\n")
    return 0


def quote_human(text: str) -> str:
    lines = text.rstrip("\n").splitlines() or [""]
    return "\n".join("> " + line if line else ">" for line in lines)


def cmd_commit(args: argparse.Namespace) -> int:
    is_event = args.event is not None
    is_protocol_error = args.protocol_error is not None
    try:
        report_text = read_text(args.report)
        # An event turn has no human message: delegated work reported back on its own.
        # A protocol-error turn (e.g. `/r <prompt>` while another request is active) is
        # likewise not a real human reply to the active request — it is the collision itself.
        if is_event:
            pairing_text = args.event.strip()
        elif is_protocol_error:
            pairing_text = args.protocol_error.strip()
        else:
            pairing_text = read_text(args.human)
    except ProtocolError as exc:
        fail(str(exc).splitlines())
        return 2

    if is_event and not pairing_text:
        print("ERROR: --event needs a non-empty description", file=sys.stderr)
        return 2
    if is_protocol_error and not pairing_text:
        print("ERROR: --protocol-error needs a non-empty description", file=sys.stderr)
        return 2

    history = Path(args.history)
    if not history.exists():
        print(
            f"ERROR: history file does not exist: {history}. Create its OPENING header first.",
            file=sys.stderr,
        )
        return 3

    try:
        current = history.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read history file: {exc}", file=sys.stderr)
        return 3

    try:
        deliverable_enabled = history_deliverable_enabled(current)
        parsed = parse_report(
            report_text, deliverable_enabled=deliverable_enabled, is_event=is_event
        )
    except ProtocolError as exc:
        fail(str(exc).splitlines())
        return 2

    # An event turn is an input to the request, not an outcome of it: nothing was asked of
    # the human, so TCOUNT is preserved and the request cannot close on it. A protocol-error
    # turn (an illegal `/r <prompt>` while this request is already active) is not a real reply
    # to the request either, so it preserves TCOUNT the same way — but it stays in the open-turn
    # Body shape (only Needs Attention), since the active request's own state is untouched.
    # Only these two structurally distinct turn shapes may preserve TCOUNT; an ordinary
    # `--human` turn always follows the increment-or-close rule below, with no escape hatch.
    transition_errors = validate_transition(current, parsed, is_event or is_protocol_error)
    if transition_errors:
        if is_event:
            transition_errors = [
                e.replace(
                    "a preserved-TCOUNT turn (event or protocol-error) must leave TCOUNT unchanged",
                    "an event turn cannot change TCOUNT; nothing was asked of the human",
                ).replace(
                    "a preserved-TCOUNT turn (event or protocol-error) cannot close the request",
                    "an event turn cannot close the request; closure stays '-'",
                )
                for e in transition_errors
            ]
        elif is_protocol_error:
            transition_errors = [
                e.replace(
                    "a preserved-TCOUNT turn (event or protocol-error) must leave TCOUNT unchanged",
                    "a protocol-error turn cannot change TCOUNT; the active request's state is preserved",
                ).replace(
                    "a preserved-TCOUNT turn (event or protocol-error) cannot close the request",
                    "a protocol-error turn cannot close the request; the active request stays open",
                )
                for e in transition_errors
            ]
        fail(transition_errors)
        return 2

    turns = [int(x) for x in TURN_RE.findall(current)]
    turn_no = (max(turns) + 1) if turns else 1

    digest = hashlib.sha256(
        (pairing_text.rstrip() + "\n\0\n" + parsed.raw.rstrip()).encode("utf-8")
    ).hexdigest()[:16]
    marker = f"<!-- r-turn:{digest} -->"
    if marker in current:
        print("ERROR: this exact turn is already committed to history", file=sys.stderr)
        return 4

    label = "Event" if is_event else ("Protocol Error" if is_protocol_error else "Human")
    block = (
        f"\n\n---\n\n## Turn {turn_no}\n\n"
        f"{marker}\n\n"
        f"**{label}:**\n\n{quote_human(pairing_text)}\n\n"
        f"**Report:**\n\n{parsed.raw.rstrip()}\n"
    )

    try:
        with history.open("a", encoding="utf-8") as fh:
            fh.write(block)
    except OSError as exc:
        print(f"ERROR: cannot append history file: {exc}", file=sys.stderr)
        return 3

    # Keep this session's local pointer in step with the request it tracks: cleared on
    # closure, refreshed with the new TCOUNT otherwise. Best-effort — the history file
    # just written is the actual source of truth.
    skill_dir = Path(__file__).resolve().parent
    if parsed.rcode[-1] != "-":
        _clear_pointer(skill_dir)
    else:
        pointer = _read_pointer(skill_dir) or {}
        _write_pointer(
            skill_dir,
            rname=parsed.rname,
            history=str(history),
            opened=pointer.get("opened", ""),
            tchar=parsed.rcode[1],
        )

    # Only after validation + successful append do we emit the canonical Lead.
    sys.stdout.write(parsed.lead + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate /r Reports and deterministically render the on-screen Lead."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser(
        "config",
        help="print the effective config: config.local.yaml layered over config.yaml",
    )
    p.add_argument("--key", help="print just this key's effective value")
    p.add_argument("--skill-dir", help="directory holding config.yaml (default: this script's)")

    p = sub.add_parser(
        "active",
        help="print this session's active-request pointer (rname/history/opened/tcount); "
        "exit 1 if none. Local per-worktree and session-scoped — never scan history_path "
        "to find 'the' active request",
    )
    p.add_argument("--skill-dir", help="directory holding the .active/ pointer store (default: this script's)")

    p = sub.add_parser("init", help="create a new request history header")
    p.add_argument("--history", required=True, help="new request history file")
    p.add_argument("--rname", required=True, help="semantic request name")
    p.add_argument("--opened", required=True, help="opening timestamp for the durable header")
    p.add_argument(
        "--deliverable",
        action="store_true",
        help="record that the request was explicitly opened with -d",
    )

    for name, help_text in (
        ("check", "validate a canonical Report; writes diagnostics only to stderr"),
        ("render", "validate a Report and emit its exact Lead to stdout"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("report", help="path to canonical Report markdown")
        p.add_argument(
            "--history",
            help="request history used to read durable Deliverable permission; omitted means disabled",
        )

    p = sub.add_parser(
        "commit",
        help="validate Report, append Human+Report to history, then emit exact Lead",
    )
    p.add_argument("report", help="path to canonical Report markdown")
    p.add_argument("--history", required=True, help="existing append-only request history file")
    pairing = p.add_mutually_exclusive_group(required=True)
    pairing.add_argument("--human", help="file containing the current human message")
    pairing.add_argument(
        "--event",
        help="one-line description of delegated work that completed, for an event turn "
        "(no human message; TCOUNT is preserved and the request stays open)",
    )
    pairing.add_argument(
        "--protocol-error",
        help="one-line description of an illegal `/r <prompt>` received while this request "
        "is already active, for a protocol-error turn (no human message; TCOUNT is preserved, "
        "the active request's state is untouched, and the request stays open). This is the "
        "only way to preserve TCOUNT on an open turn — an ordinary --human turn always "
        "increments or closes.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "config":
        return cmd_config(args)
    if args.command == "active":
        return cmd_active(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "check":
        return cmd_check(args)
    if args.command == "render":
        return cmd_render(args)
    if args.command == "commit":
        return cmd_commit(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
