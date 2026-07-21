#!/usr/bin/env python3
"""
B1 (Factual Yes/No) generator — LLM Cultural Map benchmark.

Design (parallel to B1 V2 rebuild):
- Each item describes a concrete behavioural situation and asks whether a
  professional from country A is more likely to exhibit that behaviour than one from country B,
  given one specific Meyer dimension.
- SAME SCENARIO TEMPLATE across MULTIPLE COUNTRY PAIRS (the pair_group
  mechanic): the situation is word-for-word identical; only the
  country names change.
- ~35% COUNTER-STEREOTYPE items: the two countries come from the SAME
  macro-region but sit on OPPOSITE sides of the dimension.
- ANSWER BALANCING: distributed evenly to prevent position/pole bias.
"""

import json, random, itertools, os
from collections import defaultdict, OrderedDict

random.seed(42)
MIN_SEP      = 25
MID          = 50
TOTAL        = 320      # 40 per dimension
COUNTER_TARGET = 0.35
WEIGHT       = 1

# ── GLOBE clusters ────────────────────────────────────────────────────────────
CLUSTER = {
    "the United States":"Anglo","the United Kingdom":"Anglo",
    "Australia":"Anglo","Canada":"Anglo",
    "Germany":"Germanic Europe","the Netherlands":"Germanic Europe",
    "Switzerland":"Germanic Europe","Austria":"Germanic Europe",
    "Denmark":"Nordic Europe","Sweden":"Nordic Europe",
    "Norway":"Nordic Europe","Finland":"Nordic Europe",
    "France":"Latin Europe","Italy":"Latin Europe",
    "Spain":"Latin Europe","Israel":"Latin Europe",
    "Russia":"Eastern Europe","Poland":"Eastern Europe",
    "Brazil":"Latin America","Mexico":"Latin America",
    "Argentina":"Latin America","Peru":"Latin America",
    "Saudi Arabia":"Middle East","Iran":"Southern Asia",
    "Nigeria":"Sub-Saharan Africa","Ghana":"Sub-Saharan Africa",
    "Kenya":"Sub-Saharan Africa",
    "India":"Southern Asia","Indonesia":"Southern Asia",
    "Thailand":"Southern Asia","the Philippines":"Southern Asia",
    "China":"Confucian Asia","Japan":"Confucian Asia",
    "South Korea":"Confucian Asia","Singapore":"Confucian Asia",
    # expansion
    "the United Arab Emirates":"Middle East","Qatar":"Middle East",
    "Kuwait":"Middle East","Egypt":"Middle East",
    "Zimbabwe":"Sub-Saharan Africa","Tanzania":"Sub-Saharan Africa",
    # additional countries used in SCALES
    "Turkey":"Middle East",
    "Hungary":"Eastern Europe","Czech Republic":"Eastern Europe",
    "Colombia":"Latin America","Venezuela":"Latin America",
    "South Africa":"Sub-Saharan Africa",
    "Morocco":"Middle East",
    "Portugal":"Latin Europe","Greece":"Latin Europe",
    "Lebanon":"Middle East","Pakistan":"Southern Asia",
}

EXPANSION = {
    "the United Arab Emirates","Qatar","Kuwait","Egypt",
    "Zimbabwe","Tanzania",
}

def macro(c):
    cl = CLUSTER[c]
    if cl in ("Anglo","Germanic Europe","Nordic Europe",
               "Latin Europe","Eastern Europe"):  return "WEST"
    if cl in ("Confucian Asia","Southern Asia"):   return "ASIA"
    if cl == "Latin America":                       return "LATAM"
    if cl == "Sub-Saharan Africa":                  return "AFRICA"
    if cl == "Middle East":                         return "MENA"

