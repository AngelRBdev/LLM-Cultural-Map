#!/usr/bin/env python3
"""
CCD-Bench → Meyer 8-dimension mapper, v2 (corrected methodology).
LLM Cultural Map benchmark — task 6.

Applies to CCD-Bench the SAME lexicon and confidence calibration used for the
EtiCor++ mapping (map_eticor_dimensions.py), so the paper presents ONE mapping
method applied uniformly to both external corpora. The three fixes over the
v1 CCD mapping:

  1. DEFAULT = "Unmapped". v1 fell back to Scheduling (inflating it to 39%),
     and its Scheduling rules included long-term-orientation and career/family
     regexes that belong to GLOBE/Hofstede constructs, not Meyer's Scheduling.
     Items with no genuine Meyer content now stay Unmapped — which is the
     honest structural finding: CCD-Bench was built on the GLOBE
     individualism/collectivism axis, not on Meyer's dimensions.
  2. CONFIDENCE BY MARGIN + CORROBORATION:
       high   : top score >= 6 (defining phrase + corroboration) AND margin >= 3
       medium : top score >= 4 (single defining phrase) AND margin >= 2
       low    : any other non-zero match
     v1 assigned "high" from a single weight-4 keyword hit (59% high).
  3. AUDIT COLUMN: matched_phrases records exactly which phrases fired.

Classification input: the question stem (original_question) concatenated with
the four options of its first variant — in CCD MCQs the cultural signal often
lives in the options ("consult my team" vs "decide alone"), not the stem.

v1 labels are PRESERVED as meyer_dimension_v1 / mapping_confidence_v1 so the
workbook shows the before/after delta transparently.

Input  : CCD-Bench_MCQ_v2_mapped.xlsx  (the MCQ workbook, 3690 rows / 369 unique stems)
Outputs: <prefix>_remapped.xlsx / CCD_remapped.jsonl / CCD_validation_sample.csv

NOTE ON THE CLASSIFICATION INPUT (important for the paper):
this mapper classifies the QUESTION STEM CONCATENATED WITH THE ANSWER OPTIONS, after
stripping the four generic filler distractors. So the rule-based baseline and the final
LLM mapping see exactly the same information — the +21-point gap between them (57% -> 78%
against human ground truth) is a difference in reasoning, not in available evidence.

Deterministic. The only randomness is the seeded validation sample (seed=42).

Usage:
    pip install pandas openpyxl
    python map_ccd_dimensions_v2.py --input  data/external/ccd/CCD-Bench_MCQ_v2_mapped.xlsx \
                                    --outdir data/external/ccd
"""

import argparse
import json
import os
import random
import re
import sys
import unicodedata
from collections import defaultdict

import pandas as pd

SEED = 42
DEFAULT_SHEET = "Benchmark_MCQ_mapped"

