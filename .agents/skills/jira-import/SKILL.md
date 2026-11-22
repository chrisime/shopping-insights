---
name: jira-import
description: Use before drafting a proposal in the jira-driven schema, whenever a Jira ticket ID or URL is mentioned, or when a change's requirements originate from a Jira ticket (Summary, Description, Acceptance Criteria). Also use to re-import a ticket after it has been answered, to fold the reply into the change's Decision Questions and Open Questions, and to export still-open questions (DQ and FQ) to the ticket as a Jira comment (guided, MCP-first with a manual fallback).
---

# Jira Import

## Overview

Load a Jira ticket's content verbatim before the `proposal` artifact is created, so the proposal's `## Source` section is a faithful copy of the ticket rather than a paraphrase. This runs before `opsx-propose` / `opsx-new` drafts the proposal.

## Access Probe

Resolve Jira access in this order; stop at the first match:

1. An `opencode.json` MCP server whose name matches `/jira/i` (e.g. `"jira"` with the `mcp-atlassian` package). This is the project's configured access path; the server is launched from `opencode.json` with `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN` supplied via the environment.
2. Environment variables: `JIRA_URL` and (`JIRA_API_TOKEN`, or `JIRA_USERNAME` + `JIRA_API_TOKEN`). For a direct HTTP fetch when no MCP server is present.

If neither exists, there is no Jira access: fetch is impossible, so ask the user to paste the ticket fields verbatim (see below). Never invent ticket content.

## Workflow

1. Identify the ticket: a ticket ID (e.g. `PROJ-123`) or a Jira URL supplied by the user, or the current change's context if already recorded.
2. Run the access probe. With access, fetch the ticket by calling the **`jira_get_issue`** MCP tool directly with the ticket key (e.g. `jira_get_issue("PROJ-123")`) — do not guess alternate names (`jira_search`, `get_issue`, a URL fetch, etc.). The opencode config exposes the MCP server's tools as callable functions, so invoke `jira_get_issue` directly. If the server is unreachable or `jira_get_issue` is not exposed, ask the user to paste the three fields verbatim rather than summarizing from memory.
3. Populate the proposal template's `## Source` section with the verbatim content:
   - `Ticket:` the ticket ID
   - `Summary:` verbatim Summary field
   - `Description:` verbatim Description field (or a link, if too long to inline)
   - `Acceptance Criteria:` each AC as its own numbered line, verbatim and in ticket order
4. Do not rewrite, shorten, or interpret the AC lines at this stage - interpretation happens later, during `grill-me` interrogation and when the specs step traces each AC to a Gherkin scenario via `<!-- AC: TICKET-ID#N -->`.
5. If any field is missing or the ticket cannot be reached, record that explicitly in `## Open Questions` rather than inventing content.

## AC Detection In The Description

Acceptance Criteria usually live in the ticket Description, but the exact
format varies between teams. Locate the AC group by anchor, never by guessing:

- Anchors (case-insensitive): `ACs`, `AC`, `Acceptance Criteria`,
  `Akzeptanzkriterien`.
- The first matching anchor in the text wins; anything after it, down to the
  next heading or the end, is the AC group.
- Split the group into individual AC lines and show the split to the user for
  confirmation before writing it to `## Source` - formats differ, so confirm
  rather than assume the boundaries.
- If no anchor is found, ask the user where the Acceptance Criteria are
  located; do not assume a split. The user's answer is noted and the ACs are
  then taken verbatim.

## Notes

- This skill only concerns the `proposal` step. Acceptance Criteria traceability into specs (the `<!-- AC: TICKET-ID#N -->` comments and Gherkin scenarios) is handled by the `specs` artifact instruction in the `jira-driven` schema and by the `gherkin-authoring` skill.
- Keep all content in English, per project convention, even if the source ticket is in another language - translate rather than mix languages within the proposal.

## Re-Import After A Ticket Conversation

