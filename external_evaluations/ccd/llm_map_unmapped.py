#!/usr/bin/env python3
"""
LLM-assisted mapping pass — LLM Cultural Map benchmark.
Third tier of the hybrid mapping method:  rules -> LLM -> human validation.

v4 (2026-07-13) — BATCHED.

Why batching: Groq's free tier caps llama-3.3-70b-versatile at 100,000 tokens
PER DAY. The system prompt (the 8 Meyer dimensions with their poles) is ~700
tokens; a CCD question is ~55. Sending one item per call therefore spends ~88%
of every request re-transmitting the same instructions, and the full 369-item
pass would need ~295,000 tokens — three times the daily cap. Unreachable.

Sending 10 items per call amortises the system prompt across the batch:
    one-by-one : ~295,000 tokens (3.0x the daily cap)   -> impossible
    batch of 10:  ~63,000 tokens (63% of the daily cap) -> ~10 minutes

Same model, same prompt, same task. Only the packing changes. The batch size is
recorded in the checkpoint so the paper can state the inference conditions.

v3 fixes retained:
  * a failed call is never confused with a legitimate "None"
  * failures are NOT checkpointed, so --resume retries them
  * the run aborts loudly instead of producing 369 silent Unmapped
  * rate limiting is driven by Groq's own headers, not by a fixed guess
  * a custom User-Agent avoids Cloudflare error 1010 on api.groq.com

Modes:
  DEFAULT (rescue): only rows the rules left "Unmapped" are sent. For EtiCor.
  --all (replace):  every row is sent; the LLM label becomes meyer_dimension and
                    the rules label is kept in meyer_dimension_rules. For CCD.

Usage:
    python llm_map_unmapped.py --input  ../Datasets/CCD_remapped.jsonl \
                               --output ../Datasets/CCD_llm.jsonl --all --check
    python llm_map_unmapped.py --input  ../Datasets/CCD_remapped.jsonl \
                               --output ../Datasets/CCD_llm.jsonl --all --resume

Key is read from GROQ_API_KEY (environment or a .env file in cwd or a parent).
"""

import argparse
import csv
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

# Both providers expose an OpenAI-compatible endpoint, so only the URL, the key
# and the model id change. Free-tier daily token budgets differ a lot, and that
# is the binding constraint for a 369-item pass:
#
#   groq     llama-3.3-70b-versatile   100,000 tokens/day   <- exhausted easily
#   groq     openai/gpt-oss-20b       ~200,000 tokens/day
#   groq     llama-3.1-8b-instant     ~500,000 tokens/day
#   cerebras gpt-oss-120b           ~1,000,000 tokens/day   (5 requests/minute)
#
# NOTE ON CIRCULARITY: the benchmark evaluates llama-3.1-8b, llama-3.3-70b,
# command-r, gpt-oss-20b and qwen3-32b. Using one of *those* models to annotate
# the corpus makes the annotator a member of the evaluated set. Prefer an
# annotator outside it (e.g. cerebras/gpt-oss-120b) and state it in the paper.
PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
        "min_gap": 2.5,
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "env": "CEREBRAS_API_KEY",
        "default_model": "gpt-oss-120b",
        "min_gap": 13.0,          # free tier is ~5 requests/minute
    },
}

# Cloudflare (which fronts api.groq.com) blocks the default urllib signature
# ("Python-urllib/3.x") with error code 1010 — a 403 that looks like an auth
# failure but is really a client-fingerprint ban. Any normal User-Agent passes.
USER_AGENT = "llm-cultural-map/4.0 (research benchmark; polimi)"

DIMENSIONS = ["Communicating", "Evaluating", "Persuading", "Leading",
              "Deciding", "Trusting", "Disagreeing", "Scheduling"]