# ─────────────────────────────────────────────────────────────────────────────
# Lexicon — IDENTICAL to map_eticor_dimensions.py (single method, two corpora).
# Construct-scoped: no long-term-orientation, career/family, motivation or
# change/innovation rules (the v1 mislabel sources for Scheduling, Trusting
# and Persuading respectively).
# ─────────────────────────────────────────────────────────────────────────────
RULES = {
    "Communicating": [
        (r"read(ing)? between the lines", 4),
        (r"read(ing)? the air", 4),
        (r"indirect(ly)?\s+communicat", 4),
        (r"communicat\w*\s+(in)?direct(ly)?", 4),
        (r"\bimplicit|implied|implication\b", 4),
        (r"nonverbal (cue|communication)|non-verbal (cue|communication)", 4),
        (r"subtle (hint|cue|message)s?", 4),
        (r"a simple ['\"]?yes['\"]?", 4),
        (r"\bvague(ness)?\b", 2),
        (r"\bexplicit(ly)?\b", 2),
        (r"silence (is|can|often|may)", 2),
        (r"body language", 2),
        (r"say(ing)? ['\"]?no['\"]? directly", 2),
        (r"direct communication", 2),
        (r"\bdirectness\b", 2),
        (r"moments? of silence", 2),
    ],
    "Evaluating": [
        (r"(negative|critical) feedback", 4),
        (r"(direct|indirect)\w* (negative )?feedback", 4),
        (r"giv\w+ negative feedback", 4),
        (r"criticiz|criticis|critique", 4),
        (r"correct(ing)? (someone|a colleague|an employee) in (public|front)", 4),
        (r"prais\w+ .{0,30}(public|private)", 4),
        (r"\bfeedback\b", 2),
        (r"compliment", 1),
        (r"(lose|losing|save|saving) face", 1),
    ],
    "Persuading": [
        (r"principles?[- ]first|applications?[- ]first", 4),
        (r"(theory|theoretical|conceptual) (first|before|framework)", 4),
        (r"deductive|inductive", 4),
        (r"conclusion first|start with the conclusion", 4),
        (r"big picture before", 2),
    ],
    "Leading": [
        (r"hierarch", 4),
        (r"chain of command", 4),
        (r"defer(ence|ential)? to (senior|superior|boss|elder|authority)", 4),
        (r"address .{0,40}by (their )?(title|first name)", 4),
        (r"(use|using) (formal )?titles", 4),
        (r"aura of authority", 4),
        (r"boss.?s boss", 4),
        (r"power distance", 4),
        (r"(higher|senior) positions? .{0,40}(command|deserve|receive) (more )?respect", 4),
        (r"respect .{0,40}(bound by|based on|tied to) .{0,15}(titles?|positions?|rank)", 4),
        (r"not bound by (job )?titles?", 4),
        (r"egalitarian", 4),
        (r"senior(s)? and elders|respect (to|for) (senior|elder|superior)", 2),
        (r"\brank\b|\bseniority\b", 2),
        (r"\b(boss|superior)e?s?\b", 1),
        (r"top management|junior (staff|colleague|employee)", 1),
    ],
    "Deciding": [
        (r"\bconsensus\b", 4),
        (r"(group|collective|joint) decision", 4),
        (r"unanimous", 4),
        (r"\bringi\b( system)?", 4),
        (r"consensual decision.?making", 4),
        (r"group agreement", 4),
        (r"boss (makes?|takes?) the (final )?(call|decision)", 4),
        (r"top[- ]down decision", 4),
        (r"(management|leadership|the boss|leaders?) (should )?makes? (the )?final decisions? and inform", 4),
        (r"(decided?|determined?) collectively", 4),
        (r"collectively decide", 4),
        (r"open discussion so (that )?everyone", 4),
        (r"decision[- ]?making", 2),
        (r"decisions? (are|is) made", 1),
    ],
    "Trusting": [
        (r"build(ing)? (a )?(personal )?relationship", 4),
        (r"personal (rapport|connection|bond|relationship)", 4),
        (r"relationship(s)? (before|first|is key|are key|matter)", 4),
        (r"get(ting)? to know .{0,40}before .{0,20}business", 4),
        (r"trust is (built|established|earned)", 4),
        (r"(cognitive|affective) trust", 4),
        (r"relationship (is|are) built", 4),
        (r"get\w* to know .{0,40}before .{0,25}(business|down to business)", 4),
        (r"\btrust(ing|worthy|worthiness)?\b", 2),
        (r"socializ|socialis", 2),
        (r"long[- ]term relationship", 2),
        (r"friendship in business|business friendship", 2),
        (r"(business )?(lunch|dinner|meal) .{0,40}(relationship|partner|deal)", 1),
    ],
    "Disagreeing": [
        (r"confrontation(al)?", 4),
        (r"disagree(ment)?s? (openly|in public|directly|publicly)", 4),
        (r"avoid (open )?(conflict|confrontation|disagreement|argument)", 4),
        (r"(open|public|direct) (debate|argument|disagreement)", 4),
        (r"challeng\w+ .{0,30}(openly|in public|in front)", 4),
        (r"\bdisagree", 2),
        (r"\bconflict\b", 2),
        (r"\bharmony\b", 2),
        (r"\bdebate\b", 1),
        (r"\bargu(e|ing|ment)\b", 1),
        (r"emotionally expressive|emotional expressiveness", 4),
        (r"without attacking", 2),
    ],
    "Scheduling": [
        (r"punctual", 4),
        (r"\bon time\b", 4),
        (r"(be(ing)?|arriv\w*) (late|early)|lateness", 4),
        (r"time is (money|valued|flexible|fluid)", 4),
        (r"linear.?time|flexible.?time", 4),
        (r"keep .{0,30}waiting", 4),
        (r"start(ing)? (and end(ing)? )?on (the )?(dot|time)", 4),
        (r"\bdeadlines?\b", 2),
        (r"\bschedule[sd]?\b|\bscheduling\b", 2),
        (r"\bagenda\b", 2),
        (r"\bdelay(s|ed)?\b", 1),
        (r"\bwaiting\b", 1),
    ],
}

