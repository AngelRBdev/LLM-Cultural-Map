#!/usr/bin/env python3
"""
CCD mapping pass WITH the answer options — LLM Cultural Map benchmark.

Why this exists
---------------
The mapping pipeline so far (rules mapper, LLM pass, human annotation) only ever saw the
question STEM. The answer options were dropped during preprocessing. But CCD-Bench is a
multiple-choice corpus, and in an MCQ the construct often lives in the OPTIONS, not in the
stem:

    stem   : "How do you approach change in your professional life?"   <- underdetermined
    pole 1 : "I resist change if it disrupts the immediate workflow."
    pole 2 : "I adopt change if it benefits long-term growth."         <- now it is clear

Every CCD item has 4 options, of which 2 are drawn from a fixed pool of 4 generic
distractors that repeat across the corpus (~180-190 times each):

    "Postpone acting until they have gathered more input from trusted advisors..."
    "Seek a negotiated compromise that partially satisfies both..."
    "Defer the decision to a senior authority or supervisor..."
    "Adopt whichever option carries the least personal risk..."

Stripping those leaves exactly 2 real options per item — the two poles of the construct.
Those are what we send.

This script re-runs the mapping with stem + the 2 real poles, then DIFFS the result
against the stem-only run so you can see, as a number, whether the options change
anything. If they do not, that is a finding: it confirms the Unmapped items are genuinely
GLOBE constructs with no Meyer dimension, at the option level and not just the stem level.

Inputs
------
  --xlsx    CCD-Bench_MCQ_v2_mapped.xlsx   (the corpus WITH options)
  --rules   CCD_remapped.jsonl             (the v2 rules labels, to preserve as baseline)
  --compare CCD_llm.jsonl                  (optional: the stem-only LLM run, to diff against)

Usage
-----
    pip install openpyxl
    python llm_map_with_options.py --xlsx "..\\Datasets\\CCD-Bench_MCQ_v2_mapped.xlsx" ^
        --rules "..\\Datasets\\CCD_remapped.jsonl" ^
        --output "..\\Datasets\\CCD_llm_options.jsonl" ^
        --compare "..\\Datasets\\CCD_llm.jsonl" --check

Then drop --check to run for real. Add --resume if it gets interrupted.

Budget: 369 items, batches of 15 -> ~25 calls, ~79,000 tokens. The Groq free-tier cap for
llama-3.3-70b-versatile is 100,000 tokens/day, so this fits — but only just. Do not run it
twice in one day. Use --unmapped-only (275 items, ~60,000 tokens) if the budget is tight.
"""

import argparse, csv, json, os, random, sys, time
import urllib.error, urllib.request
from collections import Counter

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
USER_AGENT = "llm-cultural-map/5.0 (research benchmark; polimi)"   # avoids Cloudflare 1010

DIMENSIONS = ["Communicating", "Evaluating", "Persuading", "Leading",
              "Deciding", "Trusting", "Disagreeing", "Scheduling"]

# The 4 fixed distractors that repeat across the corpus. Matched by prefix.
BOILERPLATE = [
    "Postpone acting until they have gathered more input",
    "Seek a negotiated compromise that partially satisfies",
    "Defer the decision to a senior authority",
    "Adopt whichever option carries the least personal risk",
]

