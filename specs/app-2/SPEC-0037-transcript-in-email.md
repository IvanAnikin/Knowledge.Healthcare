# Technical Spec: Include transcript alongside report in outgoing email

## Metadata

- **Task ID:** TASK-0037
- **Author:** @spec-writer
- **Date:** 2026-05-02
- **App(s):** app-2 (ANOTE_mobile — backend + mobile client)
- **Status:** approved (all open questions resolved 2026-05-02)
- **Spec type:** lightweight technical spec (single app, additive change, low risk, confidence high after repo investigation)

## Summary

Extend the optional SMTP email pathway in ANOTE_mobile so that a single outgoing email contains the dictation transcript first and the generated medical report directly beneath it. The change is additive: a new optional `transcript` field on the `/send-report-email` request, body assembly updated to include a Czech-labelled transcript section above the existing report section, and the Flutter client updated to pass `state.transcript` alongside the report. SMTP gating, plain-text formatting, and existing failure modes are preserved.

## Objective

A single email sent via `/send-report-email` contains, in order: a Czech transcript section, then the existing Czech report section, in the same plain-text body. The recipient (the doctor who configured their own address) can review source dictation and structured report side-by-side without leaving the inbox.

## Scope

- Backend: extend `SendReportEmailRequest` Pydantic model with an optional `transcript: str = ""` field; update body assembly in `send_report_email` to render a `Přepis` section above the existing `Lékařská zpráva` section when transcript is non-empty; preserve subject, headers, and SMTP gating.
- Mobile: pass `state.transcript` (or `session.transcript`) to `ReportService.sendReportEmail` from all three existing call sites (`_sendEmailIfEnabled`, `sendReportEmailNow`, and the manual button path in `home_screen._sendEmail`).
- Tests: update `backend/tests/test_email_endpoint.py` to (a) keep all existing cases green (since `transcript` is optional), and (b) add at least one assertion-level test that validates body composition when transcript is supplied. Because the existing tests are integration-style (live `httpx` against `localhost:8111`), add a new pure-unit body-composition test that does not require a running server (see Validation).

## Non-Goals

- No PDF generation. No HTML email body. No multipart MIME / attachments.
- No change to `/report`, `/scenarios`, `/health`, or `/test-report/{scenario_name}`.
- No change to SMTP gating, TLS handling, or auth.
- No size-based switch from inline to attachment in this iteration (see Open Questions §1).
- No change to mobile UI strings, settings screen, history, or recording storage.
- No change to GDPR posture: transcript already crosses the backend boundary via `/report` today; this change does not expand the data path beyond the existing user-configured SMTP recipient.

## Current Behavior

Confirmed from repo inspection (2026-05-02):

- `backend/main.py:529-534` — `SendReportEmailRequest` carries `report`, `email`, `visit_type` only. **No transcript field exists today.**
- `backend/main.py:629-665` — `/send-report-email` builds a plain-text body with header (`Lékařská zpráva vygenerovaná aplikací ANOTE`, date, visit-type label), `---` separator, the report, another `---`, and a footer disclaimer. Subject: `ANOTE – Lékařská zpráva – {today}`.
- `backend/main.py:537-557` — `_send_email` uses `MIMEText(body, "plain", "utf-8")`, raises `RuntimeError("Email not configured on server")` when `SMTP_HOST` is unset (caller maps this to HTTP 502). TLS path via `SMTP_USE_TLS` exists.
- `backend/tests/test_email_endpoint.py` — five integration tests against a running backend on `localhost:8111` (health, no-SMTP, empty report, invalid email, no-auth, wrong-token). No body-composition assertions today.
- `mobile/lib/services/report_service.dart:107-129` — `sendReportEmail({report, email, visitType})` POSTs `{report, email, visit_type}`. **No transcript in payload today.**
- `mobile/lib/providers/session_provider.dart:1368-1403` — `_sendEmailIfEnabled` and `sendReportEmailNow` both have `state.transcript` in scope (the `SessionState` carries `transcript`).
- `mobile/lib/screens/home_screen.dart:57-101` — manual "Send" button calls `sendReportEmailNow(report: session.report)`. `session.transcript` is in scope on the same object.
- Email is therefore a single plain-text inline body today. Recipient sees only the structured report.