SYSTEM_PROMPT = """You classify short texts against Erin Meyer's 8 Culture Map dimensions.

The dimensions (with their two poles):
1. Communicating — low-context (explicit, literal, repeated) vs high-context (implicit, layered, reading between the lines / reading the air).
2. Evaluating — direct negative feedback (frank criticism, upgraders) vs indirect negative feedback (softened, private, downgraders).
3. Persuading — principles-first (build the theory/concept before conclusions) vs applications-first (start from conclusions/examples). Concerns HOW arguments are structured, NOT attitudes to change or innovation.
4. Leading — egalitarian (flat, boss is a facilitator, skip levels freely) vs hierarchical (status, titles, deference to seniors, power distance).
5. Deciding — consensual (group agreement before commitment, e.g. ringi) vs top-down (the boss or leader decides and informs).
6. Trusting — task-based (trust from competence and reliability, cognitive trust) vs relationship-based (trust from shared meals, personal bonds, affective trust).
7. Disagreeing — confrontational (open disagreement is healthy) vs avoids confrontation (open disagreement harms harmony).
8. Scheduling — linear-time (punctuality, fixed deadlines, one thing at a time) vs flexible-time (fluid schedules, interruptions, adaptability).

IMPORTANT: many texts are NOT about any of these dimensions. Business-etiquette
protocol (business cards, dress codes, gift wrapping, greetings), GLOBE-style
individualism/collectivism (personal vs team goals, career vs family), long/short-term
orientation, and attitude-to-technology content must be answered "None".
Only assign a dimension when the text is genuinely about that dimension's construct.

Some items genuinely involve TWO dimensions (e.g. a question about leaders whose
options contrast consensual vs unilateral decisions touches Leading AND Deciding).
In that case give both: the dominant one as "dimension" and the other as
"secondary_dimension". Use a secondary ONLY when the text genuinely engages both
constructs — not for vague thematic overlap. Most items have at most one.

You will receive a NUMBERED LIST of texts. Classify EVERY item independently —
the items are unrelated to each other; do not let one influence another.

Answer ONLY with a JSON object of this exact shape, with one entry per input item
and the same "i" numbers you were given:
{"results": [{"i": 1, "dimension": "<Communicating|Evaluating|Persuading|Leading|Deciding|Trusting|Disagreeing|Scheduling|None>", "secondary_dimension": "<same options, or None>", "reason": "<one short sentence>"}]}"""