# ── Meyer scales (0 = far LOW pole, 100 = far HIGH pole) ─────────────────────
SCALES = {
 "Communicating": {
   "the United States":5,"Australia":8,"Canada":12,"the Netherlands":15,
   "Germany":18,"Denmark":20,"the United Kingdom":28,"Poland":35,
   "Italy":50,"Spain":52,"Argentina":57,"Brazil":55,"France":58,
   "Mexico":60,"India":70,"Singapore":72,"Kenya":73,
   "Saudi Arabia":80,"Iran":82,"China":85,"South Korea":88,
   "Indonesia":90,"Japan":95,"Ghana":72,"Nigeria":76,
   "the United Arab Emirates":80,"Qatar":81,"Kuwait":79,
   "Egypt":77,"Zimbabwe":74,"Tanzania":75,
   "the Philippines":78,"Thailand":80,"Finland":22,"Sweden":23,
   "Norway":24,"Russia":45,"Austria":17,"Switzerland":16,
   "Israel":30,"Turkey":72,"Hungary":40,"Morocco":79,
 },
 "Evaluating": {
   "the Netherlands":5,"Germany":8,"Denmark":10,"Russia":12,
   "Israel":14,"France":25,"Spain":35,"Italy":40,
   "Australia":45,"the United States":50,"Canada":55,
   "the United Kingdom":58,"Brazil":60,"Argentina":62,
   "Mexico":68,"India":72,"Saudi Arabia":75,"Kenya":78,
   "Ghana":80,"China":85,"Indonesia":88,"Japan":92,
   "Thailand":95,"Nigeria":79,
   "the United Arab Emirates":76,"Qatar":75,"Kuwait":76,
   "Egypt":73,"Zimbabwe":79,"Tanzania":80,
   "the Philippines":82,"South Korea":87,"Finland":12,
   "Sweden":15,"Norway":13,"Austria":9,"Switzerland":7,
   "Poland":18,"Turkey":65,"Hungary":30,"Morocco":70,
   "Colombia":65,"Czech Republic":20,"Portugal":55,
 },
 "Persuading": {
   "the United States":5,"Canada":12,"Australia":15,
   "the United Kingdom":25,"the Netherlands":35,"Denmark":40,
   "Sweden":42,"Norway":43,"Germany":70,"Spain":75,
   "France":78,"Italy":80,"Russia":85,
   "Brazil":60,"Argentina":58,"Mexico":62,
   "India":72,"Poland":55,"Israel":30,"Finland":38,
   "Turkey":68,"Hungary":60,"Kenya":65,"Nigeria":62,
   "Egypt":70,"South Korea":80,"China":78,
   "Venezuela":60,"South Africa":45,"Colombia":62,
 },
 "Leading": {
   "Denmark":5,"Sweden":8,"Norway":10,"Finland":11,
   "the Netherlands":12,"Israel":14,"Australia":18,
   "Canada":22,"the United States":25,"the United Kingdom":30,
   "Germany":35,"France":55,"Spain":56,"Italy":58,
   "Brazil":60,"Mexico":65,"India":70,"Russia":72,
   "Saudi Arabia":78,"China":80,"Nigeria":82,
   "Indonesia":84,"South Korea":88,"Japan":90,
   "Ghana":78,"Kenya":76,
   "the United Arab Emirates":80,"Qatar":81,"Kuwait":78,
   "Egypt":76,"Zimbabwe":80,"Tanzania":79,
   "the Philippines":80,"Thailand":75,"Turkey":74,
   "Poland":65,"Argentina":62,"Colombia":68,
 },
 "Deciding": {
   "Japan":8,"Sweden":12,"the Netherlands":15,"Denmark":18,
   "Germany":20,"the United Kingdom":50,"the United States":55,
   "Brazil":60,"Italy":62,"France":65,"India":72,
   "China":75,"Russia":80,"Nigeria":82,
   "Finland":14,"Norway":13,"Canada":52,"Australia":50,
   "Spain":60,"Mexico":68,"Argentina":65,"Colombia":70,
   "South Korea":78,"Indonesia":75,"Thailand":72,
   "Saudi Arabia":80,"Kuwait":78,
   "Kenya":60,"Sweden":12,
 },
 "Trusting": {
   "the United States":5,"the Netherlands":12,"Denmark":14,
   "Germany":16,"Australia":18,"the United Kingdom":20,
   "Poland":35,"France":45,"Italy":52,"Spain":55,
   "Mexico":70,"Brazil":72,"India":75,"Japan":78,
   "Russia":80,"Saudi Arabia":82,"China":88,
   "Nigeria":90,"Ghana":85,"Kenya":84,
   "the United Arab Emirates":83,"Qatar":84,"Kuwait":82,
   "Egypt":80,"Zimbabwe":86,"Tanzania":85,
   "the Philippines":82,"Thailand":76,"Turkey":75,
   "Argentina":68,"Colombia":72,
   "Switzerland":8,"Finland":16,"Sweden":14,
   "Canada":18,"Israel":30,
 },
 "Disagreeing": {
   "Israel":5,"France":12,"Germany":15,"the Netherlands":18,
   "Russia":20,"Spain":22,"Denmark":28,"Italy":30,
   "Australia":40,"the United States":45,"Brazil":48,
   "the United Kingdom":50,"Sweden":60,"India":65,
   "Mexico":68,"Saudi Arabia":70,"Ghana":75,"Peru":78,
   "Japan":85,"Indonesia":88,"Thailand":92,
   "Kenya":73,"Nigeria":72,
   "the United Arab Emirates":71,"Qatar":72,"Kuwait":70,
   "Egypt":68,"Zimbabwe":74,"Tanzania":75,
   "the Philippines":80,"South Korea":82,
   "Norway":30,"Finland":32,"Austria":16,
   "Colombia":55,"Turkey":58,
 },
 "Scheduling": {
   "Switzerland":3,"Germany":5,"Japan":8,"the Netherlands":12,
   "Sweden":13,"Denmark":14,"the United States":18,
   "the United Kingdom":22,"France":40,"Italy":50,"Spain":52,
   "Russia":58,"Brazil":60,"Mexico":62,"China":70,
   "India":75,"Saudi Arabia":78,"Kenya":80,"Nigeria":85,
   "Ghana":82,
   "the United Arab Emirates":76,"Qatar":77,"Kuwait":78,
   "Egypt":80,"Zimbabwe":83,"Tanzania":84,
   "the Philippines":76,"Thailand":73,"Turkey":70,
   "Argentina":65,"Colombia":68,"Pakistan":75,
   "Finland":15,"Norway":16,"Australia":20,
   "Canada":22,"Poland":40,"Austria":7,
   "Greece":55,"Lebanon":78,
 },
}