SYSTEM_PROMPT = """You classify multiple-choice questions against Erin Meyer's 8 Culture Map dimensions.

You are given, for each item, a QUESTION and the TWO ANSWER POLES it contrasts. The poles
are usually what reveals the underlying construct — read them carefully, not just the question.

The dimensions (with their two poles):
1. Communicating — low-context (explicit, literal) vs high-context (implicit, read between the lines).
2. Evaluating — direct negative feedback (frank criticism) vs indirect (softened, private).
3. Persuading — principles-first (theory before conclusion) vs applications-first. This is about HOW AN ARGUMENT IS STRUCTURED, never about attitudes to change or innovation.
4. Leading — egalitarian (flat, skip levels) vs hierarchical (status, titles, deference). This is Hofstede's power distance.
5. Deciding — consensual (group agreement before commitment) vs top-down (the boss decides and informs).
6. Trusting — task-based (trust from competence, track record) vs relationship-based (trust from shared meals, personal bonds).
7. Disagreeing — confrontational (open disagreement is healthy) vs avoids confrontation (it harms harmony).
8. Scheduling — linear-time (punctuality, deadlines, one thing at a time) vs flexible-time (fluid, interruptions). This comes from Hall's monochronic/polychronic distinction: TIME as a tangible thing.

CRITICAL — most of this corpus is NOT about Meyer at all. It was built from GLOBE/Hofstede
constructs, which Meyer's framework has no dimension for. Answer "None" whenever the two
poles contrast any of the following:
  * individualism vs collectivism (personal goals vs team goals, working alone vs in a group)
  * long-term vs short-term orientation (investing for the future, career horizon, job security)
  * attitude to risk, technology, innovation or change (adopt early vs wait and see)
  * uncertainty avoidance
  * assertiveness / competitiveness vs cooperativeness
  * work-life balance, family vs career
  * performance orientation (merit, results, productivity)
  * business-etiquette protocol (business cards, dress codes, gifts, greetings)

"None" is the expected answer for the majority of items. Do not stretch to find a
dimension. Only assign one when the two poles genuinely instantiate that dimension's
construct.

Some items genuinely engage TWO dimensions (e.g. poles contrasting "the group agrees
together" vs "the senior manager decides" touch Deciding AND Leading). Then give the
dominant one as "dimension" and the other as "secondary_dimension". Most items have at
most one.

You will receive a NUMBERED LIST. Classify EVERY item independently.

Answer ONLY with a JSON object with one entry per input item, reusing the same "i" numbers:
{"results": [{"i": 1, "dimension": "<Communicating|Evaluating|Persuading|Leading|Deciding|Trusting|Disagreeing|Scheduling|None>", "secondary_dimension": "<same options, or None>", "reason": "<one short sentence>"}]}"""