# --------------------------------------------------------------------------
def load_api_key(env_name: str) -> str:
    key = os.environ.get(env_name)
    if key:
        return key.strip()
    here = os.path.abspath(os.getcwd())
    for _ in range(4):
        env_path = os.path.join(here, ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                line = line.strip()
                if line.startswith(env_name):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        print(f"{env_name} loaded from {env_path}")
                        return val
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    sys.exit(f"\nERROR: no {env_name} found. Add a line to your .env file:\n"
             f"    {env_name}=...\n")


# --------------------------------------------------------------------------
class Pacer:
    """Paces calls using Groq's own x-ratelimit-* headers instead of guessing."""

    def __init__(self, min_gap: float = 2.5):
        self.min_gap = min_gap
        self.last_call = 0.0
        self.limits_printed = False

    def wait_turn(self):
        gap = time.time() - self.last_call
        if gap < self.min_gap:
            time.sleep(self.min_gap - gap)
        self.last_call = time.time()

    @staticmethod
    def parse_duration(value: str) -> float:
        """Groq sends '7.66s', '2m59.56s', '1m', '340ms'. Return seconds."""
        if not value:
            return 0.0
        value = value.strip()
        try:
            secs, mins = 0.0, 0.0
            if "m" in value and "ms" not in value:
                mins_part, _, rest = value.partition("m")
                mins = float(mins_part)
                value = rest
            if value.endswith("ms"):
                secs = float(value[:-2]) / 1000.0
            elif value.endswith("s"):
                secs = float(value[:-1]) if value[:-1] else 0.0
            elif value:
                secs = float(value)
            return mins * 60 + secs
        except ValueError:
            return 0.0

    def observe(self, headers):
        if not self.limits_printed:
            print(f"Groq limits -> requests/day: {headers.get('x-ratelimit-limit-requests')}, "
                  f"tokens/min: {headers.get('x-ratelimit-limit-tokens')}")
            self.limits_printed = True
        try:
            rem_tok = headers.get("x-ratelimit-remaining-tokens")
            if rem_tok is not None and int(rem_tok) < 3000:
                wait = self.parse_duration(
                    headers.get("x-ratelimit-reset-tokens") or "") + 1
                if wait > 0:
                    print(f"    [pacer] token budget low ({rem_tok} left) — pausing {wait:.0f}s")
                    time.sleep(wait)
        except (TypeError, ValueError):
            pass


# --------------------------------------------------------------------------
def build_batch_prompt(texts):
    lines = [f"{i}. {t.strip()[:900]}" for i, t in enumerate(texts, start=1)]
    return f"Classify each of the following {len(texts)} texts.\n\n" + "\n\n".join(lines)


def call_batch(url, model, texts, api_key, pacer, max_retries=6, verbose=False):
    """
    Returns ("ok", [(dim, sec, reason), ...]) aligned with `texts`,
    or ("error", message).
    """
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 90 * len(texts) + 200,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_batch_prompt(texts)},
        ],
    }
    body = json.dumps(payload).encode()
    last_error = "unknown"

    for attempt in range(max_retries):
        pacer.wait_turn()
        req = urllib.request.Request(
            url, data=body,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json",
                     "User-Agent": USER_AGENT,
                     "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                headers = resp.headers
            content = data["choices"][0]["message"]["content"]
            if verbose:
                print("    raw model output:", content.strip()[:600])
            parsed = json.loads(content)
            results = parsed.get("results")
            if not isinstance(results, list):
                raise ValueError("no 'results' array in the answer")

            by_index = {}
            for entry in results:
                try:
                    idx = int(entry.get("i"))
                except (TypeError, ValueError):
                    continue
                dim = str(entry.get("dimension", "None")).strip()
                if dim not in DIMENSIONS:
                    dim = "None"
                sec = str(entry.get("secondary_dimension", "None")).strip()
                if sec not in DIMENSIONS or sec == dim or dim == "None":
                    sec = "None"
                by_index[idx] = (dim, sec, str(entry.get("reason", ""))[:200])

            missing = [i for i in range(1, len(texts) + 1) if i not in by_index]
            if missing:
                raise ValueError(f"model skipped items {missing} of {len(texts)}")

            pacer.observe(headers)
            return "ok", [by_index[i] for i in range(1, len(texts) + 1)]

        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            if e.code == 403 and "1010" in detail:
                sys.exit("\nERROR: Cloudflare 1010 — you are running an OLD copy of this "
                         "script (no USER_AGENT constant). Replace the file.\n")
            if e.code in (401, 403):
                sys.exit(f"\nERROR: HTTP {e.code} — invalid API key or no access to "
                         f"'{model}'.\nServer said: {detail}\n")
            if e.code == 404:
                sys.exit(f"\nERROR: HTTP 404 — model '{model}' does not exist on this "
                         f"provider.\nCheck the provider's model list and pass a valid "
                         f"--model.\n")
            if e.code == 429:
                wait = Pacer.parse_duration(e.headers.get("retry-after", "")) \
                       or min(60, 10 * (attempt + 1))
                if wait > 300:
                    return "error", (
                        f"DAILY TOKEN CAP REACHED — Groq wants {wait/60:.0f} minutes. "
                        f"The free-tier budget for '{model}' is spent for today. "
                        f"Options: wait for the reset, or switch model/provider "
                        f"(--provider cerebras, or --model openai/gpt-oss-20b).")
                print(f"    rate-limited (429) — waiting {wait:.0f}s "
                      f"[attempt {attempt+1}/{max_retries}]", file=sys.stderr)
                time.sleep(wait + 1)
                last_error = "HTTP 429 (rate limit)"
                continue
            if e.code >= 500:
                wait = min(30, 5 * (attempt + 1))
                print(f"    server error {e.code}, retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                last_error = f"HTTP {e.code}"
                continue
            last_error = f"HTTP {e.code}: {detail}"
            print(f"    {last_error}", file=sys.stderr)
            time.sleep(3)

        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"    {last_error} — retrying", file=sys.stderr)
            time.sleep(3)

    return "error", last_error


def detect_text_field(row: dict) -> str:
    for f in ("original_question", "statement", "question", "text"):
        if f in row:
            return f
    raise KeyError(f"No known text field in row keys: {list(row.keys())}")


def row_key(r, text_field):
    return r.get("item_id") or r.get("id") or r[text_field][:80]


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default="groq")
    ap.add_argument("--model", default=None,
                    help="model id; defaults to the provider's recommended one")
    ap.add_argument("--batch-size", type=int, default=10,
                    help="items per API call (default 10; this is what makes the run "
                         "fit inside the free-tier daily token budget)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--all", action="store_true",
                    help="classify ALL rows (replace mode), not just Unmapped")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="one real batched call, printed raw, then stop")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--min-gap", type=float, default=None,
                    help="minimum seconds between API calls; defaults per provider")
    args = ap.parse_args()

    prov = PROVIDERS[args.provider]
    url = prov["url"]
    model = args.model or prov["default_model"]
    min_gap = args.min_gap if args.min_gap is not None else prov["min_gap"]

    rows = [json.loads(l) for l in open(args.input, encoding="utf-8") if l.strip()]
    text_field = detect_text_field(rows[0])
    unmapped = [r for r in rows if r.get("meyer_dimension") == "Unmapped"]
    pool = rows if args.all else unmapped
    todo = pool[: args.limit] if args.limit else pool
    mode = "ALL (replace mode)" if args.all else "Unmapped only (rescue mode)"

    n_calls = -(-len(todo) // args.batch_size)
    est_tokens = n_calls * (700 + args.batch_size * 100)
    print(f"Input rows: {len(rows)} | Unmapped: {len(unmapped)} | mode: {mode} | "
          f"to send: {len(todo)} | text field: '{text_field}'")
    print(f"Provider: {args.provider} | model: {model}")
    print(f"Batching {args.batch_size} items/call -> {n_calls} API calls, "
          f"~{est_tokens:,} tokens estimated.")

    if args.dry_run:
        print("\n--- DRY RUN: first batch prompt ---")
        print(build_batch_prompt([r[text_field] for r in todo[:args.batch_size]])[:1500])
        print("\nNo API calls made.")
        return

    api_key = load_api_key(prov["env"])
    pacer = Pacer(min_gap=min_gap)

    if args.check:
        batch = todo[: args.batch_size]
        print(f"\n--- CHECK: one real batched call ({len(batch)} items) to "
              f"'{model}' via {args.provider} ---")
        status, res = call_batch(url, model, [r[text_field] for r in batch],
                                 api_key, pacer, max_retries=2, verbose=True)
        if status != "ok":
            print(f"\nFAILED: {res}\nDo NOT run the full pass until this is fixed.")
            return
        print()
        for r, (dim, sec, reason) in zip(batch, res):
            print(f"  {r[text_field][:70].strip()}...")
            print(f"     -> {dim}" + (f"  (+{sec})" if sec != "None" else ""))
        print(f"\nAll {len(batch)} items came back aligned. You are good to go.")
        return

    # ---- checkpoint --------------------------------------------------------
    ckpt_path = args.output + ".checkpoint.jsonl"
    done = {}
    if args.resume and os.path.exists(ckpt_path):
        for l in open(ckpt_path, encoding="utf-8"):
            d = json.loads(l)
            done[d["key"]] = d
        print(f"Resuming: {len(done)} items already classified.")
    elif os.path.exists(ckpt_path):
        sys.exit(f"\nERROR: a checkpoint already exists at\n    {ckpt_path}\n"
                 f"Pass --resume to continue it, or DELETE the file to start clean.\n"
                 f"NOTE: a checkpoint from the one-by-one version mixes inference "
                 f"conditions with this batched one. For a clean, uniform run, delete it.\n")

    pending = [r for r in todo if row_key(r, text_field) not in done]
    print(f"Still to classify: {len(pending)}")

    ckpt = open(ckpt_path, "a", encoding="utf-8")
    n_ok = n_none = 0
    failed_batches = 0
    t0 = time.time()

    for start in range(0, len(pending), args.batch_size):
        batch = pending[start:start + args.batch_size]
        status, res = call_batch(url, model, [r[text_field] for r in batch],
                                 api_key, pacer)

        if status == "error":
            failed_batches += 1
            print(f"\n  BATCH FAILED: {res}", file=sys.stderr)
            if n_ok == 0:
                ckpt.close()
                sys.exit("\nABORTED: the very first batch failed and nothing was saved.\n"
                         "Fix the cause above and re-run (try --check first).\n")
            if failed_batches >= 3:
                ckpt.close()
                sys.exit(f"\nSTOPPED after {failed_batches} failed batches.\n"
                         f"{n_ok} items are safely checkpointed. Re-run the SAME command "
                         f"with --resume once the cause is fixed (if it is the daily token "
                         f"cap, that means after 02:00 Spanish time).\n")
            continue

        for r, (dim, sec, reason) in zip(batch, res):
            n_ok += 1
            if dim == "None":
                n_none += 1
            k = row_key(r, text_field)
            ckpt.write(json.dumps({"key": k, "llm_dimension": dim, "llm_secondary": sec,
                                   "llm_reason": reason, "batch_size": args.batch_size},
                                  ensure_ascii=False) + "\n")
            done[k] = {"llm_dimension": dim, "llm_secondary": sec, "llm_reason": reason}
        ckpt.flush()

        elapsed = time.time() - t0
        rate = n_ok / max(elapsed, 1) * 60
        left = (len(pending) - n_ok) / max(rate, 0.1)
        print(f"  {n_ok}/{len(pending)} | none={n_none} | {rate:.0f} items/min | "
              f"~{left:.0f} min left")
    ckpt.close()

    # ---- merge -------------------------------------------------------------
    out_rows = []
    for r in rows:
        r = dict(r)
        rec = done.get(row_key(r, text_field))
        if args.all:
            r["meyer_dimension_rules"] = r.get("meyer_dimension")
            r["mapping_confidence_rules"] = r.get("mapping_confidence")
            if rec:
                r["meyer_dimension"] = (rec["llm_dimension"]
                                        if rec["llm_dimension"] != "None" else "Unmapped")
                r["meyer_dimension_secondary"] = rec.get("llm_secondary", "None")
                r["mapping_confidence"] = "llm"
                r["source"] = "llm"
                r["llm_reason"] = rec["llm_reason"]
            else:
                r["meyer_dimension_secondary"] = "None"
                r["source"] = "rules"
        else:
            if r.get("meyer_dimension") != "Unmapped":
                r["source"] = "rules"
            elif rec and rec["llm_dimension"] != "None":
                r["meyer_dimension"] = rec["llm_dimension"]
                r["meyer_dimension_secondary"] = rec.get("llm_secondary", "None")
                r["mapping_confidence"] = "llm-assisted"
                r["source"] = "llm-assisted"
                r["llm_reason"] = rec["llm_reason"]
            else:
                r["source"] = "rules"
        out_rows.append(r)

    with open(args.output, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- summary (counts real labels, not source tags) ----------------------
    labelled = [r for r in out_rows
                if r.get("source") in ("llm", "llm-assisted")
                and r.get("meyer_dimension") != "Unmapped"]
    n_sec = sum(1 for r in labelled
                if r.get("meyer_dimension_secondary") not in (None, "None"))

    print("\n" + "=" * 62)
    print(f"Classified by the LLM:  {n_ok}")
    print(f"  given a dimension:    {n_ok - n_none}")
    print(f"  genuinely 'None':     {n_none}")
    print(f"  with a SECONDARY:     {n_sec}")
    print(f"Failed batches:         {failed_batches}")
    print("Dimension distribution:",
          dict(Counter(r["meyer_dimension"] for r in labelled)))
    print("=" * 62)

    if n_ok and (n_ok - n_none) == 0:
        print("\nWARNING: every item came back 'None'. Inspect the checkpoint before "
              "trusting this output.")

    if labelled:
        random.seed(42)
        sample = random.sample(labelled, min(40, len(labelled)))
        sample_path = args.output.replace(".jsonl", "_llm_validation_sample.csv")
        with open(sample_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([text_field, "meyer_dimension", "meyer_dimension_secondary",
                        "llm_reason", "human_dimension", "human_agrees", "notes"])
            for r in sample:
                w.writerow([r[text_field], r["meyer_dimension"],
                            r.get("meyer_dimension_secondary", "None"),
                            r.get("llm_reason", ""), "", "", ""])
        print(f"\nValidation sample: {sample_path} ({len(sample)} rows)")
    print(f"Merged output:     {args.output}")


if __name__ == "__main__":
    main()