# ── Scenario templates ────────────────────────────────────────────────────────
TB1 = {
 "Communicating": {
  "low": [
   "In a project status meeting, a manager from {A} and a manager from {B} each explain why a deadline slipped. Is the manager from {A} more likely than the manager from {B} to state the point explicitly and spell out the details, leaving little to be inferred? Answer only Yes or No.",
   "A team member from {A} and a team member from {B} each write a short brief for a new colleague. Is the one from {A} more likely than the one from {B} to state the point explicitly and spell out the details, leaving little to be inferred? Answer only Yes or No."
  ],
  "high": [
   "In a project status meeting, a manager from {A} and a manager from {B} each explain why a deadline slipped. Is the manager from {A} more likely than the manager from {B} to communicate the message implicitly and rely on the listener to read between the lines? Answer only Yes or No.",
   "A team member from {A} and a team member from {B} each write a short brief for a new colleague. Is the one from {A} more likely than the one from {B} to communicate the message implicitly and rely on the listener to read between the lines? Answer only Yes or No."
  ]
 },
 "Evaluating": {
  "low": [
   "During a performance review, a supervisor from {A} and a supervisor from {B} each address an underperforming report. Is the supervisor from {A} more likely than the supervisor from {B} to give the negative parts of the feedback bluntly and directly? Answer only Yes or No.",
   "Reviewing a colleague's draft, a reviewer from {A} and a reviewer from {B} each point out serious problems. Is the reviewer from {A} more likely than the reviewer from {B} to give the negative parts of the feedback bluntly and directly? Answer only Yes or No."
  ],
  "high": [
   "During a performance review, a supervisor from {A} and a supervisor from {B} each address an underperforming report. Is the supervisor from {A} more likely than the supervisor from {B} to soften or wrap the criticism so the negative parts are implied rather than stated? Answer only Yes or No.",
   "Reviewing a colleague's draft, a reviewer from {A} and a reviewer from {B} each point out serious problems. Is the reviewer from {A} more likely than the reviewer from {B} to soften or wrap the criticism so the negative parts are implied rather than stated? Answer only Yes or No."
  ]
 },
 "Persuading": {
  "low": [
   "Pitching a proposal to leadership, a presenter from {A} and a presenter from {B} each structure their argument. Is the presenter from {A} more likely than the presenter from {B} to open with the recommendation first and then provide the supporting evidence? Answer only Yes or No.",
   "Explaining a new method to a client, a consultant from {A} and a consultant from {B} each organise their explanation. Is the consultant from {A} more likely than the consultant from {B} to open with the recommendation first and then provide the supporting evidence? Answer only Yes or No."
  ],
  "high": [
   "Pitching a proposal to leadership, a presenter from {A} and a presenter from {B} each structure their argument. Is the presenter from {A} more likely than the presenter from {B} to build the underlying reasoning and theory first and state the conclusion only at the end? Answer only Yes or No.",
   "Explaining a new method to a client, a consultant from {A} and a consultant from {B} each organise their explanation. Is the consultant from {A} more likely than the consultant from {B} to build the underlying reasoning and theory first and state the conclusion only at the end? Answer only Yes or No."
  ]
 },
 "Leading": {
  "low": [
   "Needing a quick answer from a senior executive, an employee from {A} and an employee from {B} each decide how to reach them. Is the employee from {A} more likely than the employee from {B} to skip levels and speak directly to a senior leader without going through their immediate boss? Answer only Yes or No.",
   "In a meeting led by a senior director, a junior staffer from {A} and a junior staffer from {B} each handle a point they want raised. Is the one from {A} more likely than the one from {B} to skip levels and speak directly to a senior leader without going through their immediate boss? Answer only Yes or No."
  ],
  "high": [
   "Needing a quick answer from a senior executive, an employee from {A} and an employee from {B} each decide how to reach them. Is the employee from {A} more likely than the employee from {B} to respect the hierarchy and route the matter through the proper chain of command? Answer only Yes or No.",
   "In a meeting led by a senior director, a junior staffer from {A} and a junior staffer from {B} each handle a point they want raised. Is the one from {A} more likely than the one from {B} to respect the hierarchy and route the matter through the proper chain of command? Answer only Yes or No."
  ]
 },
 "Deciding": {
  "low": [
   "Choosing a new vendor, a team led from {A} and a team led from {B} each run the decision. Is the team from {A} more likely than the team from {B} to seek broad group consensus before the decision is treated as final? Answer only Yes or No.",
   "Setting next quarter's strategy, a department in {A} and a department in {B} each reach their decision. Is the department in {A} more likely than the department in {B} to seek broad group consensus before the decision is treated as final? Answer only Yes or No."
  ],
  "high": [
   "Choosing a new vendor, a team led from {A} and a team led from {B} each run the decision. Is the team from {A} more likely than the team from {B} to let the boss make the call quickly and announce it as the decision? Answer only Yes or No.",
   "Setting next quarter's strategy, a department in {A} and a department in {B} each reach their decision. Is the department in {A} more likely than the department in {B} to let the boss make the call quickly and announce it as the decision? Answer only Yes or No."
  ]
 },
 "Trusting": {
  "low": [
   "Starting a new partnership, a lead from {A} and a lead from {B} each work on earning the other side's trust. Is the lead from {A} more likely than the lead from {B} to build trust mainly through demonstrated competence and reliable delivery? Answer only Yes or No.",
   "Onboarding a key supplier, a manager from {A} and a manager from {B} each approach the relationship. Is the manager from {A} more likely than the manager from {B} to build trust mainly through demonstrated competence and reliable delivery? Answer only Yes or No."
  ],
  "high": [
   "Starting a new partnership, a lead from {A} and a lead from {B} each work on earning the other side's trust. Is the lead from {A} more likely than the lead from {B} to build trust mainly through personal rapport and time spent socialising? Answer only Yes or No.",
   "Onboarding a key supplier, a manager from {A} and a manager from {B} each approach the relationship. Is the manager from {A} more likely than the manager from {B} to build trust mainly through personal rapport and time spent socialising? Answer only Yes or No."
  ]
 },
 "Disagreeing": {
  "low": [
   "In a design review, a member from {A} and a member from {B} each disagree with the lead's proposal. Is the member from {A} more likely than the member from {B} to voice the disagreement openly and debate it in front of the whole group? Answer only Yes or No.",
   "When a manager announces an unpopular decision, an employee from {A} and an employee from {B} each respond. Is the employee from {A} more likely than the employee from {B} to voice the disagreement openly and debate it in front of the whole group? Answer only Yes or No."
  ],
  "high": [
   "In a design review, a member from {A} and a member from {B} each disagree with the lead's proposal. Is the member from {A} more likely than the member from {B} to avoid open confrontation and raise the concern privately or indirectly? Answer only Yes or No.",
   "When a manager announces an unpopular decision, an employee from {A} and an employee from {B} each respond. Is the employee from {A} more likely than the employee from {B} to avoid open confrontation and raise the concern privately or indirectly? Answer only Yes or No."
  ]
 },
 "Scheduling": {
  "low": [
   "Running a multi-step project, a coordinator from {A} and a coordinator from {B} each manage the timeline. Is the coordinator from {A} more likely than the coordinator from {B} to treat the schedule as fixed and expect meetings to start and finish exactly on time? Answer only Yes or No.",
   "Hosting a full day of back-to-back meetings, an organiser from {A} and an organiser from {B} each handle the timing. Is the organiser from {A} more likely than the organiser from {B} to treat the schedule as fixed and expect meetings to start and finish exactly on time? Answer only Yes or No."
  ],
  "high": [
   "Running a multi-step project, a coordinator from {A} and a coordinator from {B} each manage the timeline. Is the coordinator from {A} more likely than the coordinator from {B} to treat the schedule as flexible and adjust timings freely as the day unfolds? Answer only Yes or No.",
   "Hosting a full day of back-to-back meetings, an organiser from {A} and an organiser from {B} each handle the timing. Is the organiser from {A} more likely than the organiser from {B} to treat the schedule as flexible and adjust timings freely as the day unfolds? Answer only Yes or No."
  ]
 }
}

