#!/usr/bin/env python3
"""
B2 (Applied) generator — LLM Cultural Map benchmark.

Design (parallel to B1 V2 rebuild):
- Each item describes a cross-cultural workplace misunderstanding involving
  TWO named countries and asks a 4-option MCQ. The correct answer is always
  the culturally-grounded interpretation; distractors are plausible
  non-cultural explanations (administrative, interpersonal, technical).
- SAME SCENARIO TEMPLATE across MULTIPLE COUNTRY PAIRS (the pair_group
  mechanic from B1): the situation is word-for-word identical; only the
  country names change. Consistency within a pair_group is the headline
  metric — a model that truly grasps the dimension answers correctly across
  famous AND obscure pairs.
- ~35% COUNTER-STEREOTYPE items: the two countries come from the SAME
  macro-region but sit on OPPOSITE sides of the dimension. The naive
  "same-region → same-behaviour" shortcut fails on these.
- ANSWER ROTATION: the correct answer is randomly assigned to A/B/C/D
  across items (target ≈ 25% each); distractors are shuffled accordingly.
  This prevents a fixed-position bias.
- Expansion countries (UAE, Qatar, Kuwait, Egypt, Zimbabwe, Tanzania) used
  only in clear cross-region, stereotype-CONSISTENT pairs. They NEVER
  appear in counter-stereotype items.
- Two variants:
    VARIANT A — 1 template per dimension, 12 pairs each, 8 pair_groups.
    VARIANT B — 2 templates per dimension, ~6 pairs each, 16 pair_groups.

Schema fields:
  id, block, dimension, template_id, pair_group,
  scenario, question, options (dict A-D), correct,
  country_low, country_high,   ← which country exhibits the LOW-pole /
  cluster_low, cluster_high,      HIGH-pole behaviour in the scenario
  gold_pole,                   ← which pole (low/high) the scenario depicts
  is_counter_stereotype, uses_expansion, separation, weight
"""

import json, random, itertools
from collections import defaultdict

