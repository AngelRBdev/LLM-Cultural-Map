#!/usr/bin/env python3
"""
Evaluate LLM mapping labels against the human-consensus ground truth.
Decides, with data, whether the LLM replaces the rules mapper for a corpus.

Ground truth: <corpus>_human_consensus.csv — the validation-sample rows where
Guillermo and Blanca independently agreed (CCD: 46 rows, EtiCor: 91 rows).
Columns: row_id, text, human_consensus, rules_label, tier.

Usage:
    python3 eval_llm_vs_consensus.py \
        --llm-output CCD_remapped_llm.jsonl \
        --consensus  CCD_human_consensus.csv

Reports:
  * Rules baseline accuracy (from the consensus file itself)
  * LLM primary-label accuracy
  * LLM dual accuracy (correct if consensus ∈ {primary, secondary})
  * Per confidence tier of the original rules mapping
  * A plain-language verdict line

Matching is by text (normalised); rows not found in the LLM output are
reported and excluded.
"""

import argparse
import json
import unicodedata

import pandas as pd


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", str(t))
    return " ".join(t.strip().strip('"\u201c\u201d').split()).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-output", required=True)
    ap.add_argument("--consensus", required=True)
    args = ap.parse_args()

    cons = pd.read_csv(args.consensus)
    rows = [json.loads(l) for l in open(args.llm_output) if l.strip()]
    text_field = next(f for f in ("original_question", "statement", "question", "text")
                      if f in rows[0])
    by_text = {norm(r[text_field]): r for r in rows}

    recs, missing = [], 0
    for _, c in cons.iterrows():
        r = by_text.get(norm(c["text"]))
        if r is None:
            missing += 1
            continue
        recs.append({
            "human": c["human_consensus"],
            "rules": c["rules_label"],
            "tier": c["tier"],
            "llm1": r.get("meyer_dimension", "Unmapped"),
            "llm2": r.get("meyer_dimension_secondary", "None"),
            "source": r.get("source", "?"),
        })
    df = pd.DataFrame(recs)
    if missing:
        print(f"WARNING: {missing} consensus rows not found in LLM output (excluded).")

    df["rules_ok"] = df["rules"] == df["human"]
    df["llm1_ok"] = df["llm1"] == df["human"]
    df["dual_ok"] = df.apply(
        lambda r: r["human"] in {r["llm1"], r["llm2"]} - {"None"}
        or (r["human"] == "Unmapped" and r["llm1"] == "Unmapped"), axis=1)

    n = len(df)
    print(f"\nConsensus rows evaluated: {n}")
    print(f"  Rules baseline accuracy : {df['rules_ok'].mean():.0%}")
    print(f"  LLM primary accuracy    : {df['llm1_ok'].mean():.0%}")
    print(f"  LLM dual accuracy       : {df['dual_ok'].mean():.0%}   "
          f"(correct if consensus in {{primary, secondary}})")
    print(f"  Items where LLM used a secondary: "
          f"{(df['llm2'].ne('None')).sum()}")

    print("\nPer original rules-confidence tier:")
    for tier in ["high", "medium", "low", "none"]:
        s = df[df["tier"] == tier]
        if not len(s):
            continue
        print(f"  {tier:6s} (n={len(s):3d}): rules {s['rules_ok'].mean():.0%}"
              f"  |  LLM primary {s['llm1_ok'].mean():.0%}"
              f"  |  LLM dual {s['dual_ok'].mean():.0%}")

    # confusion of LLM errors
    err = df[~df["dual_ok"]]
    if len(err):
        print(f"\nLLM errors ({len(err)}): human said "
              f"{err['human'].value_counts().to_dict()}, "
              f"LLM said {err['llm1'].value_counts().to_dict()}")

    # verdict
    r_acc, l_acc, d_acc = (df['rules_ok'].mean(), df['llm1_ok'].mean(),
                           df['dual_ok'].mean())
    print("\n--- Verdict ---")
    if d_acc >= r_acc + 0.15:
        print(f"ADOPT LLM for this corpus: dual accuracy {d_acc:.0%} clearly beats "
              f"rules {r_acc:.0%}. Use --all output as the corpus mapping; report "
              f"both numbers in the paper.")
    elif d_acc >= r_acc + 0.05:
        print(f"LLM is moderately better ({d_acc:.0%} vs {r_acc:.0%}). Consider "
              f"adopting; discuss with the team whether the gain justifies the "
              f"non-deterministic layer.")
    else:
        print(f"KEEP RULES: LLM ({d_acc:.0%}) does not clearly beat rules "
              f"({r_acc:.0%}) on this corpus. Keep the deterministic mapping and "
              f"report the comparison as a negative result.")


if __name__ == "__main__":
    main()