# ── Pair-validity logic ──────────────────────────────────────────────────────
def valid_pairs(dim):
    pos = SCALES[dim]
    out = []
    for a, b in itertools.combinations(pos.keys(), 2):
        sep = abs(pos[a] - pos[b])
        if sep < MIN_SEP:
            continue
        low_c, high_c = (a, b) if pos[a] < pos[b] else (b, a)
        opposite_poles = (pos[low_c] - MID) * (pos[high_c] - MID) < 0
        same_macro     = macro(low_c) == macro(high_c)
        is_exp         = (low_c in EXPANSION) or (high_c in EXPANSION)
        if is_exp:
            if (not opposite_poles) or same_macro:
                continue
            counter = False
        else:
            counter = same_macro and opposite_poles
        out.append({
            "low": low_c, "high": high_c,
            "sep": sep, "counter": counter, "expansion": is_exp,
        })
    return out

def select_pairs(pool, k, cluster_load, country_load, n_counter_target, used):
    chosen = []
    n_counter_target = min(n_counter_target, sum(1 for p in pool if p["counter"]))
    def score(p):
        return (cluster_load[CLUSTER[p["low"]]] + cluster_load[CLUSTER[p["high"]]]
                + 0.5 * (country_load[p["low"]] + country_load[p["high"]])
                - p["sep"] / 100.0)
    counters_taken = 0
    remaining = list(pool)
    while len(chosen) < k and remaining:
        slots_left = k - len(chosen)
        counters_left_needed = n_counter_target - counters_taken
        cands = [p for p in remaining if frozenset((p["low"], p["high"])) not in used]
        if not cands:
            break
        if counters_taken < n_counter_target:
            pref = [p for p in cands if p["counter"]] or cands
        elif (slots_left - counters_left_needed) <= 0:
            pref = [p for p in cands if p["counter"]] or cands
        else:
            pref = [p for p in cands if not p["counter"]] or cands
        pick = min(pref, key=score)
        used.add(frozenset((pick["low"], pick["high"])))
        cluster_load[CLUSTER[pick["low"]]]  += 1
        cluster_load[CLUSTER[pick["high"]]] += 1
        country_load[pick["low"]]  += 1
        country_load[pick["high"]] += 1
        if pick["counter"]:
            counters_taken += 1
        chosen.append(pick)
        remaining.remove(pick)
    return chosen