COMPILED = {
    dim: [(re.compile(rx, re.IGNORECASE), w) for rx, w in rules]
    for dim, rules in RULES.items()
}

def normalise(text: str) -> str:
    t = unicodedata.normalize("NFKC", str(text))
    return t.strip().strip('"\u201c\u201d').strip()

def classify(text: str):
    t = normalise(text)
    scores, matches = {}, defaultdict(list)
    for dim, rules in COMPILED.items():
        s = 0
        for rx, w in rules:
            m = rx.search(t)
            if m:
                s += w
                matches[dim].append(f"{m.group(0)[:40]}(+{w})")
        if s:
            scores[dim] = s
    if not scores:
        return "Unmapped", "none", 0, 0, ""
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top_dim, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    margin = top - second
    if top >= 6 and margin >= 3:
        conf = "high"
    elif top >= 4 and margin >= 2:
        conf = "medium"
    else:
        conf = "low"
    audit = " | ".join(f"{d}: {', '.join(ms)}" for d, ms in matches.items())
    return top_dim, conf, top, margin, audit

# CCD-Bench inserts generic filler distractors into most questions (each of
# these appears verbatim in ~180-190 of the 369 unique stems). They carry no
# signal about the QUESTION's dimension and would poison classification (e.g.
# "Defer the decision to a senior authority" would fire Leading on ~half the
# corpus). They are stripped before classification.
BOILERPLATE = {
    "Postpone acting until they have gathered more input from trusted advisors before committing.",
    "Seek a negotiated compromise that partially satisfies both their own position and the opposing one.",
    "Defer the decision to a senior authority or supervisor and follow whatever ruling is given.",
    "Adopt whichever option carries the least personal risk regardless of the underlying principle.",
}

def is_boilerplate(opt: str) -> bool:
    o = str(opt).strip()
    return any(o.startswith(b[:60]) for b in BOILERPLATE)