random.seed(42)
MIN_SEP      = 25
MID          = 50
TOTAL        = 160      # 20 per dimension
COUNTER_TARGET = 0.35
WEIGHT       = 2

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
# Each template defines:
#   situation_low  : one side exhibits LOW-pole behaviour
#   situation_high : one side exhibits HIGH-pole behaviour
#   tpl            : list of 2 template strings, {LOW} = low-pole country,
#                    {HIGH} = high-pole country
#   question       : list of 2 question strings (parallel to tpl)
#   correct_answer : the culturally-grounded explanation (always becomes the
#                    correct option after shuffling)
#   distractors    : 3 plausible non-cultural explanations
# ─────────────────────────────────────────────────────────────────────────────
T = {
 "Communicating": {
  "correct_answer": [
   "The high-context communicator embedded the key information in surrounding context rather than stating it directly, while the low-context communicator expected explicit delivery.",
   "The low-context speaker interpreted silence and indirect phrasing as agreement or compliance; the high-context speaker used implication rather than direct statement.",
  ],
  "distractors": [
   ["The high-context party was still investing in the personal rapport it treats as a precondition for commitment, and used the reply to strengthen that relationship rather than close out the task.",
    "The reply was assembled by several contributors with competing priorities, so the key task instruction ended up buried beneath sections added late for unrelated reasons.",
    "The responder was managing several urgent deadlines that week and addressed the request only briefly at the very end of the message."],
   ["The two sides disagreed about how firm a commitment must be before work begins, with one treating the exchange as final and the other as an opening position still open to negotiation.",
    "The vague phrasing reflected real uncertainty about resourcing, and a clear answer was withheld because approval from a separate department had not yet arrived.",
    "The confirmation was lost in a chain of forwarded emails, so the commitment one side recorded was never actually seen by the person responsible."],
  ],
  "tpl": [
   "{LOW} emails {HIGH}: '{msg_low}' {HIGH} replies with a lengthy message covering context, relationships, and background before briefly addressing the task. {LOW} concludes the reply missed the point.",
   "In a meeting, {LOW} asks {HIGH} directly whether the project will be delivered on time. {HIGH} responds, '{indirect}' {LOW} records this as a confirmed commitment. The deadline passes without delivery.",
  ],
  "question": [
   "Which interpretation best explains both the structure of the reply and {LOW}'s misreading of it?",
   "Which explanation best accounts for the misunderstanding over the deadline?",
  ],
  "msg_low":  ["Project update: attached. Confirm receipt by Friday.",
               "Report needed Tuesday. Please confirm.",
               "Feedback required on proposal by end of week."],
  "indirect": ["We will do our best given the current situation.",
               "Things are progressing; there may be some adjustments needed.",
               "The team is working on it and we hope to have something soon."],
 },

 "Evaluating": {
  "correct_answer": [
   "The disagreement stems from different norms about how critical feedback should be framed and delivered, not from the substance of the assessment itself.",
   "Public criticism may have been experienced as damaging to professional dignity, regardless of the developmental intent behind it.",
  ],
  "distractors": [
   ["The recipient expected a senior colleague to soften judgements as a sign of respect, and read the flat delivery as a status challenge.",
    "The document circulated more widely than intended, so the real objection was its exposure to outside third parties.",
    "The recipient had little time to absorb a dense report and reacted to its tone rather than its points."],
   ["The disengagement followed a private dispute over workload that predated the meeting, so its timing near the feedback was largely coincidental.",
    "The report expected debate to happen openly and read the shift to a group setting as shutting down discussion rather than inviting the kind of challenge they would have preferred.",
    "The specific fixes that were requested happened to be technically contested, and the report stepped back to avoid committing to changes it believed would create new problems further downstream."],
  ],
  "tpl": [
   "A manager from {LOW} delivers detailed written criticism to a colleague from {HIGH}, listing specific failures before any strengths. {HIGH}'s colleague describes the document as unnecessarily harsh, despite agreeing with most of the analysis.",
   "During a team meeting, a supervisor from {LOW} addresses a report from {HIGH}: '{critique}' {HIGH}'s report becomes noticeably less engaged in subsequent discussions.",
  ],
  "question": [
   "What best explains the reaction to the feedback?",
   "What most plausibly explains the change in engagement?",
  ],
  "critique": ["This analysis misses the main point. Please redo it before Friday.",
               "There are three major weaknesses here. We need to fix them.",
               "This section is weak and needs a complete rewrite."],
 },

 "Persuading": {
  "correct_answer": [
   "The two parties prefer different sequences for presenting reasoning: one leads with the conclusion, the other builds the context before revealing it.",
   "The persuasive approach assumed a presentation logic that the audience did not share, causing the substantive content to be received less favorably than expected.",
  ],
  "distractors": [
   ["The executives expected visible seniority behind a recommendation and discounted a proposal made by someone they did not see as holding the authority to make it.",
    "The recommendation conflicted with commitments the leadership team had already made elsewhere, so the proposal was turned down for reasons that had little to do with how it was argued.",
    "The session ran short and the consultant moved on to implementation before the audience had fully absorbed the reasoning, leaving them without a sufficient basis on which to judge the recommendation."],
   ["The counterparts had a fixed agenda and little time, so asking to skip ahead reflected schedule pressure rather than any preference about arguments.",
    "The background material contained figures the audience considered unreliable, so their impatience was really an objection to the data.",
    "The presenter and audience wanted different things: one sought a decision, the other an early exploratory discussion."],
  ],
  "tpl": [
   "A consultant from {LOW} opens a proposal with the recommendation on the second slide and immediately addresses implementation. Executives from {HIGH} listen politely but reject the proposal without detailed feedback.",
   "A presenter from {HIGH} spends the first half of the session on historical context, stakeholder relationships, and systems analysis before reaching the recommendation. Counterparts from {LOW} repeatedly ask to hear the conclusion first.",
  ],
  "question": [
   "Which explanation best fits the outcome?",
   "What most likely explains the gap in communication?",
  ],
 },

 "Leading": {
  "correct_answer": [
   "The egalitarian leadership style removed authority signals that employees in the hierarchical context relied upon to calibrate their own behavior.",
   "Behaviors intended to empower employees were interpreted as an absence of clear direction, because the audience expected visible authority markers to guide action.",
  ],
  "distractors": [
   ["The employees found open challenge confrontational, so they routed concerns through indirect channels that the manager never thought to check or monitor closely.",
    "A reorganization had left reporting lines unclear, so the hesitation reflected real ambiguity about who actually owned each individual task.",
    "The team had long been rewarded for following detailed instructions, and that incentive still discouraged initiative."],
   ["The new structure was introduced without changing the formal approval systems, so employees kept routing decisions upward simply because the old sign-off requirements were still formally in place.",
    "Staff doubted the change would last and kept to established channels to avoid being exposed if leadership quietly reverted to the previous hierarchy within a few months.",
    "After recent errors the unit had become risk-averse, and people sought senior sign-off to protect themselves rather than for direction."],
  ],
  "tpl": [
   "A manager from {LOW} encourages a team in {HIGH} to address her by first name, challenge decisions openly, and act independently. Months later, initiative is low and employees wait for explicit guidance on routine tasks.",
   "A leader from {LOW} takes over a unit in {HIGH} and replaces visible hierarchy markers with flat structures and peer-based decision-making. Employees continue routing decisions through senior leaders before acting.",
  ],
  "question": [
   "What is the most plausible explanation for the outcome?",
   "What most plausibly explains why employees did not adopt the new structure?",
  ],
 },

 "Deciding": {
  "correct_answer": [
   "The two sides attach different meanings to what a formal decision represents: one treats it as the conclusion of a rigorous process, the other as a flexible starting point.",
   "The groups differ on how much alignment should be established before a decision is treated as final and implementation can begin.",
  ],
  "distractors": [
   ["One side distrusted the new information's source and wanted independent checks before acting, so the reluctance was about evidence, not the decision's standing.",
    "Reopening the matter would expose an earlier misjudgement by a senior figure, so the real resistance was about protecting reputations.",
    "The dispute was over who held the authority to reopen a matter that senior figures had already formally closed."],
   ["The continued discussions were required by an internal compliance process, so the pause was a governance step rather than a view of when decisions bind.",
    "The two teams actually disagreed about implementation priorities, and the extra meetings were an attempt to resolve that conflict rather than to broaden agreement on the decision itself.",
    "One side preferred to keep harmony by consulting each person individually before acting, treating open disagreement in the room as something to be avoided rather than surfaced and worked through."],
  ],
  "tpl": [
   "After approving an initiative in a formal meeting, colleagues from {HIGH} resist revisiting it despite new information. Counterparts from {LOW} argue that decisions should remain open to revision as circumstances evolve.",
   "A team from {LOW} expects implementation to begin once the formal meeting concludes. Colleagues from {HIGH} continue holding additional discussions with affected stakeholders before committing to action.",
  ],
  "question": [
   "Which explanation best fits the tension between the two sides?",
   "What is the most likely explanation for the delay in execution?",
  ],
 },

 "Trusting": {
  "correct_answer": [
   "One side may be building trust primarily through demonstrated competence and formal process, while the other requires personal rapport and relationship investment before committing.",
   "The process established formal reliability but omitted the social bonding and personal engagement that the other side treats as a precondition for serious commitment.",
  ],
  "distractors": [
   ["The hesitant side was quietly weighing a competing offer that had arrived during the same period, so the delay reflected an open commercial alternative rather than any need for personal rapport first.",
    "Outstanding legal and compliance checks had not yet cleared, and the counterpart would not finalize until that review concluded, regardless of how far the relationship had developed.",
    "The relationship talk was mainly a tactic to slow the process and extract better terms, not a genuine precondition rooted in how they build trust."],
   ["The competitor simply offered better pricing, and the day of face-to-face meetings coincided with, but did not cause, a decision that ultimately turned on commercial terms rather than rapport.",
    "The onboarding portal had usability problems that slowed the partner's replies, so the lag was a technical obstacle rather than a missing relational step in the approach.",
    "The partner was weighing whether to challenge some contract terms and went quiet while deciding how directly to raise objections they were reluctant to state."],
  ],
  "tpl": [
   "A manager from {LOW} focuses immediately on specifications, pricing, and contract terms. A counterpart from {HIGH} repeatedly steers conversations toward personal background, shared history, and long-term relationship development. Several meetings later, {HIGH} appears reluctant to finalize.",
   "A firm from {LOW} onboards a partner from {HIGH} through an efficient digital portal: forms, compliance checks, and a short video call. {HIGH}'s partner responds slowly afterward. A competitor from a third country that invested a full day in face-to-face meetings wins the next contract.",
  ],
  "question": [
   "Which explanation best accounts for the reluctance to finalize?",
   "What element was most likely missing from the approach by the firm from {LOW}?",
  ],
 },

 "Disagreeing": {
  "correct_answer": [
   "The direct challenger intended open debate as intellectual engagement; the recipient experienced public criticism as a threat to professional standing.",
   "Silence or indirect behavior was incorrectly interpreted as agreement; the actual concerns were communicated through channels that the other side did not recognize.",
  ],
  "distractors": [
   ["The recipient expected criticism to come privately and softened first, and read the blunt public challenge as a judgement on their overall professional competence.",
    "The proposal under challenge was one the recipient had little personal ownership of, so the withdrawal reflected a reduced stake rather than any reaction to the manner of the challenge.",
    "A long-standing rivalry between the two colleagues shaped the whole exchange, so the withdrawal followed that ongoing interpersonal history far more than the directness of this meeting."],
   ["The silent colleagues had no real objections and only found problems once implementation began, making the changes a response to new facts.",
    "The implementation changes were driven by shifting external requirements, so they reflected new conditions rather than withheld concerns.",
    "The quiet side deferred to a settled leadership decision and expected direction from above rather than input."],
  ],
  "tpl": [
   "A professional from {LOW} challenges a colleague from {HIGH}'s proposal in a team meeting, listing logical flaws and inviting the group to improve the idea. {HIGH}'s colleague responds politely but withdraws from subsequent discussions.",
   "A manager from {LOW} asks whether anyone disagrees with a plan. Colleagues from {LOW} raise concerns openly; colleagues from {HIGH} stay silent. During implementation, the {HIGH} side adapts the process in ways that address concerns never mentioned in the meeting.",
  ],
  "question": [
   "What is the most accurate interpretation of the interaction?",
   "What most likely explains the gap between the meeting behavior and the implementation behavior of {HIGH}?",
  ],
 },

 "Scheduling": {
  "correct_answer": [
   "The two sides operate under different assumptions about whether schedules are fixed commitments or adaptable frameworks, leading one side to experience normal flexibility as unreliability.",
   "Activities perceived as schedule disruptions by one side are being treated by the other side as legitimate and necessary components of relationship-building or stakeholder management.",
  ],
  "distractors": [
   ["The team kept reprioritizing because genuinely urgent stakeholder demands arrived throughout the project, so the slippage reflected real external pressure rather than a different philosophy about deadlines.",
    "The milestones were set far too aggressively at the outset, and the adjustments were a rational correction to an unrealistic plan rather than a cultural attitude toward time.",
    "The delays were a deliberate lever to renegotiate scope, with one side using slower delivery to extract concessions rather than acting on any view of time."],
   ["The hosts were building the personal rapport they treat as a precondition for real commitment, so the extra engagements served relationship trust far more than any particular attitude toward the timetable.",
    "An unrelated scheduling conflict on the hosts' side forced the agenda to expand, so the added sessions reflected a logistical constraint rather than a deliberate approach to time.",
    "The visiting manager had underestimated how long each item would take, so the unfinished feeling came from their own planning error rather than the hosts' behavior."],
  ],
  "tpl": [
   "A coordinator from {LOW} establishes fixed milestones for a project with {HIGH}. {HIGH}'s team consistently adjusts timings to accommodate emerging stakeholder priorities. Overall quality remains high but deadlines slip. {LOW} considers introducing contractual penalties.",
   "A manager from {LOW} visits {HIGH} with back-to-back meetings scheduled. Hosts extend discussions, introduce relationship-building conversations, and propose additional social engagements. {LOW}'s manager becomes concerned about unfinished items.",
  ],
  "question": [
   "Which interpretation best explains the recurring pattern?",
   "Which interpretation most accurately explains the situation?",
  ],
 },
}