def load_api_key():
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key.strip()
    here = os.path.abspath(os.getcwd())
    for _ in range(4):
        p = os.path.join(here, ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.strip().startswith("GROQ_API_KEY"):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        print(f"API key loaded from {p}")
                        return v
        nxt = os.path.dirname(here)
        if nxt == here:
            break
        here = nxt
    sys.exit("\nERROR: no GROQ_API_KEY. Put GROQ_API_KEY=gsk_... in a .env file.\n")


def parse_duration(v):
    if not v:
        return 0.0
    v = v.strip()
    try:
        mins = 0.0
        if "m" in v and "ms" not in v:
            a, _, v = v.partition("m")
            mins = float(a)
        if v.endswith("ms"):
            s = float(v[:-2]) / 1000
        elif v.endswith("s"):
            s = float(v[:-1]) if v[:-1] else 0.0
        else:
            s = float(v) if v else 0.0
        return mins * 60 + s
    except ValueError:
        return 0.0


def is_boilerplate(text):
    return any(text.strip().startswith(b) for b in BOILERPLATE)


def load_items(xlsx_path, rules_path):
    """One record per unique stem: question + the 2 real poles + the rules label."""
    try:
        import openpyxl
    except ImportError:
        sys.exit("\nERROR: openpyxl is not installed.  Run:  pip install openpyxl\n")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    I = {h: i for i, h in enumerate(hdr)}
    for need in ("original_question", "option_A", "option_B", "option_C", "option_D"):
        if need not in I:
            sys.exit(f"\nERROR: column '{need}' not found in the xlsx. Found: {hdr}\n")

    items, seen = [], set()
    n_bad = 0
    for r in it:
        q = r[I["original_question"]]
        if not q:
            continue
        q = str(q).strip()
        if q in seen:
            continue
        seen.add(q)
        opts = [str(r[I[f"option_{L}"]] or "").strip() for L in "ABCD"]
        poles = [o for o in opts if o and not is_boilerplate(o)]
        if len(poles) != 2:
            n_bad += 1
        items.append({"original_question": q, "poles": poles,
                      "domain": str(r[I["domain"]] or "") if "domain" in I else ""})

    rules = {}
    for line in open(rules_path, encoding="utf-8"):
        if line.strip():
            d = json.loads(line)
            rules[d["original_question"].strip()] = {
                "meyer_dimension_rules": d.get("meyer_dimension", "Unmapped"),
                "mapping_confidence_rules": d.get("mapping_confidence", "none"),
            }
    for it_ in items:
        it_.update(rules.get(it_["original_question"],
                             {"meyer_dimension_rules": "Unmapped",
                              "mapping_confidence_rules": "none"}))

    print(f"Unique stems in the xlsx: {len(items)}")
    print(f"Stems whose options do NOT reduce to exactly 2 real poles: {n_bad}")
    return items


def build_prompt(batch, show_options=True):
    """
    ABLATION NOTE. The with-options run changed TWO things at once versus the original
    stem-only run: it added the answer poles AND it hardened the GLOBE exclusion list in
    the system prompt. That confounds the result — the +73 Unmapped items cannot be
    attributed to the options alone.

    Passing show_options=False (--no-options) runs the SAME hardened prompt with the
    stems only, isolating the variable:
        result ~= the with-options run   -> the prompt did the work; options add nothing
        result ~= the original run       -> the options did the work; that is the finding
    """
    n = len(batch)
    if not show_options:
        out = [f"Classify each of the following {n} items.\n"]
        for i, it in enumerate(batch, 1):
            out.append(f"{i}. QUESTION: {it['original_question'].strip()[:400]}\n")
        return "\n".join(out)

    out = [f"Classify each of the following {n} multiple-choice items.\n"]
    for i, it in enumerate(batch, 1):
        out.append(f"{i}. QUESTION: {it['original_question'].strip()[:400]}")
        for j, p in enumerate(it["poles"], 1):
            out.append(f"   POLE {j}: {p.strip()[:300]}")
        out.append("")
    return "\n".join(out)


def call_batch(model, batch, key, state, max_retries=6, verbose=False, show_options=True):
    payload = {"model": model, "temperature": 0.0,
               "max_tokens": 90 * len(batch) + 250,
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": build_prompt(batch, show_options)}]}
    body = json.dumps(payload).encode()
    last = "unknown"

    for attempt in range(max_retries):
        gap = time.time() - state["last"]
        if gap < 3.0:
            time.sleep(3.0 - gap)
        state["last"] = time.time()

        req = urllib.request.Request(
            GROQ_URL, data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=150) as resp:
                data = json.loads(resp.read())
                H = resp.headers
            content = data["choices"][0]["message"]["content"]
            if verbose:
                print("    raw:", content.strip()[:700])
            parsed = json.loads(content)
            results = parsed.get("results")
            if not isinstance(results, list):
                raise ValueError("no 'results' array")

            by_i = {}
            for e in results:
                try:
                    idx = int(e.get("i"))
                except (TypeError, ValueError):
                    continue
                dim = str(e.get("dimension", "None")).strip()
                if dim not in DIMENSIONS:
                    dim = "None"
                sec = str(e.get("secondary_dimension", "None")).strip()
                if sec not in DIMENSIONS or sec == dim or dim == "None":
                    sec = "None"
                by_i[idx] = (dim, sec, str(e.get("reason", ""))[:200])
            missing = [i for i in range(1, len(batch) + 1) if i not in by_i]
            if missing:
                raise ValueError(f"model skipped items {missing}")

            if not state["printed"]:
                print(f"Groq limits -> tokens/min: {H.get('x-ratelimit-limit-tokens')}, "
                      f"requests/day: {H.get('x-ratelimit-limit-requests')}")
                state["printed"] = True
            try:
                rem = H.get("x-ratelimit-remaining-tokens")
                if rem is not None and int(rem) < 4000:
                    w = parse_duration(H.get("x-ratelimit-reset-tokens") or "") + 1
                    if w > 0:
                        print(f"    [pacer] token budget low ({rem}) — pausing {w:.0f}s")
                        time.sleep(w)
            except (TypeError, ValueError):
                pass
            return "ok", [by_i[i] for i in range(1, len(batch) + 1)]

        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            if e.code == 403 and "1010" in detail:
                sys.exit("\nERROR: Cloudflare 1010 — you are running an old copy of this script.\n")
            if e.code in (401, 403):
                sys.exit(f"\nERROR: HTTP {e.code} — bad API key or no access to '{model}'.\n{detail}\n")
            if e.code == 404:
                sys.exit(f"\nERROR: HTTP 404 — model '{model}' does not exist on Groq.\n")
            if e.code == 429:
                w = parse_duration(e.headers.get("retry-after", "")) or min(60, 10 * (attempt + 1))
                if w > 300:
                    return "error", (f"DAILY TOKEN CAP REACHED — Groq wants {w/60:.0f} min. "
                                     f"The free-tier budget for '{model}' is spent for today "
                                     f"(resets 00:00 UTC = 02:00 Spanish time).")
                print(f"    rate-limited — waiting {w:.0f}s [{attempt+1}/{max_retries}]",
                      file=sys.stderr)
                time.sleep(w + 1)
                last = "HTTP 429"
                continue
            if e.code >= 500:
                time.sleep(min(30, 5 * (attempt + 1)))
                last = f"HTTP {e.code}"
                continue
            last = f"HTTP {e.code}: {detail}"
            print(f"    {last}", file=sys.stderr)
            time.sleep(3)
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            print(f"    {last} — retrying", file=sys.stderr)
            time.sleep(3)

    return "error", last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--rules", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--compare", default=None,
                    help="the stem-only run (CCD_llm.jsonl) to diff against")
    ap.add_argument("--model", default="llama-3.3-70b-versatile")
    ap.add_argument("--batch-size", type=int, default=15)
    ap.add_argument("--unmapped-only", action="store_true",
                    help="only send items the rules left Unmapped (cheaper: ~60k tokens)")
    ap.add_argument("--no-options", action="store_true",
                    help="ABLATION: same hardened prompt, but send the STEM ONLY. Isolates whether the options or the prompt caused the change.")
    ap.add_argument("--check", action="store_true", help="one real batch, printed, then stop")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    show_opts = not args.no_options
    if not show_opts:
        print("\n*** ABLATION MODE: hardened prompt, STEM ONLY (no options sent) ***\n")
    items = load_items(args.xlsx, args.rules)
    todo = [i for i in items if i["meyer_dimension_rules"] == "Unmapped"] \
        if args.unmapped_only else items

    n_calls = -(-len(todo) // args.batch_size)
    est = n_calls * (800 + args.batch_size * (165 if show_opts else 100))
    print(f"To classify: {len(todo)} | batches of {args.batch_size} -> {n_calls} calls | "
          f"~{est:,} tokens (free-tier cap: 100,000/day)")
    if est > 95000:
        print("  WARNING: this is very close to the daily cap. Consider --unmapped-only.")

    key = load_api_key()
    state = {"last": 0.0, "printed": False}

    if args.check:
        batch = todo[: args.batch_size]
        print(f"\n--- CHECK: one real batch of {len(batch)} ---")
        st, res = call_batch(args.model, batch, key, state, max_retries=2, verbose=True,
                             show_options=show_opts)
        if st != "ok":
            print(f"\nFAILED: {res}")
            return
        print()
        for it, (d, s, r) in zip(batch, res):
            print(f"  Q: {it['original_question'][:66]}")
            for p in it["poles"]:
                print(f"     | {p[:66]}")
            old = it["meyer_dimension_rules"]
            print(f"     -> LLM+options: {d}" + (f" (+{s})" if s != "None" else "")
                  + f"   [rules said: {old}]")
        print(f"\nAll {len(batch)} came back aligned. Drop --check to run for real.")
        return

    ckpt_path = args.output + ".checkpoint.jsonl"
    done = {}
    if args.resume and os.path.exists(ckpt_path):
        for l in open(ckpt_path, encoding="utf-8"):
            d = json.loads(l)
            done[d["key"]] = d
        print(f"Resuming: {len(done)} already done.")
    elif os.path.exists(ckpt_path):
        sys.exit(f"\nERROR: checkpoint exists at {ckpt_path}. Use --resume, or delete it.\n")

    pending = [i for i in todo if i["original_question"] not in done]
    ckpt = open(ckpt_path, "a", encoding="utf-8")
    n_ok = n_none = 0
    failed = 0
    t0 = time.time()

    for s in range(0, len(pending), args.batch_size):
        batch = pending[s: s + args.batch_size]
        st, res = call_batch(args.model, batch, key, state, show_options=show_opts)
        if st == "error":
            failed += 1
            print(f"\n  BATCH FAILED: {res}", file=sys.stderr)
            if n_ok == 0:
                ckpt.close()
                sys.exit("\nABORTED: first batch failed, nothing saved.\n")
            if failed >= 3:
                ckpt.close()
                sys.exit(f"\nSTOPPED after {failed} failed batches. {n_ok} items are "
                         f"checkpointed — re-run with --resume.\n")
            continue
        for it, (d, sec, r) in zip(batch, res):
            n_ok += 1
            if d == "None":
                n_none += 1
            rec = {"key": it["original_question"], "llm_dimension": d,
                   "llm_secondary": sec, "llm_reason": r}
            ckpt.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done[it["original_question"]] = rec
        ckpt.flush()
        el = time.time() - t0
        rate = n_ok / max(el, 1) * 60
        print(f"  {n_ok}/{len(pending)} | none={n_none} | {rate:.0f}/min | "
              f"~{(len(pending)-n_ok)/max(rate,.1):.0f} min left")
    ckpt.close()

    # ---- merge ----
    out = []
    for it in items:
        r = dict(it)
        r.pop("poles", None)
        rec = done.get(it["original_question"])
        if rec:
            r["meyer_dimension"] = rec["llm_dimension"] if rec["llm_dimension"] != "None" else "Unmapped"
            r["meyer_dimension_secondary"] = rec["llm_secondary"]
            r["llm_reason"] = rec["llm_reason"]
            r["source"] = "llm+options" if show_opts else "llm+prompt_only"
        else:
            r["meyer_dimension"] = it["meyer_dimension_rules"]
            r["meyer_dimension_secondary"] = "None"
            r["source"] = "rules"
        out.append(r)
    with open(args.output, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    tag = "llm+options" if show_opts else "llm+prompt_only"
    lab = [r for r in out if r["source"] == tag and r["meyer_dimension"] != "Unmapped"]
    print("\n" + "=" * 64)
    print(f"Classified with options: {n_ok}   (failed batches: {failed})")
    print(f"  given a dimension:     {n_ok - n_none}")
    print(f"  'None' / Unmapped:     {n_none}")
    print("Distribution:", dict(Counter(r["meyer_dimension"] for r in lab)))
    print("=" * 64)

    # ---- THE DIFF: does seeing the options change anything? ----
    if args.compare and os.path.exists(args.compare):
        old = {}
        for l in open(args.compare, encoding="utf-8"):
            if l.strip():
                d = json.loads(l)
                old[d["original_question"].strip()] = d.get("meyer_dimension", "Unmapped")
        both = [r for r in out if r["original_question"] in old and r["source"] == tag]
        changed = [(old[r["original_question"]], r["meyer_dimension"], r["original_question"])
                   for r in both if old[r["original_question"]] != r["meyer_dimension"]]
        rescued = [c for c in changed if c[0] == "Unmapped" and c[1] != "Unmapped"]
        lost = [c for c in changed if c[0] != "Unmapped" and c[1] == "Unmapped"]

        print("\n" + "#" * 64)
        print("#  DOES SEEING THE OPTIONS CHANGE THE MAPPING?")
        print("#" * 64)
        print(f"  items comparable            : {len(both)}")
        print(f"  labels CHANGED              : {len(changed)}  ({len(changed)/len(both)*100:.0f}%)")
        print(f"    Unmapped -> a dimension   : {len(rescued)}   <- the 'rescue' effect")
        print(f"    a dimension -> Unmapped   : {len(lost)}")
        print(f"    dimension -> dimension    : {len(changed)-len(rescued)-len(lost)}")
        print(f"\n  Unmapped rate, stem only    : "
              f"{sum(1 for q in old if old[q]=='Unmapped')}/{len(old)}")
        print(f"  Unmapped rate, with options : "
              f"{sum(1 for r in out if r['meyer_dimension']=='Unmapped')}/{len(out)}")
        print("\n  DECISION RULE: if <10% of labels changed, the options add nothing and the")
        print("  stem-only mapping stands (a finding: the corpus is GLOBE at the option level")
        print("  too). If >25% changed, the mapping must be redone with options.")
        if rescued:
            print(f"\n  Sample of rescued items (max 10 of {len(rescued)}):")
            for o, n, q in rescued[:10]:
                print(f"    {o} -> {n:13} | {q[:58]}")

        with open(args.output.replace(".jsonl", "_diff.csv"), "w", newline="",
                  encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["original_question", "stem_only", "with_options", "changed"])
            for r in both:
                o = old[r["original_question"]]
                w.writerow([r["original_question"], o, r["meyer_dimension"],
                            "YES" if o != r["meyer_dimension"] else ""])
        print(f"\n  Full diff written to: {args.output.replace('.jsonl', '_diff.csv')}")

    # ---- blind validation sample, now WITH the options shown ----
    if lab or out:
        random.seed(42)
        poles = {i["original_question"]: i["poles"] for i in items}
        samp = random.sample(out, min(40, len(out)))
        p = args.output.replace(".jsonl", "_validation_sample.csv")
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["original_question", "pole_1", "pole_2", "meyer_dimension",
                        "meyer_dimension_secondary", "llm_reason",
                        "human_dimension", "human_agrees", "notes"])
            for r in samp:
                pp = poles.get(r["original_question"], ["", ""]) + ["", ""]
                w.writerow([r["original_question"], pp[0], pp[1], r["meyer_dimension"],
                            r.get("meyer_dimension_secondary", "None"),
                            r.get("llm_reason", ""), "", "", ""])
        print(f"  Validation sample: {p}")
    print(f"  Merged output:     {args.output}")


if __name__ == "__main__":
    main()
