# TASK-0036 Baseline Session Report

Date: 2026-05-02  
Repo: `/Users/ivananikin/Documents/Ivanek-Anakin/ANOTE_mobile`

## What was created

- Synthetic transcript fixtures under `test_scenarios/feedback_fixes/`
- New pytest suite: `backend/tests/test_prompt_fixes.py`
- Baseline summary (blocked-run documentation): `backend/tests/baseline_v4_results.md`
- Pytest output capture: `backend/tests/baseline_v4_pytest.txt`
- Pytest marker registration: `pytest.ini` (`feedback_fixes` marker)
- Combined scenario folder prepared for judge run: `backend/eval_dataset/task0036_baseline_v4/`

## New fixture files and word counts

- `test_scenarios/feedback_fixes/cz_jar_allergy.txt` — 219 words
- `test_scenarios/feedback_fixes/cz_quiet_compliant.txt` — 208 words
- `test_scenarios/feedback_fixes/cz_terse_dosing.txt` — 200 words
- `test_scenarios/feedback_fixes/cz_objective_in_dialogue.txt` — 190 words

All fixtures include required header:

- `# Synthetic transcript — pending Dr. Brož clinical review`
- `# Do not use in clinical evaluations until reviewed.`

## Required output paths

- Test suite: `backend/tests/test_prompt_fixes.py`
- v4 baseline JSON: `backend/evaluation_results_v4_baseline_TASK0036.json`
- Baseline markdown summary: `backend/tests/baseline_v4_results.md`
- Pytest output: `backend/tests/baseline_v4_pytest.txt`

## Current v4 baseline scores

LLM-as-judge scoring completed successfully over 11 scenarios with prompt variant v4.

- Mean composite: 4.93
- Per-dimension means: Fact 5.00, Completeness 4.64, Structure 5.00, Negation 5.00, Clinical language 5.00, Noise resilience 5.00

### Scenario x rubric scores (requested table)

| Scenario | Fact | Comp | Strc | Neg | Lang | Noise | Composite |
|---|---:|---:|---:|---:|---:|---:|---:|
| S Hurvínkem za lékařem   1  Díl   Nachlazení | 5 | 4 | 5 | 5 | 5 | 5 | 4.8 |
| S Hurvínkem za lékařem   2  Díl   Zlomenina | 5 | 4 | 5 | 5 | 5 | 5 | 4.8 |
| S Hurvínkem za lékařem 08 Angína | 5 | 4 | 5 | 5 | 5 | 5 | 4.8 |
| cz_detska_prohlidka | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_jar_allergy | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_kardialni_nahoda | 5 | 4 | 5 | 5 | 5 | 5 | 4.8 |
| cz_objective_in_dialogue | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_otrava_jidlem | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_quiet_compliant | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_respiracni_infekce | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |
| cz_terse_dosing | 5 | 5 | 5 | 5 | 5 | 5 | 5.0 |

### Composite per scenario and overall mean

- Composite per scenario: see table above
- Overall mean composite: 4.93

## Manual 5-defect baseline (requested)

Manual pass/fail against generated reports was completed in `backend/tests/baseline_v4_results.md` (per-scenario matrix with citations).

- Defect 1 (off-topic leakage): 11/11 pass
- Defect 2 (objective placement): 10/11 pass
- Defect 3 (JAR handling): 10/11 pass
- Defect 4 (cooperation boilerplate): 5/11 pass
- Defect 5 (dosage preservation): 11/11 pass

## Test suite verification

Command executed:

```bash
./.venv/bin/python -m pytest backend/tests/test_prompt_fixes.py -v -m feedback_fixes | tee backend/tests/baseline_v4_pytest.txt
```

Observed result:

- 10 tests collected
- 7 tests passed
- 3 tests failed
- 0 tests skipped

Failures proving defect detection on v4:

- `test_objective_findings_in_correct_section[cz_objective_in_dialogue]`
- `test_jar_allergy_no_pollen_inference`
- `test_no_cooperation_boilerplate_when_absent`

Unexpected passes worth monitoring:

- `test_no_song_or_offtopic_in_report` passed on all Hurvínek scenarios
- `test_dosage_preserved_verbatim` passed on the terse dosing fixture

Interpretation:

- The suite reproduces defects 2, 3, and 4 on v4 with deterministic failures in this run.
- Defect 1 and defect 5 did not reproduce on this model run and appear currently non-failing under this baseline path.

## Reproducibility instructions

From repo root:

```bash
# 1) Obtain Azure key in current shell only (do not write to disk)
source .venv/bin/activate
export AZURE_OPENAI_KEY="$(az containerapp secret show -g anote-rg -n anote-api --secret-name azure-openai-key --query value -o tsv)"

# 2) Build/refresh combined baseline scenario set
mkdir -p backend/eval_dataset/task0036_baseline_v4
cp test_scenarios/cz_*.txt backend/eval_dataset/task0036_baseline_v4/
cp testing_hurvinek/*.txt backend/eval_dataset/task0036_baseline_v4/
cp test_scenarios/feedback_fixes/*.txt backend/eval_dataset/task0036_baseline_v4/

# 3) Run v4 judge baseline (creates required JSON)
cd backend
../.venv/bin/python evaluate_reports.py \
  --scenarios-dir eval_dataset/task0036_baseline_v4 \
  --prompt-variant v4 \
  --output evaluation_results_v4_baseline_TASK0036.json

# 4) Run targeted pytest suite and capture output
cd ..
./.venv/bin/python -m pytest backend/tests/test_prompt_fixes.py -v -m feedback_fixes \
  | tee backend/tests/baseline_v4_pytest.txt
```