# ── Pair-validity logic (identical to B1) ────────────────────────────────────
def valid_pairs(dim):
    pos = SCALES[dim]
    out = []
    for a, b in itertools.combinations(pos.keys(), 2):
        sep = abs(pos[a] - pos[b])
        if sep < MIN_SEP:
            continue
        # a = LOW pole, b = HIGH pole  (enforce by convention; swap later if needed)
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

# ── Answer shuffling ──────────────────────────────────────────────────────────
_ANSWER_SLOTS = ["A", "B", "C", "D"]

def shuffle_options(correct_text, distractor_texts):
    """Return (options_dict, correct_key) with the correct answer placed
    randomly so the position distribution converges to 25% each."""
    slot = random.choice(_ANSWER_SLOTS)
    others = [s for s in _ANSWER_SLOTS if s != slot]
    random.shuffle(others)
    random.shuffle(distractor_texts)
    options = {}
    di = 0
    for s in _ANSWER_SLOTS:
        if s == slot:
            options[s] = correct_text
        else:
            options[s] = distractor_texts[di]; di += 1
    return options, slot

# ── Build one item ────────────────────────────────────────────────────────────
def build_item(dim, tpl_idx, pair, item_id, group_id):
    low_c  = pair["low"]
    high_c = pair["high"]

    tpl_data = T[dim]
    template = tpl_data["tpl"][tpl_idx]
    question = tpl_data["question"][tpl_idx]

    # fill optional inline variables (msg_low, indirect, critique, …)
    fill = {}
    for key in ("msg_low", "indirect", "critique"):
        if key in tpl_data:
            fill[key] = random.choice(tpl_data[key])

    scenario = template.format(LOW=low_c, HIGH=high_c, **fill)
    question = question.format(LOW=low_c, HIGH=high_c)

    correct_text   = tpl_data["correct_answer"][tpl_idx]
    distractor_set = list(tpl_data["distractors"][tpl_idx])  # copy

    options, correct_key = shuffle_options(correct_text, distractor_set)

    return {
        "id":                item_id,
        "block":             "B2",
        "dimension":         dim,
        "template_id":       f"{dim[:4].upper()}-T{tpl_idx + 1}",
        "pair_group":        group_id,
        "scenario":          scenario,
        "question":          question,
        "options":           options,
        "correct":           correct_key,
        "country_low":       low_c,
        "country_high":      high_c,
        "cluster_low":       CLUSTER[low_c],
        "cluster_high":      CLUSTER[high_c],
        "gold_pole":         "low_explicit",   # scenario always shows LOW acting first
        "is_counter_stereotype": pair["counter"],
        "uses_expansion":    pair.get("expansion", False),
        "separation":        pair["sep"],
        "weight":            WEIGHT,
    }

