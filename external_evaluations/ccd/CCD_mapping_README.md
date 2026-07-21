# External-corpus dimension mapping

Maps items from external cultural benchmarks (CCD-Bench, EtiCor++) onto Erin Meyer's
8 Culture Map dimensions, and validates the mapping against blind human annotation.

The mapping is **not** an evaluation axis — it is corpus analysis. Its output feeds two
claims in the paper: that existing cultural benchmarks do not cover Meyer's dimensions,
and that automatic cultural labelling is fragile in specific, measurable ways.

---

## Result

| System | Information seen | Accuracy (n=90) |
|---|---|---|
| Rule-based mapper (v2) | stem + answer options | **57%** |
| LLM, weak prompt, stem only | stem | 69% |
| LLM, hardened prompt, stem only | stem | 72% |
| **LLM, hardened prompt, + options** ← final | stem + answer options | **78%** |

Ground truth: 90 CCD-Bench items, blind double annotation (κ = 0.56), 68 by agreement
and 22 by adjudication. Both the rules baseline and the final mapping see the same
information, so the 21-point gap is a difference in reasoning, not in evidence.

**The final CCD mapping is `data/external/ccd/CCD_llm_options.jsonl`.**

---

## Where things live

```
data/external/ccd/
    CCD_remapped.jsonl              rules v2 (baseline, 57%)
    CCD_llm.jsonl                   LLM, weak prompt, stems only     [ablation]
    CCD_ablation_noopts.jsonl       LLM, hardened prompt, stems only [ablation]
    CCD_llm_options.jsonl           FINAL MAPPING (78%)
    CCD_llm_options_diff.csv        per-item diff vs the stem-only run
    CCD_ablation_noopts_diff.csv    per-item diff vs the stem-only run
    annotation/
        CCD_annotation_guideline_v2.md   pre-registered, derived from Meyer
        CCD_round3_BLIND_v2.csv          the 90-item blind sample
        CCD_round3_GUILLE_v2.csv         independent annotation
        CCD_round3_BLANCA_v2.csv         independent annotation
        CCD_round3_ADJUDICATION.csv      the 22 disagreements, resolved

src/mapping/ccd/
    map_ccd_dimensions_v2.py        rule-based mapper
    llm_map_with_options.py         LLM pass (--no-options reproduces the ablation)
    llm_map_unmapped.py             earlier stem-only pass, kept for the ablation
    eval_llm_vs_consensus.py        scoring against human ground truth
    build_consensus_and_stats.py    builds consensus from two annotators' CSVs
    README.md                       this file
```

All three LLM runs are kept on purpose. `CCD_llm_options.jsonl` is only interpretable
next to the other two: together they are the ablation.

---

## Pipeline

```
CCD-Bench_MCQ_v2_mapped.xlsx          (third-party corpus, not in this repo)
        │
        ├─ map_ccd_dimensions_v2.py   rules  →  CCD_remapped.jsonl        (baseline, 57%)
        │
        ├─ llm_map_with_options.py    LLM    →  CCD_llm_options.jsonl     (FINAL, 78%)
        │                             --no-options  →  ablation runs
        │
        └─ eval_llm_vs_consensus.py   scored against the human ground truth
```

### 1. Rule-based mapper (baseline)

```bash
pip install pandas openpyxl
python src/mapping/ccd/map_ccd_dimensions_v2.py \
    --input  data/external/ccd/CCD-Bench_MCQ_v2_mapped.xlsx \
    --outdir data/external/ccd
```

Deterministic. Classifies stem + options (the four generic filler distractors are
stripped first). Default label is `Unmapped`; confidence comes from score margin plus
corroboration, never a single keyword hit. `matched_phrases` records exactly which
phrases fired, so every label is auditable.

Produces 275/369 `Unmapped` (74.5%).

### 2. LLM mapping pass (final)

Needs a Groq API key in a `.env` file at the repo root:

```
GROQ_API_KEY=gsk_...
```

```bash
# sanity check first — one real batch, printed raw, writes nothing
python src/mapping/ccd/llm_map_with_options.py \
    --xlsx    data/external/ccd/CCD-Bench_MCQ_v2_mapped.xlsx \
    --rules   data/external/ccd/CCD_remapped.jsonl \
    --output  data/external/ccd/CCD_llm_options.jsonl \
    --compare data/external/ccd/CCD_llm.jsonl \
    --check

# the real run (~8 min, ~82k tokens, resumable with --resume)
python src/mapping/ccd/llm_map_with_options.py \
    --xlsx    data/external/ccd/CCD-Bench_MCQ_v2_mapped.xlsx \
    --rules   data/external/ccd/CCD_remapped.jsonl \
    --output  data/external/ccd/CCD_llm_options.jsonl \
    --compare data/external/ccd/CCD_llm.jsonl
```

`llama-3.3-70b-versatile`, temperature 0, JSON-constrained, batches of 15.

**Budget matters.** The Groq free tier caps this model at 100,000 tokens/day. The system
prompt is ~800 tokens and a CCD question is ~55, so one-item-per-call would spend ~88% of
every request re-sending the same instructions and need ~295,000 tokens — three times the
cap. Batching amortises it to ~82,000. Batch contamination was checked: per-batch label
distributions show no bleed between adjacent items.

### 3. Ablation

Two things changed between the first and final LLM passes: the answer options were added
**and** the system prompt was hardened with an explicit GLOBE exclusion list. `--no-options`
runs the hardened prompt on stems only, isolating the two.

```bash
python src/mapping/ccd/llm_map_with_options.py \
    --xlsx    data/external/ccd/CCD-Bench_MCQ_v2_mapped.xlsx \
    --rules   data/external/ccd/CCD_remapped.jsonl \
    --output  data/external/ccd/CCD_ablation_noopts.jsonl \
    --compare data/external/ccd/CCD_llm.jsonl \
    --no-options
```