## Proposed Behavior

A single plain-text email with the following body (Czech, UTF-8), sent only when `SMTP_HOST` is configured and the request is otherwise valid:

```
Lékařská zpráva vygenerovaná aplikací ANOTE
Datum: {today}
Typ návštěvy: {vt_label}

--- Přepis ---

{transcript}

--- Lékařská zpráva ---

{report}

---
Tato zpráva byla automaticky odesláná aplikací ANOTE.
```

Behavior rules:

1. If `transcript` is empty/missing in the request, fall back to the **current** body verbatim (the `Přepis` section is omitted entirely, including its heading and separator). This preserves backwards compatibility for any caller that has not yet been updated.
2. If `transcript` is present and non-empty (after `.strip()`), render the `Přepis` section above the existing report section, using the heading style shown above (delimiter pattern `--- {heading} ---` reuses the existing `---` separator vocabulary already in the email).
3. Subject line is unchanged.
4. SMTP gating, TLS, auth, and 400/401/502 error paths are unchanged.
5. Mobile client always passes `transcript` when available (even if empty string, send empty string — semantics equivalent to omission per the optional default).

### Resolved decisions (with repo evidence)

| # | Decision | Resolution | Evidence |
|---|----------|------------|----------|
| 1 | Inline vs. attachment vs. mixed | **Inline, plain-text, both sections in body.** No multipart, no attachment plumbing exists today; adding it would expand scope significantly. | `backend/main.py:542` uses `MIMEText(body, "plain", "utf-8")`. |
| 2 | Size threshold for inline→attachment | **None — confirmed by user 2026-05-02.** v1 keeps everything inline regardless of transcript length. No size cap, no attachment fallback path. If mail-client truncation is ever observed in production, it will be handled as a separate future task; this spec deliberately does not introduce that complexity. | Pilot scope per `applications/app-2-overview.md:18-24`; user decision 2026-05-02. |
| 2b | `SendReportEmailRequest` `extra` policy | **Unchanged — confirmed by user 2026-05-02.** The model keeps Pydantic's permissive default (no `extra="forbid"`). This is the smallest diff and preserves the additive backwards-compatibility property. Out of scope for this task. | `backend/main.py:529-534` (no `model_config` set today); user decision 2026-05-02. |
| 4b | Heading wording | **Confirmed by user 2026-05-02.** Use exactly `--- Přepis ---` and `--- Lékařská zpráva ---`. No alternates. | User decision 2026-05-02. |
| 3 | Mobile→backend payload contract | **Additive optional field `transcript: str = ""`** on `SendReportEmailRequest`. UTF-8 JSON (already the encoding). Field name matches `/report` convention. | `backend/main.py:521-526` (`ReportRequest.transcript: str`); `report_service.dart:107-129`. |
| 4 | Czech section headings + separator | **Headings `Přepis` and `Lékařská zpráva`**, both rendered as `--- {heading} ---` lines. Reuses existing `---` separator vocabulary already in the body. The terms `Přepis` / `Zpráva` are the same vocabulary used in mobile UI strings. | `backend/main.py:646-655` (existing `---` style); `home_screen.dart:110` (`Přepis zkopírován` / `Zpráva zkopírována`). |
| 5 | PHI / GDPR framing | **No change to data-flow posture.** Transcript already crosses the backend boundary today via `/report`. The optional SMTP path is gated by `SMTP_HOST`, recipient is user-configured, and backend deliberately does not log transcript or report content. The change adds the transcript to a body that is already destined for the same user-configured recipient. Document this explicitly in the rollout note; flag that SMTP transport security (`SMTP_USE_TLS`) and recipient hygiene remain the operator's responsibility, unchanged by this spec. | `applications/app-2-overview.md:139-154`; `backend/main.py:680-681`, `547-557`. |

## Likely Files Affected