# ── Pair selection (greedy, from B1) ─────────────────────────────────────────
def select_pairs(pool, k, cluster_load, country_load, n_counter_target, used):
    chosen = []
    n_counter_target = min(n_counter_target,
                           sum(1 for p in pool if p["counter"]))
    def score(p):
        return (cluster_load[CLUSTER[p["low"]]] + cluster_load[CLUSTER[p["high"]]]
                + 0.5 * (country_load[p["low"]] + country_load[p["high"]])
                - p["sep"] / 100.0)
    counters_taken = 0
    remaining = list(pool)
    while len(chosen) < k and remaining:
        slots_left          = k - len(chosen)
        counters_left_needed = n_counter_target - counters_taken
        cands = [p for p in remaining
                 if frozenset((p["low"], p["high"])) not in used]
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

# ── Main generator ────────────────────────────────────────────────────────────
def generate(n_templates):
    dims          = list(SCALES.keys())
    counts        = per_dim_counts(TOTAL, len(dims))
    cluster_load  = defaultdict(int)
    country_load  = defaultdict(int)
    items         = []

    splits = []
    for di, dim in enumerate(dims):
        pool          = valid_pairs(dim)
        avail_counter = sum(1 for p in pool if p["counter"])
        k             = counts[di]
        if n_templates == 1:
            parts = [(0, k)]
        else:
            k1 = (k + 1) // 2; k2 = k - k1
            parts = [(0, k1), (1, k2)]
        for tpl_idx, kk in parts:
            splits.append({
                "dim": dim, "tpl": tpl_idx, "kk": kk,
                "pool": pool,
                "cap": min(kk, avail_counter),
            })

    # distribute counter-stereotype quota (largest-remainder)
    quota = round(TOTAL * COUNTER_TARGET)
    raw   = [s["kk"] * COUNTER_TARGET for s in splits]
    base  = [min(int(r), splits[i]["cap"]) for i, r in enumerate(raw)]
    assigned = sum(base)
    rema  = sorted(range(len(splits)),
                   key=lambda i: raw[i] - int(raw[i]), reverse=True)
    j = 0
    while assigned < quota and j < len(rema) * 4:
        i = rema[j % len(rema)]
        if base[i] < splits[i]["cap"]:
            base[i] += 1; assigned += 1
        j += 1
    for i, s in enumerate(splits):
        s["ctgt"] = base[i]

    gid          = 0
    used_by_dim  = defaultdict(set)
    for s in splits:
        picks = select_pairs(
            [dict(p) for p in s["pool"]], s["kk"],
            cluster_load, country_load, s["ctgt"],
            used_by_dim[s["dim"]],
        )
        gid += 1
        for p in picks:
            it = build_item(
                s["dim"], s["tpl"], p,
                f"B2-{len(items) + 1:03d}", f"G{gid:02d}",
            )
            items.append(it)
    return items

