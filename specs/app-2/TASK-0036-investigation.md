# TASK-0036 — Report Quality / Prompt Engineering — Investigation

**Repository:** `ANOTE_mobile` (`/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile`)
**Mode:** investigation only — no source code modified
**Date:** 2 May 2026
**Author:** Copilot (automated investigation)

---

## 0. Defects in scope

The 5 confirmed defects from doctor feedback (Dr. Jan Brož, 6 sessions):

| # | Defect | Sample evidence |
|---|--------|-----------------|
| 1 | Irrelevant/social content placed in clinical sections (esp. NO) | Hurvínek transcripts: songs/rhymes leak into reports; reports include theater banter as NO content |
| 2 | Physical exam findings put in subjective sections | Reports place patient‑stated TT/BP under NO instead of `Objektivní nález`; or move objective findings into NO |
| 3 | Allergy hallucination: "JAR" → "jara" → false pollen allergy | **Not present in any committed fixture** — anecdotal report from doctor (see §5) |
| 4 | Boilerplate cooperation note: "Spolupráce dobrá." added to every report | feedback6.txt report ends with "Spolupráce dobrá, abstinenci od alkoholu dodržuje, bere předepsanou medikaci." |
| 5 | Medication dosage paraphrased / lost: "1 tbl." → "pacientka užívá předepsanou medikaci pravidelně" | feedback4 / feedback6 transcripts contain "jednu tabletu ráno" — sometimes preserved, sometimes paraphrased |

---

## 1. Report generation pipeline

### 1.1 Endpoint

- File: [backend/main.py](../../../Ivanek-Anakin/ANOTE_mobile/backend/main.py)
- `POST /report` defined at line ~640 (`generate_report`); auxiliary `POST /test-report/{scenario_name}` at ~552.
- Request schema: `ReportRequest { transcript: str, language="cs", visit_type="default" }`.
- Auth: bearer token compared exact‑equal to `APP_API_TOKEN` env var.
- `visit_type` validated against `{default, initial, followup, gastroscopy, colonoscopy, ultrasound}`; unknown → falls back to `default`.

### 1.2 LLM call

```python
messages = [
    {"role": "system", "content": _build_system_prompt(today, visit_type)},
    {"role": "user",
     "content": "Převeď tento přepis do strukturované lékařské zprávy"
                f" v češtině:\n\n{transcript}"},
]
response = client.chat.completions.create(
    model=model,                # CHAT_MODEL = AZURE_OPENAI_DEPLOYMENT (prod: gpt-5-mini)
    messages=messages,
    max_completion_tokens=4096,
    timeout=60.0,
)
report = response.choices[0].message.content or ""
```

- Model selection: `AZURE_OPENAI_DEPLOYMENT` env var; fallback `AZURE_OPENAI_FALLBACK_DEPLOYMENT` (default `gpt-5-nano`).
- **No `temperature` is set** (gpt‑5‑mini is a reasoning model — temperature is unsupported / fixed). `evaluate_reports.py` confirms this with `_is_reasoning_model()`.
- **No post‑processing** of the LLM output — the model's text is returned verbatim. (No regex cleanup, no validators, no guardrails.)
- Transcript is GDPR‑logged out: only `visit_type` is logged.

### 1.3 System prompt structure

