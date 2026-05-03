# Session Handoff: TASK-0034 Implemented — Awaiting Smoke Test and Deploy (app-1)

## Session Date

2026-04-30

## Goal

Update the control layer to reflect that TASK-0034 (mandatory Czech safety disclaimer beneath
dose-modification recommendations in Diabetický poradce 2) has been fully implemented and
tested locally in the `medical_advisor` repo. The task is `done` and awaiting a manual smoke
test followed by deployment to Azure.

## What Was Learned

- **Server-side enforcement was chosen over prompt-only.** The implementation appends the
  verbatim Czech disclaimer at the rendering layer (`ChatMessageBubble.razor`) conditioned on
  `AdvisorId == "diabetes-2"` and a dose-flag, rather than relying on the LLM to include it.
  This makes the disclaimer model-failure-proof.
- **No spec was written.** The open questions from triage (trigger definition, prompt-only vs.
  server-side, localization policy) were resolved directly during implementation. The chosen
  answers: server-side enforcement; advisor gate = `diabetes-2` only; always Czech regardless
  of user language (regulatory requirement).
- **Verbatim Czech phrasing preserved.** "na rozdíl o vašeho lékaře" was not corrected — the
  original text was shipped as specified.
- **Backward compatible.** The short legacy warning is retained for the other 4 advisors.
  No system prompt changes were needed.
- **Build and test results are clean.** 0 errors, 0 warnings; 104 tests passed (96 existing +
  10 new). The 10 new tests cover `AdvisorId` property behaviour (2) and the full disclaimer
  helper logic including Czech phrasing (8).
- **No CI/CD.** Deployment to `medical-advisor-cz` is a manual `az webapp deploy` ZIP step
  controlled by the user. An 8-point smoke test plan was documented during implementation.

## Files Reviewed

Control layer:

- `/Users/ivananikin/Documents/Knowledge.Healthcare/AGENTS.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/current-priorities.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/dashboards/task-board.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/tasks/triage/TASK-0034.md`
- `/Users/ivananikin/Documents/Knowledge.Healthcare/handoffs/handoff-template.md`

## Files Changed

Control layer:

- `tasks/done/TASK-0034.md` — **NEW** (moved from `tasks/triage/`). Status updated to `done`;
  full implementation details, files changed, build/test results, and deployment-pending note
  added.
- `dashboards/task-board.md` — TASK-0034 removed from **Triaged** section; added to **Done**
  section with implementation summary, build/test results, and deployment-pending note.
- `current-priorities.md` — Updated active goal for TASK-0034 from "triaged, needs-spec" to
  "implemented and tested locally, awaiting deploy". Updated recommended next action #1 from
  "spec TASK-0034" to "deploy TASK-0034". Added implementation entry to the App-1 follow-ups
  log.
- `handoffs/2026-04-30-task-0034-implemented.md` — this note.

app-1 repo (`/Users/ivananikin/Documents/medical_advisor`) — changes made by the Build agent,
not this session:

- `ChatMessage.cs` — Added `string? AdvisorId` property.
- `MedicalAdvisorService.cs` — Populates `streamingMessage.AdvisorId = advisorId;` at line 150.
- `DoseWarningHelpers.cs` — **NEW** static helper class: `GetDiabetes2DisclaimerText()` and
  `GetShortDoseWarningText()`.
- `ChatMessageBubble.razor` — Conditional rendering: diabetes-2 + dose flag → long Czech
  disclaimer; otherwise → short legacy warning.
- `ChatMessageTests.cs` — 2 new tests for `AdvisorId` property.
- `DoseWarningHelpersTests.cs` — **NEW** 8 unit tests validating disclaimer logic and Czech
  phrasing.

## Decisions Made

- **Server-side enforcement chosen.** The disclaimer is appended deterministically at the
  rendering layer, not via a system-prompt instruction. This resolves the key open question
  from triage (prompt-only vs. server-side) in favour of the safer, model-failure-proof option.
- **Always Czech.** The disclaimer is always rendered in Czech regardless of the user's
  conversation language. This was confirmed as the regulatory requirement.
- **Verbatim text shipped as specified.** "na rozdíl o vašeho lékaře" was not corrected.
- **No spec written.** The open questions were resolved directly during implementation. The
  implementation record in `tasks/done/TASK-0034.md` serves as the durable decision record.

## Assumptions

- The 8-point manual smoke test plan documented during implementation covers the acceptance
  criteria adequately. (needs verification: yes — user must execute the smoke test before deploy)
- The `az webapp deploy` ZIP deploy to `medical-advisor-cz` is the correct deployment method
  (consistent with prior notes in `tasks/triage/TASK-0034.md` and `app-1-overview.md`).
  (needs verification: no — confirmed in triage notes)

## Unresolved Questions

- **Smoke test not yet run.** The 8-point manual smoke test plan was documented but not
  executed. It must be run before deployment.
- **Not deployed.** The implementation is local only. Azure `medical-advisor-cz` still runs
  the pre-disclaimer version.
- **Other advisors scope.** Whether `gestational-diabetes`, `insulin-pump`, or `insulin-pump-2`
  should eventually receive a similar disclaimer for any dose-related recommendations they may
  emit was not resolved. Deferred — not blocking TASK-0034 deployment.

## Recommended Next Step

1. **Run the 8-point manual smoke test** against the local `medical_advisor` build. Confirm
   the verbatim Czech disclaimer appears beneath dose-modification recommendations in
   Diabetický poradce 2, does not appear for other advisors, and does not break quick-reply
   rendering or streaming.
2. **Deploy to Azure** — `az webapp deploy` (ZIP) to `medical-advisor-cz` once the smoke test
   passes. Verify the disclaimer is live on `https://medical-advisor-cz.azurewebsites.net`.
3. **Update the control layer** after successful deployment: move TASK-0034 from `done` to
   `deployed` in `tasks/done/TASK-0034.md` and `dashboards/task-board.md`; update
   `current-priorities.md`.