def parse_args():
    ap = argparse.ArgumentParser(
        description="CCD-Bench -> Meyer 8-dimension mapper (v2). "
                    "Classifies stem + answer options; default label is Unmapped.")
    ap.add_argument("--input", required=True,
                    help="CCD-Bench_MCQ_v2_mapped.xlsx (the MCQ workbook)")
    ap.add_argument("--outdir", default=".",
                    help="where to write the outputs (default: current directory)")
    ap.add_argument("--sheet", default=DEFAULT_SHEET,
                    help=f"worksheet name (default: {DEFAULT_SHEET})")
    ap.add_argument("--seed", type=int, default=SEED)
    return ap.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.input):
        sys.exit(f"\nERROR: input not found: {args.input}\n")
    os.makedirs(args.outdir, exist_ok=True)
    out_xlsx = os.path.join(args.outdir, "CCD-Bench_MCQ_v2_remapped.xlsx")
    out_jsonl = os.path.join(args.outdir, "CCD_remapped.jsonl")
    out_sample = os.path.join(args.outdir, "CCD_validation_sample.csv")

    try:
        df = pd.read_excel(args.input, sheet_name=args.sheet)
    except ValueError:
        xl = pd.ExcelFile(args.input)
        sys.exit(f"\nERROR: no sheet named '{args.sheet}'. Sheets found: {xl.sheet_names}\n"
                 f"Pass the right one with --sheet.\n")

    required = ["original_question", "domain", "meyer_dimension", "mapping_confidence",
                "option_A", "option_B", "option_C", "option_D"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"\nERROR: the workbook is missing these columns: {missing}\n"
                 f"Found: {list(df.columns)}\n")

    # preserve v1 labels
    df = df.rename(columns={"meyer_dimension": "meyer_dimension_v1",
                            "mapping_confidence": "mapping_confidence_v1"})

    # classification text per unique stem: original_question + first variant's options
    firsts = df.groupby("original_question", sort=False).first()
    cls = {}
    for oq, row in firsts.iterrows():
        opts = " ".join(str(row[f"option_{k}"]) for k in "ABCD"
                        if not is_boilerplate(row[f"option_{k}"]))
        cls[oq] = classify(f"{oq} {opts}")

    df["meyer_dimension"] = df["original_question"].map(lambda q: cls[q][0])
    df["mapping_confidence"] = df["original_question"].map(lambda q: cls[q][1])
    df["match_score"] = df["original_question"].map(lambda q: cls[q][2])
    df["score_margin"] = df["original_question"].map(lambda q: cls[q][3])
    df["matched_phrases"] = df["original_question"].map(lambda q: cls[q][4])

    # ---- JSONL (unique stems only: the mapping deliverable) ----
    uq = df.drop_duplicates("original_question")
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for _, r in uq.iterrows():
            f.write(json.dumps({
                "original_question": r["original_question"],
                "domain": r["domain"],
                "meyer_dimension": r["meyer_dimension"],
                "mapping_confidence": r["mapping_confidence"],
                "match_score": int(r["match_score"]),
                "score_margin": int(r["score_margin"]),
                "matched_phrases": r["matched_phrases"],
                "meyer_dimension_v1": r["meyer_dimension_v1"],
                "mapping_confidence_v1": r["mapping_confidence_v1"],
            }, ensure_ascii=False) + "\n")

    # ---- Excel (same sheet layout as v1 workbook, + comparison sheet) ----
    dim_summary = (uq.groupby(["meyer_dimension", "mapping_confidence"])
                     .size().unstack(fill_value=0))
    dim_x_domain = (uq[uq.meyer_dimension != "Unmapped"]
                    .groupby(["meyer_dimension", "domain"]).size().unstack(fill_value=0))
    v1_vs_v2 = pd.crosstab(uq["meyer_dimension_v1"], uq["meyer_dimension"],
                           rownames=["v1 (Blanca)"], colnames=["v2 (corrected)"])
    caveats = pd.DataFrame({"Caveat": [
        "v2 applies the SAME lexicon and confidence calibration as the EtiCor++ mapping: one method, two corpora.",
        "Default is 'Unmapped'. The large Unmapped share is the honest structural finding: CCD-Bench was built on the GLOBE individualism/collectivism axis, not on Meyer's 8 dimensions (as flagged in the v1 review).",
        "v1 fell back to Scheduling and included long-term-orientation / career-family rules; those items are now Unmapped, not Scheduling.",
        "high confidence requires a defining phrase PLUS corroboration and a margin over the 2nd dimension; a single keyword can reach at most medium.",
        "matched_phrases records exactly which phrases fired: every label is auditable.",
        "Classification input = question stem + options of the first variant (the cultural signal in MCQs often lives in the options).",
        "v1 labels are preserved in meyer_dimension_v1 / mapping_confidence_v1; the V1_vs_V2 sheet shows the full migration matrix.",
        "Validation: human-annotate CCD_validation_sample.csv (stratified) and report accuracy per confidence tier, same protocol as EtiCor++.",
    ]})
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Benchmark_MCQ_mapped", index=False)
        dim_summary.to_excel(xw, sheet_name="Dimension_summary")
        dim_x_domain.to_excel(xw, sheet_name="Dim_x_Domain")
        v1_vs_v2.to_excel(xw, sheet_name="V1_vs_V2")
        caveats.to_excel(xw, sheet_name="Mapping_caveats", index=False)

    # ---- Stratified validation sample over unique stems ----
    random.seed(args.seed)
    strata, per_cell = [], 5
    for dim in list(RULES.keys()) + ["Unmapped"]:
        for conf in ["high", "medium", "low", "none"]:
            cell = uq[(uq.meyer_dimension == dim) & (uq.mapping_confidence == conf)]
            if len(cell):
                take = cell.sample(min(per_cell, len(cell)), random_state=args.seed)
                strata.append(take[["original_question", "domain",
                                    "meyer_dimension", "mapping_confidence",
                                    "matched_phrases"]])
    sample = pd.concat(strata).sample(frac=1, random_state=args.seed)
    sample = sample.assign(human_dimension="", human_agrees="", notes="")
    sample.to_csv(out_sample, index=False, encoding="utf-8-sig")

    # ---- Report ----
    n = len(uq)
    print(f"Unique questions remapped: {n} (broadcast to {len(df)} rows)")
    print("\nv2 dimension distribution (369):")
    for d, c in uq.meyer_dimension.value_counts().items():
        print(f"  {d:15s}: {c:4d}  ({c/n*100:4.1f}%)")
    print("\nv2 confidence distribution (369):")
    for cf, c in uq.mapping_confidence.value_counts().items():
        print(f"  {cf:8s}: {c:4d}  ({c/n*100:4.1f}%)")
    print(f"\nValidation sample: {len(sample)} rows")
    print(f"\nOutputs:\n  {out_xlsx}\n  {out_jsonl}\n  {out_sample}")

if __name__ == "__main__":
    main()