| App | File / Module | Change Type |
|-----|---------------|-------------|
| app-2 backend | `backend/main.py` (`SendReportEmailRequest`, `send_report_email`) | modify |
| app-2 backend | `backend/tests/test_email_endpoint.py` | modify (add at least one body-composition test; ensure existing pass) |
| app-2 mobile | `mobile/lib/services/report_service.dart` (`sendReportEmail`) | modify (add `transcript` parameter, pass in JSON) |
| app-2 mobile | `mobile/lib/providers/session_provider.dart` (`_sendEmailIfEnabled`, `sendReportEmailNow`) | modify (pass `state.transcript`) |
| app-2 mobile (caller) | `mobile/lib/screens/home_screen.dart` (`_sendEmail`) | modify only if `sendReportEmailNow` signature requires transcript explicitly; can otherwise be left unchanged because the notifier has `state.transcript` in scope |

Total: 4 files touched in the change path, plus optionally the screen call site. The mobile screen does **not** need to know about the transcript if `sendReportEmailNow` reads it from state internally — recommended approach to keep the UI layer unchanged.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Mobile clients on older builds keep sending no `transcript` field after backend deploys | medium | New backend field is **optional with `""` default**; the Přepis section is omitted when empty, so old clients see today's exact behavior. |
| Very long transcripts cause some mail providers to truncate the body | low–medium | Accepted residual risk per user decision 2026-05-02 (no size cap, no attachment fallback in v1). Pilot use is short dictations. If truncation is observed in production, address as a separate future task. |
| Operator forgets that transcript now also leaves via SMTP and chooses a non-TLS SMTP host | low | Behavior identical in principle to today — transcript already leaves the device via HTTPS to `/report`. Call this out in `Rollout Notes`; no code change can prevent operator misconfiguration. |
| Test suite regression because `test_email_endpoint.py` is integration-style and requires a running server | low | New body-composition test should be a pure-unit test that calls a small extracted helper (or imports `send_report_email`'s body builder). Existing live tests remain unchanged. |
| Czech encoding regressions in headings (`Přepis`, `Lékařská zpráva`) | low | Body is already UTF-8 (`MIMEText(body, "plain", "utf-8")`); existing body uses Czech characters via `\u00xx` escapes — keep the same convention. |

## Validation

### Acceptance criteria (mirrors task)

- AC1: A **single** email is sent (not two messages). Subject unchanged.
- AC2: When the request includes a non-empty `transcript`, the assembled email body contains, in this order: the **transcript first** under heading `--- Přepis ---`, then the **report below** under heading `--- Lékařská zpráva ---`. Both sections are **inline plain-text** in the same body — no attachments, no HTML, no multipart MIME.
- AC3: When the request omits `transcript` or sends `""`, the assembled body equals today's body byte-for-byte (no Přepis heading, no extra blank lines).
- AC4: Everything is delivered inline regardless of transcript length — no size threshold, no attachment fallback path is introduced in this task.
- AC5: SMTP gating, TLS, 400 (empty report / invalid email), 401 (auth), and 502 (`Email not configured`) paths are unchanged.
- AC6: `SendReportEmailRequest` retains Pydantic's permissive default for unknown fields (no `extra="forbid"` introduced in this task).
- AC7: All existing tests in `test_email_endpoint.py` pass without modification (or with only payload-shape additions that remain valid).
- AC8: A new body-composition test asserts AC2 and AC3.
- AC9: Manual end-to-end send (with `SMTP_HOST` configured) produces a received email matching the layout above with the exact headings `--- Přepis ---` and `--- Lékařská zpráva ---`.

### Test strategy

- **Unit (new):** Refactor body assembly into a small pure function (e.g., `_build_email_body(report, transcript, today, vt_label) -> str`) and assert composition for two cases: with transcript and without. This avoids needing a running server and is the cleanest delta to `test_email_endpoint.py`.
- **Integration (existing):** Re-run the five live tests in `test_email_endpoint.py` against `localhost:8111` to confirm no regressions on auth / validation paths.
- **Mobile:** Update `mobile/test/services/report_service_test.dart` (existence noted in `app-2-overview.md:185`) so the mocked HTTP call asserts the request payload now contains a `transcript` key.
- **End-to-end manual:** With `SMTP_HOST` configured to a developer mailbox, run a real recording session and confirm the received email matches the proposed body layout.

## Rollout Notes

- Backwards compatibility is preserved by the optional default — backend can be deployed before mobile without breaking existing clients, and a stale mobile build will continue to send report-only emails.
- No feature flag required; the behavior is data-driven (presence of `transcript` in the request).
- No migration; no persisted data is touched.
- Re-state the GDPR posture in the deploy note: the SMTP path remains opt-in (`SMTP_HOST`), recipient is user-configured in the mobile settings screen, and backend logging is unchanged (transcript and report content are not logged — `backend/main.py:680-681`).

## Rollback Considerations

- Single revert of the backend change restores previous body assembly. No schema migrations to undo.
- Mobile rollback is independent: a mobile client that keeps sending `transcript` to a rolled-back backend is harmless because `SendReportEmailRequest` retains Pydantic's permissive default (per AC6) — extra fields are ignored. This task explicitly does **not** introduce `extra="forbid"`.

## Open Questions

None — all decisions resolved (user, 2026-05-02). See the *Resolved decisions* table above (rows 2, 2b, 4b) for the locked-in answers.

---

## Implementation Plan (embedded — lightweight)

### Sequencing

Backend first (additive, backwards-compatible), then mobile, then tests. Each step is independently revertable.

### Steps

#### Step 1 — Backend: extend request model and body assembly

- **What:** Add `transcript: str = ""` to `SendReportEmailRequest`. Extract a `_build_email_body(...)` helper. Render `--- Přepis ---` section only when `transcript.strip()` is non-empty; render `--- Lékařská zpráva ---` heading above the report section unconditionally (small layout improvement, justifiable as part of the same change because the report previously had no explicit heading, only the leading `---` separator).
- **Where:** `backend/main.py` (lines ~529-534 model; ~629-665 endpoint; new helper near `_send_email`).
- **Validation:** New unit test `test_build_email_body_with_transcript` and `test_build_email_body_without_transcript` in `test_email_endpoint.py` (or a new `test_email_body.py`).
- **Rollback:** Revert this commit; schema and body return to today's shape.

#### Step 2 — Mobile: pass transcript in payload

- **What:** Add `String transcript = ''` parameter to `ReportService.sendReportEmail`; include `'transcript': transcript` in the POST body. Update `_sendEmailIfEnabled` and `sendReportEmailNow` to read `state.transcript` and pass it through. Leave `home_screen._sendEmail` unchanged (it does not need to know about transcript; the notifier reads from `state`).
- **Where:** `mobile/lib/services/report_service.dart`, `mobile/lib/providers/session_provider.dart`.
- **Validation:** Update `mobile/test/services/report_service_test.dart` to assert the outgoing payload includes the `transcript` key.
- **Rollback:** Revert this commit; mobile reverts to report-only payload, which the new backend tolerates.

#### Step 3 — Test coverage and manual verification

- **What:** Run `python -m pytest backend/tests/test_email_endpoint.py -v` against a running local backend; run `flutter test` for mobile unit tests; perform one real end-to-end send with `SMTP_HOST` configured.
- **Where:** Local dev environment.
- **Validation:** All seven acceptance criteria above.
- **Rollback:** Not applicable (verification only).

### Checkpoints

| After Step | Check | Pass Criteria |
|-----------|-------|---------------|
| 1 | Backend unit tests | New body-composition tests pass; existing five live tests still pass when run against local server. |
| 2 | Mobile unit tests | `report_service_test` asserts new payload field; no other mobile tests regress. |
| 3 | End-to-end manual | Received email matches the layout in *Proposed Behavior*. |

### Final Validation

A real recording → report → email round trip with `SMTP_HOST` configured produces a single received email whose body contains, in order: header block, `--- Přepis ---`, transcript text, `--- Lékařská zpráva ---`, report text, footer disclaimer.

### Rollback Plan

Revert backend commit (Step 1) and mobile commit (Step 2) independently. No data migrations to undo. Existing five live tests provide the safety net for the auth / validation paths.