The same skill, invoked again once the ticket owner has answered the change's
open questions. On-call only - run it when the user gives the resume signal
(e.g. "ticket answer for PROJ-123 arrived"), never automatically and never by
polling.

1. Load the ticket verbatim again (Summary, Description, Acceptance Criteria) by calling `jira_get_issue` as above.
2. Diff the fresh content against the change's `## Source`, `## Decision
   Questions` and `## Open Questions` in `proposal.md`, one entry at a time.
3. For each answered gap: record the outcome (e.g. new/changed AC moved first
   into `## Source`, or a clarification note), tick the checkbox (`- [ ]` →
   `- [x]`), and keep the reason plus a short note of the answer. For a
   resolved DQ the outcome is a decision (PO answer in the ticket or a team
   decision) — record it as a `Decision:` note and set the status to
   `resolved`. `resolved` is a latch: NEVER flip it back to `awaiting-answers`
   on any later re-import, even if the ticket changed again.
4. Leave unanswered gaps as `- [ ]`; they stay open for the next round. A
   re-import with an unchanged ticket leaves `awaiting-answers` DQs open as-is
   (no new comment, no status change).
5. If all questions are answered, unfreeze the AC numbering: resolve every
   provisional `[ACx]` handle to its final number and position, and stop
   referring to `-DELETED` entries. Until that unfreeze, do not commit to
   final AC numbers.

### AC Freeze Rules

AC numbering freezes when the change's specs are created (the `<!-- AC:
TICKET-ID#N -->` anchors exist). Until then, and especially while questions
are still open, ACs use **provisional handles** instead of final numbers:

- `[ACx] (e.g. [AC3])` — a question for this AC is still open; it gets its
  final number at unfreeze (and its `[ACx]` handle graduates to the
  `<!-- AC: TICKET-ID#N -->` anchor). The `[ACx]` handle is the proposal-level
  provisional standing in for `-TBD`.
- `[ACx] DELETED (e.g. [AC5] DELETED)` — the ticket struck this AC; it stays
  visible in `## Source` for audit (when and why it left), but it is never
  referenced by scenarios and must not carry an `<!-- AC: -->` comment.

After unfreeze the numbering is authoritative, and only two mutations are
allowed:

- **append** — a new AC gets the next number (`AC-N+1`); existing anchors are
  unchanged.
- **supersede** — a struck AC is annotated `DELETED` in `## Source` and left
  unreferenced; existing anchors are unchanged.

Renumbering existing ACs after the freeze is never allowed.

### Drift Warnings

After every re-import, compare the fresh AC list against `## Source` and
report, never silently accept:

- **more ACs** — new AC detected, not yet traced to a scenario.
- **fewer ACs** — an AC was removed in the ticket; decide freeze-annotate
  (DELETED) or confirm.
- **shifted ACs** — numbering or wording moved; report it so the freeze rules
  can be applied deliberately.

## Export: Questions → Jira

After Grill-Me, still-open questions become a Jira ticket comment so the
reporter/PO can confirm or answer them. The unified format is the single source
of truth defined in the proposal template:

```
Proposal line:   - [ ] <AC> — [FQx] · <gap>          (feedback question)
Jira comment:    <AC> — [FQx] · <gap>

Proposal line:   - [ ] [DQx] · <decision question>   (decision question)
Jira comment:    [DQx] · <decision question>
```

The `[FQx]` / `[DQx]` handles are the question's stable process identity
(assigned at Grill-Me time, never renamed, independent of block position and
AC numbering). They are the deterministic anchors for the export's pre-sync:
a question already sent is identified by its handle and is never sent twice.

DQ comments target the ticket author (PO/ReqEng — tickets are written by them,
so the author is the best available contact for scope decisions). The author
sees the DQ, agrees with the DEV team, and adjusts the ticket; the re-import
diff picks that adjustment up as the resolution.

### Two Modes, Not A Loose Fallback

