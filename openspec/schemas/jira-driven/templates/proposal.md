## Source

<!-- Jira ticket this change originates from. Populate verbatim via the
     jira-import skill before drafting the rest of this proposal. -->

- **Ticket:** <!-- TICKET-ID -->
- **Summary:** <!-- verbatim Jira Summary field -->
- **Description:** <!-- verbatim Jira Description field, or a link if too long to inline -->
- **Acceptance Criteria:**
  1. <!-- verbatim AC line 1 -->
  2. <!-- verbatim AC line 2 -->

## Why

<!-- Explain the motivation for this change. What problem does this solve? Why now? -->

## What Changes

<!-- Describe what will change. Be specific about new capabilities, modifications, or removals. -->

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md with OpenSpec delta headers and Gherkin-style scenarios. -->
- `<name>`: <brief description of what this capability covers>

### Modified Capabilities
<!-- Existing capabilities whose behaviour is changing (not just implementation).
     Only list here if spec-level behaviour changes. Each needs a delta spec.md file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `<existing-name>`: <what behaviour is changing>

## Impact

<!-- Affected code, APIs, dependencies, systems -->

## Decision Questions

<!-- While decision questions are pending, set the status marker and stop the
     workflow:

     **Status:** awaiting-answers (TICKET-ID · N/M answered ·
                 since YYYY-MM-DD · comment sent to Jira)

     Remove or clear this marker only after the re-import has folded in the
     answers and ticked the boxes. -->

<!-- After the Grill-Me Phase 0 review: record every fundamental / scope
     decision gap as a checkbox. Format per still-open decision question:
       - [ ] [DQx] · <decision question>
             Decision: <team decision / documented assumption>  (on resolution)
             Status: awaiting-answers | resolved
             Reason: <why this blocks AC interpretation>
             → communicated to Jira: <date/comment link>  (only if done)
     DQs use their own monotonic numbering ([DQ1], [DQ2], ...), separate from
     [FQx] and [ACx]. A DQ stays a DQ - it is never promoted to an AC and
     carries no AC contract. Resolve DQs before generating any FQs.

     State machine (one-way):
       awaiting-answers -> resolved   (PO answer in ticket, or team decision
                                        with a 'Decision:' note)
       resolved         -> resolved   (a later re-import NEVER flips back)
       awaiting-answers -> awaiting-answers (re-import with unchanged ticket)

     Unified export format (shared with the Jira comment): the Jira comment
     header derives from the same proposal line, minus the checkbox prefix:
       Proposal line:  - [ ] [DQx] · <decision question>
       Jira comment:   [DQx] · <decision question>
     DQ comments target the ticket author (PO/ReqEng). One deterministic
     anchor ([DQx]) used by the export pre-sync, so a question already sent
     is never sent twice. -->

## Open Questions

<!-- While open questions are pending, set the status marker and stop the
     workflow (see ## Decision Questions for the shared status marker). -->

<!-- After the Grill-Me Phase 1 review: record every unresolved AC gap as a
     checkbox. Format per still-open gap:
       - [ ] <AC reference> — [FQx] · <gap>
             Recommendation: <Grill-Me recommendation>
             Reason: <why the gap blocks>
             → communicated to Jira: <date/comment link>  (only if done)
     The [FQx] handle is the question's stable process identity, assigned at
     Grill-Me time: never renamed, independent of block position and AC
     numbering (and of the AC freeze). Resolved gaps carry no [FQx] handle,
     and each new question gets the next monotonic number.
     A box is ticked ([x]) only after the Jira answer has been folded in
     (e.g. new/changed AC in the ticket or in ## Source).
     The open boxes are the backlog: N open, M communicated with date.

     Unified export format (shared with the Jira comment): the Jira comment
     header derives from the same proposal line, minus the checkbox prefix:
       Proposal line:  - [ ] <AC> — [FQx] · <gap>
       Jira comment:   <AC> — [FQx] · <gap>
     One deterministic anchor ([FQx]) used by the export pre-sync, so a
     question already sent is never sent twice. -->
