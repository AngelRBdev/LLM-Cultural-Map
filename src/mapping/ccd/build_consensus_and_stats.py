#!/usr/bin/env python3
"""
Build human-consensus ground truth + validation statistics from the two
annotators' filled CSVs. Rerunnable: if the validation is redone, just swap
the filled files and run this again — everything downstream regenerates.

Inputs:
  --guillermo   Filled BLIND file (columns: row_id, <text>, human_dimension, notes)
  --blanca      Filled file. Two accepted formats, auto-detected:
                  (a) BLIND format (same as above)  ← recommended for re-runs
                  (b) original sample format (has meyer_dimension +
                      human_agrees); blanks are resolved to 'Unmapped'
  --answer-key  <corpus>_validation_ANSWERKEY.csv (mapper labels + tier)
  --corpus      Name used for output files (e.g. CCD, EtiCor)

Outputs (in --outdir, default .):
  <corpus>_human_consensus.csv      rows where both annotators agree
  <corpus>_adjudication_needed.csv  rows where they disagree
  stats printed to stdout: inter-annotator agreement, Cohen's kappa,
  mapper accuracy per confidence tier (vs each annotator and vs consensus)

Row alignment is positional (all files derive from the same sample in the
same order); when both files carry the mapper label it is cross-checked.
Labels are normalised (case/whitespace); anything not one of the 8 dimensions
or 'Unmapped' triggers a loud warning. Blank labels are counted, warned
about, and treated as 'Unmapped' (matching the documented resolution rule
from the first validation round — but please just write 'Unmapped').
"""

import argparse
import sys

import pandas as pd

VALID = {"Communicating", "Evaluating", "Persuading", "Leading",
         "Deciding", "Trusting", "Disagreeing", "Scheduling", "Unmapped"}


def normalise_label(x, where, warnings):
    if pd.isna(x) or str(x).strip() == "":
        warnings.append(f"blank label in {where} -> treated as Unmapped")
        return "Unmapped"
    lab = str(x).strip().title()
    if lab not in VALID:
        warnings.append(f"UNRECOGNISED label '{x}' in {where} -> kept verbatim, FIX IT")
        return str(x).strip()
    return lab


def kappa(a, b):
    labs = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa = pd.Series(a).value_counts(normalize=True)
    pb = pd.Series(b).value_counts(normalize=True)
    pe = sum(pa.get(l, 0) * pb.get(l, 0) for l in labs)
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guillermo", required=True)
    ap.add_argument("--blanca", required=True)
    ap.add_argument("--answer-key", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    g = pd.read_csv(args.guillermo)
    b = pd.read_csv(args.blanca)
    k = pd.read_csv(args.answer_key)
    if "row_id" in g.columns:
        g = g.sort_values("row_id")
    g = g.reset_index(drop=True)
    b = b.reset_index(drop=True)
    k = k.sort_values("row_id").reset_index(drop=True)
    if not (len(g) == len(b) == len(k)):
        sys.exit(f"Row-count mismatch: G={len(g)} B={len(b)} key={len(k)}")

    text_col = next(c for c in ("original_question", "statement", "question", "text")
                    if c in k.columns)

    # cross-check when the annotator file carries the mapper label
    if "meyer_dimension" in b.columns:
        if not (b["meyer_dimension"] == k["meyer_dimension"]).all():
            sys.exit("Blanca file rows are not aligned with the answer key "
                     "(mapper labels differ). Do not reorder the CSVs.")

    warnings = []
    g_lab = [normalise_label(x, f"Guillermo row {i+1}", warnings)
             for i, x in enumerate(g["human_dimension"])]
    b_lab = [normalise_label(x, f"Blanca row {i+1}", warnings)
             for i, x in enumerate(b["human_dimension"])]

    m = pd.DataFrame({
        "row_id": k["row_id"], "text": k[text_col],
        "rules_label": k["meyer_dimension"], "tier": k["mapping_confidence"],
        "guillermo": g_lab, "blanca": b_lab,
        "g_notes": g.get("notes", ""), "b_notes": b.get("notes", ""),
    })

    po, kap = kappa(m["guillermo"].tolist(), m["blanca"].tolist())
    cons = m[m["guillermo"] == m["blanca"]].copy()
    cons["human_consensus"] = cons["guillermo"]
    dis = m[m["guillermo"] != m["blanca"]]

    cpath = f"{args.outdir}/{args.corpus}_human_consensus.csv"
    apath = f"{args.outdir}/{args.corpus}_adjudication_needed.csv"
    cons[["row_id", "text", "human_consensus", "rules_label", "tier"]].to_csv(
        cpath, index=False)
    dis.to_csv(apath, index=False)

    print(f"===== {args.corpus} =====")
    if warnings:
        print(f"⚠ {len(warnings)} label warnings (first 5):")
        for w in warnings[:5]:
            print("   ", w)
    print(f"Rows: {len(m)} | consensus: {len(cons)} | disagreements: {len(dis)}")
    print(f"Inter-annotator agreement: {po:.0%} | Cohen's kappa: {kap:.2f}\n")
    print("Mapper accuracy per confidence tier:")
    print(f"  {'tier':6s} {'n':>3s}  {'vs_G':>5s} {'vs_B':>5s} {'vs_consensus':>12s}")
    for tier in ["high", "medium", "low", "none"]:
        s = m[m["tier"] == tier]
        if not len(s):
            continue
        c = s[s["guillermo"] == s["blanca"]]
        vc = (f"{(c['rules_label'] == c['guillermo']).mean():.0%} (n={len(c)})"
              if len(c) else "—")
        print(f"  {tier:6s} {len(s):3d}  "
              f"{(s['rules_label'] == s['guillermo']).mean():5.0%} "
              f"{(s['rules_label'] == s['blanca']).mean():5.0%} {vc:>12s}")
    ca = (cons["rules_label"] == cons["human_consensus"]).mean()
    print(f"\nOverall mapper accuracy on consensus rows: {ca:.0%} ({len(cons)})")
    print(f"\nWrote: {cpath}\n       {apath}")


if __name__ == "__main__":
    main()