- **Mode 1 (MCP configured):** automated pre-sync diff + marker derived from
  the successful send; the ticket comment is the truth, the proposal marker is
  the memory, corrected from the diff.
- **Mode 2 (no MCP):** fully manual. The user writes the comment themselves,
  and no automated sync is possible. Tell the user explicitly that no automated
  sync can occur in this mode; offer the ready-to-paste text.

### Guided Send

Never write to the ticket autonomously. The send is guided:

1. After Grill-Me, collect the still-open questions (those with a `[FQx]` /
   `[DQx]` handle and an unticked box).
2. Summarize them for the user and state clearly that they will be uploaded as
   a Jira comment.
3. Require explicit user confirmation before any MCP write.
4. Only after confirmation, send.

### Pre-Sync Diff (Mode 1)

Before writing, fetch the ticket's existing comments — call `jira_get_issue` again with a `comment_limit` large enough to surface all comments — and diff them against
`## Decision Questions` / `## Open Questions`. Decide each question, never guessing:

| Proposal has | Ticket has | Decision |
|---|---|---|
| FQ/DQ, not sent | nothing | **send** |
| FQ/DQ sent, same target | FQ/DQ, same target | **skip** (already sent), confirm marker |
| FQ, AC=X | FQ, AC=Y | **correct** the AC mapping (no re-send) |
| DQ, communicated | answer in ticket/comment | **fold in + tick, set resolved** (latch) |
| — | FQ/DQ duplicated | **ask the user** |
| marker=communicated | FQ/DQ absent | **notify + ask the user** (inconsistency) |
| — | free text, no FQ/DQ | **ask the user** (could be manual/foreign) |
| — | FQ/DQ present (orphan) | **report**, do not send |

Only the first four states are unambiguous and auto-decided; the rest stop and
ask the user. This enforces "never duplicate" and "ask before a clash".

### Pro-Gap Checkpoint

Send each open question by calling the **`jira_add_comment`** MCP tool with the ticket key and the question body — one `jira_add_comment` call per question (1:1), and mark it atomically on success
(set the `→ communicated to Jira` marker with the comment link/date). A failed
send gets no marker and joins a retry set; successful ones keep their marker.
No partial-batch corruption.

### Fallback To Manual

If MCP is not configured, or a send fails in Mode 1, fall back to Mode 2: give
the user the ready-to-paste comment text and ask them to write it to the ticket
themselves. Do not set the marker yourself as "sent" unless the user confirms
they actually wrote it to Jira.

### Write-Back: Locally Answered DQ/FQ → Jira

The export above handles still-open questions. Separately, when a DQ or FQ is
answered **locally** — the agent asks the question in conversation and the
user answers it, ticking the box as resolved — that resolved answer is also
written back to the ticket as a comment. This is additive to, and never
replaces, the still-open-question export.

**One comment per resolved question.** Each locally-answered DQ/FQ is written
back as its own comment carrying the same stable `[DQx]` / `[FQx]` handle it
already uses in the proposal. The handle is the deterministic anchor for the
pre-sync diff, so a resolved question already written back is never written
twice.

**Same guided-send guarantees.** The write-back reuses the existing outbound
path with all its guardrails:

1. Require explicit user confirmation before any write (never autonomous).
2. Run the pre-sync diff keyed on the handle; skip a question already sent.
3. Without Jira access, fall back to Mode 2 — hand the user ready-to-paste text
   and make clear no automated sync can occur.

**Comment format** — distinct from the still-open-question format, adding a
resolve marker and the answer. This keeps the two comment kinds unambiguous:

```
Still-open comment:  [FQx] · <gap>                              (question asked)
Write-back comment:  [FQx] RESOLVED (<date>) · <gap> → <answer> (question answered)
```

A question answered through the ticket (folded in by a re-import) is not
written back — it would be redundant; the write-back is only for questions that
were resolved here, in the conversation.