**The two metrics disagree, and that is the finding.** By label churn, the prompt looks
decisive: it moves 66 of the 73 items that became `Unmapped` (90%), the options only 7.
By accuracy against human ground truth, the options do more: the prompt adds +3 points,
the options +6. The prompt relabels many items but only about half of them correctly — it
improves rejection (71% → 85% on `Unmapped` items) while degrading assignment (65% → 48%).
The options recover assignment without giving back the rejection gain.

Counting how many labels changed would have led to the wrong conclusion. Only accuracy
against human ground truth separates them.

### 4. Evaluation

```bash
python src/mapping/ccd/eval_llm_vs_consensus.py \
    --llm-output data/external/ccd/CCD_llm_options.jsonl \
    --consensus  data/external/ccd/annotation/CCD_round3_ADJUDICATION.csv
```

---

## Human validation

Three rounds. Only round 3 counts; the first two are kept because their failure modes are
themselves results.

| Round | Setup | κ |
|---|---|---|
| 1 | non-blind (v1 mapper labels visible) | 0.68 |
| 2 | blind, **stem only** | **0.31** |
| 3 | blind, **stem + answer poles** | **0.56** |

**Round 2's collapse was not noise.** With only the stem, a CCD item is underdetermined —
*"How do you approach change in your professional life?"* cannot be labelled without seeing
what the options contrast. The annotators were not disagreeing; they were guessing. Adding
the poles nearly doubled agreement, with the same two people and the same guideline.

**Inter-annotator agreement is a function of the information available, not only of
annotator skill.**

Round 3 used a pre-registered guideline (`data/external/ccd/annotation/CCD_annotation_guideline_v2.md`)
derived from Meyer's book — deliberately not from the mapper's behaviour or the model's
output, which would have made the ground truth circular.

---

## Findings

**79% of CCD-Bench has no Meyer dimension** (290 of 369). Human annotators independently
agree: 59 of the 90 ground-truth items are `Unmapped`. The corpus encodes GLOBE/Hofstede
constructs Meyer has no dimension for — individualism–collectivism, long/short-term
orientation, uncertainty avoidance, attitude to risk and technology, assertiveness,
work–life balance, performance orientation.

**Persuading is entirely absent.** Zero under the rules, zero in the final LLM mapping,
zero in human ground truth. The 6 Persuading labels produced by the weak-prompt run were
hallucinations: given an underdetermined stem and no explicit exclusion, the model invented
the construct rather than declining.

**Per-dimension scoring on CCD is impossible.** Final counts: Leading 42, Deciding 20,
Disagreeing 7, Trusting 4, Scheduling 3, Communicating 2, Evaluating 1, Persuading 0.
External-corpus labels are therefore used as a general cultural-awareness pool, not for
per-dimension scoring.

**Boilerplate distractors.** Every one of the 369 questions contains at least one of four
fixed generic distractors, each recurring 177–190 times across the corpus. Stripping them
leaves exactly two real options per item — the two poles of the construct. Both the rules
mapper and the LLM pass strip them before classifying.

---

## Limitations

**`Leading` is a magnet. Precision 47% (7 of 15).** When the final mapping says Leading it
is wrong more than half the time. Recall is fine (7/10) — precision is what fails. Leading
is where the model goes when the item is ambiguous.

**Evaluating only against inter-annotator consensus overstates accuracy.** On the 68
agreement rows the final mapping scores 88%; on all 90 (adding the 22 adjudicated, i.e.
hard, rows) it scores 78%. Consensus rows are by construction the easy ones. Report the
adjudicated set.

**The model shares the more conservative annotator's bias — and that bias was wrong.**
Adjudication went 13–9 in favour of the annotator who assigned *more* dimensions. The model
sides with the conservative reading, which adjudication overturned. Evaluation against
consensus alone would never have surfaced this.

**The v1 garbage bucket contaminated the human annotators.** The v1 mapper had no
`Unmapped` category and forced all 369 items into a dimension; `Scheduling` absorbed 143
of them (39%), mostly long-term-orientation content. Round 1 was annotated with those
labels visible. In round 2 — blind — one annotator was still applying the v1 `Scheduling`
criterion from memory. Only an explicit warning in the round-3 guideline eliminated it.

> **Do not validate an automatic mapping with annotators who have seen its output.** The
> contamination is not just copied labels; it is a learned criterion that persists after
> the labels are removed.

**Other:** n=90 (±8-point interval on 78%); a single annotator model
(llama-3.3-70b-versatile); the adjudication criteria were applied but not recorded in the
`rule_applied` column.

---

## EtiCor++

`src/mapping/eticor/map_eticor_dimensions.py` applies the same lexicon. Earlier validation put it at 92%, but
that figure was measured with the protocol that turned out to overstate CCD accuracy, and
the EtiCor rules never saw an explicit GLOBE exclusion. **It needs re-checking before it
goes in the paper.**

---

## Files

| Path | What |
|---|---|
| `data/external/ccd/CCD_remapped.jsonl` | Rules v2 (baseline) |
| `data/external/ccd/CCD_llm.jsonl` | LLM, weak prompt, stems only (ablation) |
| `data/external/ccd/CCD_ablation_noopts.jsonl` | LLM, hardened prompt, stems only (ablation) |
| `data/external/ccd/CCD_llm_options.jsonl` | **Final mapping** |
| `data/external/ccd/annotation/` | Guideline, blind sample, both annotations, adjudication |

The CCD-Bench corpus itself is third-party and is not redistributed here:
https://github.com/smartlab-nyu/CCD-Bench