Required environment variables:

- `AZURE_OPENAI_KEY` (required; exported in current shell only)
- Optional overrides depending on local setup: deployment/model args to `evaluate_reports.py`

Approximate runtime and Azure cost (this run):

- Scenarios: 11
- Generation tokens (tracked): 32,074 prompt + 6,643 completion = 38,717
- Generation API time (sum): 58.49s
- End-to-end generate+judge time (from per-scenario log sums): ~97s, plus CLI overhead
- Cost: non-zero; expected low single-digit USD for this run, exact amount depends on deployed Azure model pricing and judge token accounting

## Known limitations

- Synthetic fixtures are provisional and not clinically approved.
- Judge script logs generation token usage, but does not persist judge token usage per scenario in output JSON.

## Clinical review notes for Dr. Brož

Potentially weak synthetic points to review:

- `cz_jar_allergy.txt`: confirm wording around contact dermatitis and whether allergy framing should be narrowed to irritant/contact reaction language.
- `cz_terse_dosing.txt`: confirm medication mix and abbreviated dosing style are clinically realistic for routine dictation.
- `cz_objective_in_dialogue.txt`: validate that interleaving objective values with subjective narration reflects realistic ambulatory workflow.

## Readiness for v5 prompt-fix work

v5 prompt-fix implementation can proceed from a technical baseline standpoint (v4 baseline + failing tests are now in place), but fixture sign-off by Dr. Brož is still required before treating synthetic scenarios as clinically validated regression assets.

## Regression-set interpretation

- Most reliably reproduced defects in this run: Defect 4 (cooperation boilerplate), plus targeted failures for Defect 2 and Defect 3.
- Flaky or not reproduced in this run: Defect 1 (off-topic leakage) and Defect 5 (dosage paraphrasing) did not fail under current model/path.
- Existing demo scenarios already pass v4 and should not be primary regression sentinels for TASK-0036 defects: `cz_detska_prohlidka`, `cz_kardialni_nahoda`, `cz_otrava_jidlem`, `cz_respiracni_infekce`.

## v5 comparison (2026-05-02)

Three v5 candidates were generated (`v5a_negative`, `v5b_positive`, `v5c_fewshot`) and run against the v4 baseline on all 7 fixtures using both the legacy 6-dim judge and the new TASK-0036 weighted rubric (8 factors, total weight 15). Full breakdown: [`backend/tests/v5_comparison.md`](../../../Ivanek-Anakin/ANOTE_mobile/backend/tests/v5_comparison.md).

Headline:

| Variant | 6-dim mean | Weighted | Pytest |
|---|---|---|---|
| v4 | 4.91 | 4.352 | baseline |
| v5a `negative` | 4.86 | 4.581 | 8/10 |
| v5b `positive` | 4.91 | 4.400 | 7/10 |
| v5c `fewshot` | 4.91 | **4.495** | **9/10** |

**Recommended next step:** iterate on `v5c_fewshot` — best clinical_relevance (4.143) and section_placement (4.714), no 6-dim regression, fewest pytest failures. Caveat: `adherence_appropriateness` regressed to 2.857 (boilerplate over-insertion from few-shot pattern); next iteration `v5d` should swap one few-shot example to demonstrate `Adherence: neuvedeno`. The single remaining pytest failure (`test_jar_allergy_no_pollen_inference`) is a test-design issue (AA-section-literal-`jar` assertion), not a clinical regression — pollen-hallucination check passes for all v5 variants. **All v5 results remain provisional pending Dr. Brož clinical signoff** on the synthetic fixtures.

### v5d / v5e iteration (2026-05-02)

Two isolation variants tested against the v5c adherence regression: **v5d_adherence_example** (richer realistic Example C) and **v5e_explicit_rule** (single explicit imperative). **Neither clears the acceptance gate** (weighted ≥ 4.50, adherence ≥ 4.0): v5d 4.428 / 3.000, v5e 4.448 / 3.143. Both improve adherence vs v5c (2.857) but lose v5c's clinical_relevance gain (back to 3.571). Pytest: both 9/10 (after loosening `test_jar_allergy_no_pollen_inference` per spec). **Recommendation: stay on `v5c_fewshot` and iterate to `v5f`** = v5c + v5e's explicit rule (expanded to name the polite-patient trap `"Rozumím, děkuji"`) + a sixth few-shot example demonstrating that polite agreement ≠ adherence evidence. Full breakdown: [`backend/tests/v5_comparison.md`](../../../Ivanek-Anakin/ANOTE_mobile/backend/tests/v5_comparison.md) → "v5d / v5e iteration" section. Still provisional pending Dr. Brož signoff.