Built by `_build_system_prompt(today, visit_type)` at [backend/main.py L466](../../../Ivanek-Anakin/ANOTE_mobile/backend/main.py#L466). It concatenates:

1. `intro` — one sentence ("Jsi asistent pro tvorbu lékařské dokumentace…").
2. `_build_base_rules()` — the **ZÁSADY** block (~30 bullets shared by all visit types).
3. `_build_sections_<visit_type>(today)` — section template (13 sections for `initial`/`default`; compact for `followup`; procedure templates for gastro/colo/UZ).
4. `footer` — "JAZYK / Celý výstup musí být v češtině…".

Key rules already present in `_build_base_rules()` that target the 5 defects (some directly, some only partially):

- **Defect 1 (irrelevant content)** — partial: "Přepis může obsahovat chyby z automatického rozpoznávání řeči — interpretuj smysl, ne doslovný text." Nothing explicit about songs / rhymes / off‑topic chatter.
- **Defect 2 (subj vs obj)** — present: "Rozlišuj subjektivní údaje (udává pacient) vs objektivní nález (naměřeno / zjištěno vyšetřením). Co je jen udávané, nepiš jako objektivní." `Objektivní nález` section also says: "Pokud pacient jen udává, že nemá horečku: nepiš jako objektivní TT, ale dej do NO jako 'zvýšenou teplotu neguje'."
- **Defect 3 (allergy)** — present: "Rozlišuj ALERGII… a INTOLERANCI… V AA uváděj pouze alergie." Nothing about brand‑name false positives or "JAR".
- **Defect 4 (cooperation boilerplate)** — actively *encouraged*: the `Adherence a spolupráce pacienta` section literally says `'- Pokud je spolupráce dobrá: "spolupráce dobrá" / "režim dodržuje".'` This is the source of the boilerplate.
- **Defect 5 (dosage preservation)** — present: "Zachovej přesná čísla, jednotky, dávkování a frekvenci (mg, ml, 1‑0‑1, 2× denně, týdny…)." But the rule is general — it does not forbid paraphrasing dosage into prose.

Full prompt text (shared rules block) is reproduced verbatim in `evaluate_reports.py` lines 47‑85.

---

## 2. Transcript fixtures inventory

Three fixture sets exist:

| Path | Type | Source quality | Suitable for issues |
|------|------|----------------|---------------------|
| `mobile/assets/demo_scenarios/cz_kardialni_nahoda.txt` | Synthetic CZ ER scenario, 172 w | Clean, scripted | Limited — clean text, no ASR noise |
| `mobile/assets/demo_scenarios/cz_respiracni_infekce.txt` | Synthetic CZ resp. infection, 196 w | Clean | Limited |
| `mobile/assets/demo_scenarios/cz_otrava_jidlem.txt` | Synthetic CZ food poisoning, 198 w | Clean | Limited |
| `mobile/assets/demo_scenarios/cz_detska_prohlidka.txt` | Synthetic CZ pediatric checkup, 200 w | Clean | Limited |
| `mobile/assets/demo_scenarios/{cardiac_emergency,food_poisoning,pediatric_checkup,respiratory_infection}.txt` | Synthetic English versions | Clean | Not applicable (Czech‑only prompt) |
| `test_scenarios/cz_*.txt` | Identical to the 4 cz scenarios above | Clean | Same as above |
| `testing_hurvinek/S Hurvínkem … 1 Nachlazení.txt` | Real ASR transcript of Czech children's audio drama, 1090 w | Heavy noise — songs, rhymes, banter, multiple speakers | **Defect 1** (irrelevant content), **Defect 2** (subjective vs objective drift) |
| `testing_hurvinek/… 2 Zlomenina.txt` | Same source, 985 w | Heavy noise | Defect 1, 2 |
| `testing_hurvinek/… 08 Angína.txt` | Same source, 1128 w | Heavy noise | Defect 1, 2 |
| `feedback_janbroz/feedback{1..6}.txt` | Real session transcripts + LLM reports + doctor's annotations | Real ASR errors, real reports | Defect 4 (feedback6 shows the boilerplate), Defect 5 (feedback6 has "jednu tabletu ráno"), Defect 2 (multiple) — these are **artifacts/observations**, not inputs |

### Fixture suitability per defect

| Defect | Fixture(s) covering it | Gap |
|--------|-----------------------|-----|
| 1 — irrelevant content | testing_hurvinek/* (perfect — songs + medical content mixed) | None; but no Czech medical scenario where doctor‑patient banter (weather, family chit‑chat) precedes clinical Q&A |
| 2 — exam findings in subjective | testing_hurvinek/* (objective findings spoken inline) | No purpose‑built fixture where a doctor says "TK 140/90, P 78" amidst patient narration |
| 3 — JAR → pollen allergy | **None** | Need a synthetic transcript that explicitly contains "JAR" (dish soap brand) in an allergy context — not present in repo |
| 4 — "Spolupráce dobrá" boilerplate | feedback6.txt shows the *output*, but no input‑level fixture forces the bug | Need a fixture where the patient does NOT discuss adherence at all → assert "Spolupráce dobrá" must NOT appear |
| 5 — "1 tbl." → paraphrase | feedback6 transcript contains "jednu tabletu ráno"; the report happens to preserve it. We have no fixture where a doctor utters the literal abbreviation "tbl." | Need a fixture where the doctor literally dictates "1 tbl. ráno" or similar terse dosing |

---

## 3. Existing test inventory

All in `backend/tests/`:

| File | Type | Tests | What is asserted | Gaps for our 5 issues |
|------|------|-------|-------------------|------------------------|
| `test_prompt_builder.py` | Pure unit (no API) | 18 tests | Static prompt construction: section names, `TODAY` injection, `ZÁSADY` header, "neuvedeno" rule, negation examples, ASR rule, subjective/objective rule, visit‑type routing, language footer | Does **not** assert any rule for issues 1, 3, 4, 5; loosely covers issue 2 |
| `test_report_endpoint.py` | FastAPI TestClient + mocked OpenAI | 7 tests | Auth, 200/400/401/422/502 status codes, basic response shape | None of the 5 issues — content is mocked |
| `test_endpoints_comprehensive.py` | TestClient + mocks | ~17 tests | Visit‑type routing, scenario listing, very long transcripts, Unicode, GDPR (no transcript echo in errors), bearer header strictness | None of the 5 issues |
| `test_email_endpoint.py` | TestClient + mocked SMTP | ~6 tests | `/send-report-email` validation, SMTP path | Out of scope |
| `test_report_quality.py` | **LIVE** call against Azure backend (`ANOTE_API_URL`) | ~17 tests over 5 classes | Required sections present, basic factual recall (age/BP/HR/medication for cardiac scenario), `neuvedeno` count ≥ 3, negation phrases present, performance < 120 s, all `cz_*.txt` scenarios produce valid report | **No tests for** issues 1, 3, 4 (boilerplate), 5 (literal dosage). Negation tests use `_has_negation_language()` which only checks for *presence*, not *appropriateness* |
| `test_transcription_quality.py` | Live (whisper, not report) | — | WER on transcription | Out of scope (transcription, not report) |

**Net assessment:** The test suite covers structural correctness and a handful of factual recall checks, but has **no targeted regression assertions for any of the 5 prompt defects**. Adding them is the central output of this investigation.

---

## 4. LLM‑as‑Judge layer

### Status: **EXISTS** and is implemented.

- Spec: [LLM_JUDGE_SPEC.md](../../../Ivanek-Anakin/ANOTE_mobile/LLM_JUDGE_SPEC.md) — implementation status "Implemented & Tested".
- Implementation: [backend/evaluate_reports.py](../../../Ivanek-Anakin/ANOTE_mobile/backend/evaluate_reports.py) (642 lines).
- Driver model: `gpt-4-1-mini` by default (overridable via `--model`); judge runs on the *same* model with a separate JSON‑mode call.
- Prompt variants already wired in: `v0` (baseline) … `v4` (current production with adherence/negation/SA/roles). Selectable via `--prompt-variant`.
- Inputs: any directory of `.txt` transcripts. Outputs: `evaluation_results.json` + console table.
- Existing rubric (6 dimensions, 0–5):
  1. `factual_accuracy`
  2. `completeness`
  3. `structure`
  4. `negation_handling`
  5. `clinical_language`
  6. `noise_resilience`
- Composite score = simple mean. Thresholds: ≥ 4.0 production, 3.0–3.9 acceptable, < 3.0 fail.
- Hallucinations and omissions are returned as free‑text lists per scenario.
- Known evaluation results stored under `backend/evaluation_results*.json` and `backend/eval_v{1..3}_{demo,hurvinek}.json` (already used to compare prompt variants).

The judge script does **not** currently include criteria specific to the 5 defects; it operates at the rubric level. It does, however, capture hallucinations and omissions as free‑text — which would catch issue 3 if the judge happens to flag a fabricated pollen allergy, but this is not enforced.

---

## 5. Allergy hallucination root cause (Issue 3 — JAR → pollen)

**Search for "JAR", "jaro", "jara", "pyl"** across the entire fixture set returned **no hits in any committed transcript**. The only allergy artifacts present are:
- feedback4: ananas (correctly handled)
- feedback6: ibuprofen (correctly handled)
- feedback2: prach/dust (correctly handled)
- cz_respiracni_infekce: penicilin (correctly handled)

**Conclusion (with caveats):**

| Layer | Likelihood of being root cause | Reasoning |
|-------|-------------------------------|-----------|
| Whisper / ASR | **Most likely** | "JAR" is a 3‑letter all‑caps brand name. Czech Whisper will transcribe it phonetically as "jar" (lowercase common noun) or, with declension context ("alergický na…"), as the inflected form **"jara"** or **"jaro"** — both of which mean *spring (season)*. The Czech medical hotwords list (`mobile/assets/hotwords_cs_medical.txt`) does not contain "JAR" or other dish‑soap brands. |
| LLM | **Low** | If the LLM literally received the token "JAR" it would not infer "pollen". It would more plausibly write "alergie na JAR (čisticí prostředek)" or refuse. The leap from *jara/jaro* → "pylová alergie" is a reasonable but wrong **clinical inference** the LLM makes once the ASR has substituted the word. |

So: **most plausible chain is ASR substitution `JAR → jara/jaro` followed by LLM clinical inference `jaro → pyl/pylová alergie`.** The LLM is the *amplifier*, not the *origin*.

Implications for the prompt fix:
- The prompt cannot recover "JAR" from "jaro" without context, so a defensive rule is appropriate: "Pokud v AA zazní slovo 'jaro' nebo 'jara' bez explicitní zmínky pylu, NEINTERPRETUJ to automaticky jako pylovou alergii — uveď to doslova nebo označ jako 'nejasné, k upřesnění'."
- Long term, the proper fix is a Whisper hotword for "JAR" (and other common household brand names). Out of scope for prompt‑engineering only.

This split of responsibilities should be flagged to the team — the prompt fix will only attenuate the issue; eliminating it requires Whisper‑level work.

---

## 6. Testing plan

### A. How to test prompts without modifying the live backend — **3 options**

1. **(Recommended) Reuse `evaluate_reports.py` directly.**
   - It already accepts `--prompt-variant`, calls Azure OpenAI directly (bypassing the FastAPI backend), runs the judge, and writes machine‑readable JSON.
   - To test a new prompt: add a `v5` (or `feedback_fixes`) entry to `PROMPT_VARIANTS` in the script *or* parameterize via a new flag (`--system-prompt-file`). Either is purely local — production is untouched.
   - The script imports its own copy of the prompt builder (it does not import `main.py`), which means changes in the script do not change deployed behavior.
   - The script reads `AZURE_OPENAI_KEY` from env. Currently `backend/.env` has only `OPENAI_API_KEY` — for direct Azure calls we either (a) add `AZURE_OPENAI_KEY` locally (per `workflows/azure-cli-access.md`) or (b) extend the script to fall back to plain OpenAI like `main.py` does.
   - **Lowest friction; lowest production risk; produces judge‑graded comparable JSON; reuses existing rubric.**

2. **Run FastAPI locally with `MOCK_MODE=false` and a local prompt edit on a feature branch.**
   - `uvicorn main:app --reload --port 8000` from `backend/`.
   - Point a test client at `http://localhost:8000/report`.
   - Higher friction (must run a server, manage env, integrate with judge), but useful if we want to test the *end‑to‑end* path including request validation. No production impact, as long as we never deploy the branch.

3. **Standalone ad‑hoc script bypassing both backend and judge.**
   - Useful only for hand‑inspection / quick prompt iteration. Not recommended as a regression mechanism.

**Primary recommendation: option 1.** It is already 90 % built. We extend `evaluate_reports.py` with the new variant + extend `_call` results into per‑defect assertions (see §B).

### B. Prompt comparison test structure

Proposed new file: `backend/evaluate_prompts.py` (thin wrapper around `evaluate_reports.py`) **or** simply an added `v5` variant + a new pytest module `backend/tests/test_prompt_fixes.py` that:

1. Inputs:
   - **Existing fixtures kept:** `testing_hurvinek/*.txt` (defects 1, 2), `feedback6.txt` transcript portion (defect 4), `feedback4.txt` (defect 5).
   - **New synthetic fixtures (proposed in §D):** one per defect that the existing set does not cover: `cz_jar_allergy.txt` (defect 3), `cz_quiet_compliant.txt` (defect 4 — patient never discusses adherence), `cz_terse_dosing.txt` (defect 5 — explicit "1 tbl." dictation).
2. For each fixture × prompt variant `(v4_baseline, v5_candidate)`:
   - Generate report (existing `generate_report`).
   - Apply **structural assertions** specific to each defect (see table).
   - Run the judge (existing `evaluate_report`) and additionally inject 5 new dimensions (see §C).
   - Persist to `evaluation_results_v5.json`.
3. Comparison output: side‑by‑side markdown table; pass/fail per defect per fixture per variant.

**Per‑defect assertions (deterministic, no LLM needed):**

| Defect | Fixture | Assertion |
|--------|---------|-----------|
| 1 | hurvinek_*.txt | Report does not contain song/rhyme tokens (`stůně myš`, `slůně`, `♪`, `divadlo`, `paní učitelka` if not relevant). NO section length ≤ 80 % of transcript words about NO. |
| 2 | hurvinek_*.txt + new synthetic | Any pattern matching `\b(TK|TF|P|SpO2|TT|teplota)\s*\d` appears under `Objektivní nález:` and not under `NO:`. Conversely, `udává|říká|cítí` patterns must not appear inside Objektivní nález. |
| 3 | new `cz_jar_allergy.txt` | Report does not contain `pyl`, `pylová`, `pylové`, `pylové alergi`. Must contain literal `JAR`/`jar` OR `nejasné` flag. |
| 4 | new `cz_quiet_compliant.txt` (patient never discusses adherence) | Report's `Adherence a spolupráce pacienta:` block equals `neuvedeno` — must NOT contain the substrings `Spolupráce dobrá`, `režim dodržuje` when adherence was not discussed. |
| 5 | new `cz_terse_dosing.txt` (doctor says "Furosemid 1 tbl. ráno") | Report's `FA` section contains `1 tbl.` or `1 tableta` or `1‑0‑0` literal — must NOT replace it with paraphrases like `pravidelně`, `předepsanou medikaci`, `dle doporučení`. |

**Recommendation:** extend the existing `test_report_quality.py` with a new class `TestFeedbackFixes` so the assertions live alongside the other live tests, **and** add `v5` to `evaluate_reports.py`'s `PROMPT_VARIANTS`. Two artefacts: deterministic regression tests (pytest) + judge‑scored variant comparison (JSON).

### C. LLM‑as‑Judge extension

The existing 6 dimensions stay. Add **5 binary criteria** (one per defect), each scored `pass / fail` with a reason. JSON shape extension:

```json
"feedback_fixes": {
  "irrelevant_content": {"pass": true, "reason": "..."},
  "exam_findings_placement": {"pass": true, "reason": "..."},
  "allergy_no_pollen_hallucination": {"pass": true, "reason": "..."},
  "no_cooperation_boilerplate": {"pass": false, "reason": "Adherence section says 'Spolupráce dobrá' although patient did not discuss adherence."},
  "dosage_preservation": {"pass": true, "reason": "..."}
}
```

Why binary, not 1–5: each defect is a discrete clinical correctness condition; a graded score adds noise. Aggregate across runs as `pass_rate` per criterion per variant.

Storage & comparability:
- Add `prompt_variant` to the per‑result record (already there).
- Always write to `evaluation_results_<variant>_<scenarios>.json` so v4 and v5 sit side by side.
- Add a `compare_variants.py` (or extend `summarize_results.py`) to print a delta table: `criterion | v4_pass_rate | v5_pass_rate | Δ`.

### D. Transcript fixtures needed

Existing fixtures cover defects 1 and 2 well (Hurvínek set), partially cover 4 and 5 (only via output samples), and do not cover 3 at all.

**Proposed new synthetic fixtures (clean Czech, ~150–250 words each):**

| Filename | Purpose | Should contain | Should NOT contain |
|----------|---------|----------------|--------------------|
| `cz_jar_allergy.txt` | Defect 3 regression | Doctor asks about allergies; patient answers "jsem alergický na JAR, vždycky mi po něm zčervenají ruce" (or post‑ASR variant "alergický na jaro" with surrounding cleaning context) | Any mention of pollen/season |
| `cz_quiet_compliant.txt` | Defect 4 regression | A short visit where adherence is **never discussed** (patient states symptoms, doctor examines, prescribes) | Any phrase resembling "spolupráce", "dodržuje režim", "bere léky pravidelně" |
| `cz_terse_dosing.txt` | Defect 5 regression | Doctor dictates terse abbreviations: "Furosemid 1 tbl. ráno, Anopyrin 100 mg 1‑0‑0, Atorvastatin 20 mg večer" | (input only — assertion is on output) |
| `cz_objective_in_dialogue.txt` (optional) | Reinforces defect 2 | Doctor speaks measurements aloud during exam: "tlak 145/90, puls 78, teplota 36,8" interleaved with patient narration | (input only) |

> ⚠️ **Synthetic fixtures must be reviewed by Dr. Jan Brož before being used as permanent regression inputs.** They will be marked clearly as "synthetic — pending clinical review" in their headers and excluded from any clinical evaluation reports until approved.

---

## 7. Other findings relevant to the 5 fixes

1. **The "Spolupráce dobrá" boilerplate is encoded into the prompt itself** ([backend/main.py L172–L184](../../../Ivanek-Anakin/ANOTE_mobile/backend/main.py)): the `Adherence a spolupráce pacienta` section explicitly tells the model to emit this phrase when adherence is good. Defect 4 cannot be fixed without **changing this rule** to: "Pokud téma adherence nezaznělo, napiš 'neuvedeno'. Frázi 'spolupráce dobrá' uveď POUZE pokud zaznělo, že pacient režim výslovně dodržuje, ALE častěji popisuj jen non‑compliance (česká norma — adherence se popisuje jen pokud není v normě)."
2. **The base rules already contain the dose‑preservation rule** but it lives in a long bullet list. Promoting it to its own paragraph and adding an explicit "NEPARAFRÁZUJ" instruction is likely to materially improve defect 5.
3. **`evaluate_reports.py` duplicates the prompt builder.** Any prompt change must be applied in **both** `backend/main.py` and `backend/evaluate_reports.py` — easy to miss, and the existing v4 is the only proof that the duplication is currently in sync. We should add a unit test that asserts the two builders produce identical output for the production variant. (Out of scope for TASK‑0036 fixing, in scope for TASK‑0036 testability.)
4. **No `temperature` is currently sent.** When we move to non‑reasoning fallbacks (`gpt-4-1-mini`) the judge currently uses temp 0.3 for generation and 0.0 for judging — production sends none. We should check whether `evaluate_reports.py` is therefore measuring a slightly different output distribution than production. For prompt comparison this is usually fine (relative deltas hold), but absolute pass rates may not transfer.
5. **No regression of the existing 6‑dimension scores when adding the 5 new binary criteria.** Re‑running v4 over the existing scenario set before any prompt change establishes the baseline; v5 must not regress on any of the original 6 dimensions while improving on the 5 new criteria.
6. **GDPR.** Existing tests confirm transcript text is not echoed in error responses. New fixtures should remain synthetic; never commit feedback`*`.txt content into permanent assertion strings.

---

## 8. Recommended next concrete steps

1. Add `v5_feedback_fixes` to `PROMPT_VARIANTS` in `backend/evaluate_reports.py` containing the 5 targeted prompt deltas (boilerplate suppression, dose‑preservation emphasis, JAR/jaro defensive note, NO‑vs‑Objektivní reinforcement, irrelevant‑content filter expansion).
2. Add the 5 binary criteria to `JUDGE_SYSTEM_PROMPT` and parse them into the result JSON.
3. Add `backend/tests/test_prompt_fixes.py` with deterministic per‑defect string assertions over the existing Hurvínek set.
4. Create the 3 (optionally 4) synthetic fixtures listed in §D under `test_scenarios/feedback_fixes/`. Mark them as pending Dr. Brož review.
5. Run `evaluate_reports.py --prompt-variant v4` and `… --prompt-variant v5_feedback_fixes` over the Hurvínek + new fixtures; commit `evaluation_results_v4_*.json` and `evaluation_results_v5_*.json` for diff.
6. Only after green: apply the v5 prompt deltas into `backend/main.py` (`_build_base_rules` + Adherence section) and ship in a single, reviewed PR.

---

*End of investigation report.*