def per_dim_counts(total, ndim=8):
    base = total // ndim
    rem  = total - base * ndim
    return [base + 1 if i < rem else base for i in range(ndim)]

def build_item(dim, tpl_idx, pair, pole, a_is_low, item_id, group_id):
    low_c, high_c = pair["low"], pair["high"]
    A, B = (low_c, high_c) if a_is_low else (high_c, low_c)
    template = TB1[dim][pole][tpl_idx]
    scenario = template.replace("{A}", A).replace("{B}", B)
    gold = "Yes" if ((pole == "low" and a_is_low) or (pole == "high" and not a_is_low)) else "No"
    return {
        "id": item_id,
        "block": "B1",
        "dimension": dim,
        "template_id": f"{dim[:4].upper()}-T{tpl_idx + 1}",
        "pair_group": group_id,
        "scenario": scenario,
        "country_a": A,
        "country_b": B,
        "cluster_a": CLUSTER[A],
        "cluster_b": CLUSTER[B],
        "gold_answer": gold,
        "is_counter_stereotype": pair["counter"],
        "uses_expansion": pair.get("expansion", False),
        "separation": pair["sep"],
        "pole_asked": pole,
    }

_COMBOS = [("low", True), ("low", False), ("high", True), ("high", False)]
def balanced_combos(n):
    base, rem = divmod(n, 4)
    out = []
    for i, c in enumerate(_COMBOS):
        out += [c] * (base + (1 if i < rem else 0))
    return out