# ── Report ────────────────────────────────────────────────────────────────────
def report(items, name):
    n   = len(items)
    ctr = sum(1 for i in items if i["is_counter_stereotype"])
    cl  = defaultdict(int)
    for i in items:
        cl[i["cluster_low"]]  += 1
        cl[i["cluster_high"]] += 1
    cd  = defaultdict(int)
    for i in items:
        cd[i["correct"]] += 1
    print(f"\n=== {name}: {n} items ===")
    print(f"Counter-stereotype: {ctr}/{n} ({ctr/n:.0%})")
    print(f"Min separation: {min(i['separation'] for i in items)}")
    print(f"Correct-answer distribution: {dict(sorted(cd.items()))}")
    print("Cluster slots (target ~%.1f each):" % (2 * n / 10))
    for c in sorted(cl):
        print(f"   {c:25s} {cl[c]}")
    per_dim = defaultdict(int)
    for i in items:
        per_dim[i["dimension"]] += 1
    print("Per dimension:", dict(per_dim))

# ── Run ───────────────────────────────────────────────────────────────────────
for variant, ntpl in [("A_1template", 1), ("B_2templates", 2)]:
    random.seed(42)
    items = generate(ntpl)
    report(items, variant)
    path = f"/home/claude/V2_B2_applied_{variant}.jsonl"
    with open(path, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print("written:", path)