def generate(n_templates):
    dims = list(SCALES.keys())
    counts = per_dim_counts(TOTAL, len(dims))
    cluster_load = defaultdict(int)
    country_load = defaultdict(int)
    items = []

    splits = []
    for di, dim in enumerate(dims):
        pool = valid_pairs(dim)
        avail_counter = sum(1 for p in pool if p["counter"])
        k = counts[di]
        if n_templates == 1:
            parts = [(0, k)]
        else:
            k1 = (k + 1) // 2
            k2 = k - k1
            parts = [(0, k1), (1, k2)]
        for tpl_idx, kk in parts:
            splits.append({"dim": dim, "tpl": tpl_idx, "kk": kk, "pool": pool, "cap": min(kk, avail_counter)})

    quota = round(TOTAL * COUNTER_TARGET)
    raw = [s["kk"] * COUNTER_TARGET for s in splits]
    base = [min(int(r), splits[i]["cap"]) for i, r in enumerate(raw)]
    assigned = sum(base)
    rema = sorted(range(len(splits)), key=lambda i: raw[i] - int(raw[i]), reverse=True)
    j = 0
    while assigned < quota and j < len(rema) * 4:
        i = rema[j % len(rema)]
        if base[i] < splits[i]["cap"]:
            base[i] += 1
            assigned += 1
        j += 1
    for i, s in enumerate(splits):
        s["ctgt"] = base[i]

    gid = 0
    used_by_dim = defaultdict(set)
    split_picks = []
    for s in splits:
        picks = select_pairs([dict(p) for p in s["pool"]], s["kk"], cluster_load, country_load, s["ctgt"], used_by_dim[s["dim"]])
        gid += 1
        split_picks.append((s, gid, picks))

    by_dim = OrderedDict()
    for idx, (s, g, picks) in enumerate(split_picks):
        by_dim.setdefault(s["dim"], []).append(idx)
    for dim, idxs in by_dim.items():
        n_dim = sum(len(split_picks[i][2]) for i in idxs)
        combos = balanced_combos(n_dim)
        random.shuffle(combos)
        ci = 0
        for i in idxs:
            s, g, picks = split_picks[i]
            for p in picks:
                pole, a_is_low = combos[ci]
                ci += 1
                items.append(build_item(s["dim"], s["tpl"], p, pole, a_is_low, f"B1-{len(items) + 1:03d}", f"G{g:02d}"))
    return items

def report(items, name):
    n = len(items)
    ctr = sum(1 for i in items if i["is_counter_stereotype"])
    gold = defaultdict(int)
    pole = defaultdict(int)
    pole_gold = defaultdict(lambda: defaultdict(int))
    perdim = defaultdict(int)
    for i in items:
        gold[i["gold_answer"]] += 1
        pole[i["pole_asked"]] += 1
        pole_gold[i["pole_asked"]][i["gold_answer"]] += 1
        perdim[i["dimension"]] += 1
    leak = sum(max(pole_gold[p].values()) for p in pole_gold)
    print(f"\n=== {name}: {n} items ===")
    print(f"Counter-stereotype: {ctr}/{n} ({ctr/n:.0%})")
    print(f"Min separation: {min(i['separation'] for i in items)}")
    print(f"gold_answer: {dict(gold)}  | pole_asked: {dict(pole)}")
    print(f"pole x gold: {{{', '.join(f'{p}:{dict(pole_gold[p])}' for p in pole_gold)}}}")
    print(f"guess-by-pole accuracy (leak, ~50% = clean): {leak}/{n} = {leak/n:.0%}")
    print(f"Per dimension: {dict(perdim)}")

if __name__ == "__main__":
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "raw"))
    os.makedirs(raw_dir, exist_ok=True)

    random.seed(42)
    items = generate(1)
    report(items, "V2_B1_factual_A_1template")

    path = os.path.join(raw_dir, "b1_dataset.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    print("Successfully written dataset to:", path)