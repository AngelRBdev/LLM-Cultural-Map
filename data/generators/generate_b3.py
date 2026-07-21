#!/usr/bin/env python3
"""
B3 (Identification) generator — LLM Cultural Map benchmark.

New question type: a short workplace scenario clearly instantiates ONE POLE
of ONE Meyer dimension. The model is asked "Which country is this person most
likely from?" with 4 options (1 correct + 3 distractors at different pole
distances). This tests dimensional understanding from the behaviour side,
complementing B1 (which tests from the country-pair side) and B2 (which tests
from the misunderstanding side).

Gold country: the country with the MOST EXTREME position on the asked pole
for that dimension (highest or lowest on the 0-100 scale), chosen from a
balanced set across GLOBE clusters.

Distractors:
  - near_correct:  same pole, less extreme (sep 15-25 from correct)
  - opposite:      opposite pole, clearly different (sep > 40 from correct)
  - neutral:       near midpoint (40-60 range)

Answer position randomised (no position bias).
Weight: 2 (same as B2, behaviour identification is applied reasoning).
~10-11 items per dimension = 80-88 total.
"""

import json, random, itertools, os
from collections import defaultdict

random.seed(42)
WEIGHT = 2
ITEMS_PER_DIM = 10  # ~80 total across 8 dims

# ── GLOBE clusters ─────────────────────────────────────────────────────────────
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
    "the United Arab Emirates":"Middle East","Qatar":"Middle East",
    "Turkey":"Middle East","Colombia":"Latin America",
    "Portugal":"Latin Europe","Greece":"Latin Europe",
    "Hungary":"Eastern Europe","Czech Republic":"Eastern Europe",
}

# ── Meyer scales ───────────────────────────────────────────────────────────────
SCALES = {
 "Communicating": {
   "the United States":5,"Australia":8,"Canada":12,"the Netherlands":15,
   "Germany":18,"Denmark":20,"the United Kingdom":28,"Poland":35,
   "Italy":50,"Spain":52,"Argentina":57,"Brazil":55,"France":58,
   "Mexico":60,"India":70,"Singapore":72,"Kenya":73,
   "Saudi Arabia":80,"China":85,"South Korea":88,
   "Indonesia":90,"Japan":95,"Ghana":72,"Nigeria":76,
   "the United Arab Emirates":80,"Turkey":72,
   "the Philippines":78,"Thailand":80,"Finland":22,"Sweden":23,
   "Norway":24,"Russia":45,"Austria":17,"Switzerland":16,
   "Israel":30,"Hungary":40,
 },
 "Evaluating": {
   "the Netherlands":5,"Germany":8,"Denmark":10,"Russia":12,
   "Israel":14,"France":25,"Spain":35,"Italy":40,
   "Australia":45,"the United States":50,"Canada":55,
   "the United Kingdom":58,"Brazil":60,"Argentina":62,
   "Mexico":68,"India":72,"Saudi Arabia":75,"Kenya":78,
   "Ghana":80,"China":85,"Indonesia":88,"Japan":92,
   "Thailand":95,"Nigeria":79,
   "the United Arab Emirates":76,"Turkey":65,
   "the Philippines":82,"South Korea":87,"Finland":12,
   "Sweden":15,"Norway":13,"Austria":9,"Switzerland":7,
   "Poland":18,"Hungary":30,"Portugal":55,"Colombia":65,
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
   "the United Arab Emirates":80,"Turkey":74,
   "the Philippines":80,"Thailand":75,"Poland":65,
   "Argentina":62,"Colombia":68,
 },
 "Deciding": {
   "Japan":8,"Sweden":12,"the Netherlands":15,"Denmark":18,
   "Germany":20,"the United Kingdom":50,"the United States":55,
   "Brazil":60,"Italy":62,"France":65,"India":72,
   "China":75,"Russia":80,"Nigeria":82,
   "Finland":14,"Norway":13,"Canada":52,"Australia":50,
   "Spain":60,"Mexico":68,"Argentina":65,"Colombia":70,
   "South Korea":78,"Indonesia":75,"Thailand":72,
   "Saudi Arabia":80,
 },
 "Trusting": {
   "the United States":5,"the Netherlands":12,"Denmark":14,
   "Germany":16,"Australia":18,"the United Kingdom":20,
   "Poland":35,"France":45,"Italy":52,"Spain":55,
   "Mexico":70,"Brazil":72,"India":75,"Japan":78,
   "Russia":80,"Saudi Arabia":82,"China":88,
   "Nigeria":90,"Ghana":85,"Kenya":84,
   "the United Arab Emirates":83,"Turkey":75,
   "the Philippines":82,"Thailand":76,
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
   "the United Arab Emirates":71,"Turkey":58,
   "the Philippines":80,"South Korea":82,
   "Norway":30,"Finland":32,"Austria":16,"Colombia":55,
 },
 "Scheduling": {
   "Switzerland":3,"Germany":5,"Japan":8,"the Netherlands":12,
   "Sweden":13,"Denmark":14,"the United States":18,
   "the United Kingdom":22,"France":40,"Italy":50,"Spain":52,
   "Russia":58,"Brazil":60,"Mexico":62,"China":70,
   "India":75,"Saudi Arabia":78,"Kenya":80,"Nigeria":85,
   "Ghana":82,"the United Arab Emirates":76,"Turkey":70,
   "the Philippines":76,"Thailand":73,
   "Argentina":65,"Colombia":68,
   "Finland":15,"Norway":16,"Australia":20,
   "Canada":22,"Poland":40,"Austria":7,
   "Greece":55,
 },
}

# ── B3 scenario templates (2 per dimension, each with LOW and HIGH pole) ──────
SCENARIOS = {
 "Communicating": [
  {
   "pole": "low",
   "text": "During a client handover call, a project manager lists every assumption, constraint, and open question in explicit detail before moving to the next topic. When a client asks a follow-up question, the manager restates the answer using different words to ensure nothing is left to interpretation.",
   "ambiguity_note": "Could seem like Evaluating (thorough feedback), but the scene is about information transfer, not performance assessment.",
  },
  {
   "pole": "high",
   "text": "In a team debrief, a team lead mentions the project outcome briefly and pauses, allowing the group to absorb the implications without spelling them out. When asked for details, the lead gestures toward the shared document and says 'it is all there between the lines.'",
   "ambiguity_note": "Could seem like Leading (facilitative style), but the scene centres on how information is conveyed, not on authority structure.",
  },
  {
   "pole": "low",
   "text": "A colleague sends a meeting summary that itemises every decision point, assigns owners to every action, and includes a numbered list of next steps with no assumptions left implicit. The email ends with a request for explicit written confirmation from each recipient.",
   "ambiguity_note": "Could seem like Deciding (formalising decisions), but the focus is on the communication medium and explicitness, not on who made the decision.",
  },
  {
   "pole": "high",
   "text": "A senior analyst presents quarterly results without stating a recommendation. After the slide deck ends, the analyst waits, expecting the room to draw the obvious conclusion from the data pattern without it being voiced aloud.",
   "ambiguity_note": "Could seem like Persuading (argument structure), but the scene is about withholding explicit conclusions as a communication norm, not about how an argument is built.",
  },
 ],

 "Evaluating": [
  {
   "pole": "low",
   "text": "After reviewing a junior analyst's report, a line manager calls the analyst directly into a meeting and lists three specific errors, describing each one as a serious problem that needs to be corrected before the report can be shared externally. The manager names the sections, explains what is wrong, and states that this standard of work is not acceptable.",
   "ambiguity_note": "Could seem like Leading (authority exercised), but the scene is purely about how critical feedback is delivered, not about hierarchy or decision authority.",
  },
  {
   "pole": "high",
   "text": "At the end of a presentation, a team leader tells the presenter that the slides were 'quite interesting' and suggests they might want to 'think about the framing a little more.' No specific problem is named, and the session moves on.",
   "ambiguity_note": "Could seem like Communicating (indirect messaging), but the scene is specifically about the delivery of a negative performance signal, not about general information exchange.",
  },
  {
   "pole": "low",
   "text": "During a project retrospective, a manager goes through each deliverable and states plainly which ones missed the brief, naming the responsible team members and describing exactly what fell short. The tone is matter-of-fact, and no positive remarks are made until all the shortcomings have been addressed.",
   "ambiguity_note": "Could seem like Disagreeing (open confrontation), but the scene is a manager assessing performance output, not a peer disagreeing with a proposal.",
  },
  {
   "pole": "high",
   "text": "A supervisor sends a written review that opens with three paragraphs of praise before dedicating one sentence to a concern, phrased as a question: 'Could it be worth revisiting the methodology section?' The email closes with encouragement.",
   "ambiguity_note": "Could seem like Communicating (implicit messaging), but the context is specifically a formal performance evaluation, making Evaluating the primary dimension.",
  },
 ],

 "Persuading": [
  {
   "pole": "low",
   "text": "Opening a strategy session, a consultant states the recommended course of action on the first slide and then spends the remaining time walking through the data and rationale that support it. When questions arise, the consultant answers them before returning to the recommendation already on the table.",
   "ambiguity_note": "Could seem like Leading (controlling the room), but the scene is about argument structure — conclusion first, evidence second — not about authority.",
  },
  {
   "pole": "high",
   "text": "A senior advisor spends the first half of a board presentation tracing the historical context, mapping the competitive landscape, and explaining the theoretical framework before arriving at any recommendation in the final minutes.",
   "ambiguity_note": "Could seem like Scheduling (using time in a certain way), but the scene is explicitly about how an argument is structured to persuade, not about time management.",
  },
  {
   "pole": "low",
   "text": "In a client pitch, a sales lead opens with a single slide that states the proposed solution and its projected outcome, then moves to supporting evidence only when the client asks why. The conclusion is restated at the end as a confirmation of what was said at the start.",
   "ambiguity_note": "Could seem like Communicating (explicit delivery), but the scene is about the logical ordering of a persuasive argument, not about communication style in general.",
  },
  {
   "pole": "high",
   "text": "Presenting a proposal to a steering committee, a project lead methodically explains the problem definition, the theoretical model, the evidence base, and the constraints before proposing any solution. The committee chair asks for the recommendation halfway through, and the lead politely continues with the setup.",
   "ambiguity_note": "Could seem like Leading (handling authority), but the lead's behaviour is about how they structure a persuasive case, not about hierarchy or deference.",
  },
 ],

 "Leading": [
  {
   "pole": "low",
   "text": "A new team member notices an issue that falls under the remit of a director two levels above them. Without informing their immediate line manager, they send the director a direct message summarising the issue and proposing a solution, expecting a quick response.",
   "ambiguity_note": "Could seem like Deciding (taking initiative), but the scene is specifically about how hierarchy is navigated in communication — egalitarian skip-level behaviour — not about who makes the final call.",
  },
  {
   "pole": "high",
   "text": "A junior analyst who disagrees with a project direction does not raise it in the team meeting. Instead, they brief their direct manager after the meeting, who agrees to raise the point upward through the appropriate channel at the next management review.",
   "ambiguity_note": "Could seem like Disagreeing (avoiding open confrontation), but the scene is driven by the norm that issues travel through the chain of command, not by a preference for harmony over conflict.",
  },
  {
   "pole": "low",
   "text": "During an all-hands meeting, the department head invites everyone, including interns, to challenge any item on the agenda. When a junior employee questions a budget decision, the head thanks them and opens it to the floor for debate.",
   "ambiguity_note": "Could seem like Disagreeing (open debate encouraged), but the driver here is the egalitarian leadership philosophy — the head creates the conditions — not a norm about conflict itself.",
  },
  {
   "pole": "high",
   "text": "Before sending a proposal to a client, a team member routes the document through their manager, who makes edits and forwards it to the department head for sign-off before it is sent under the department head's name.",
   "ambiguity_note": "Could seem like Deciding (approval process), but the scene is about communication authority and who is permitted to represent the team externally — a Leading dimension behaviour.",
  },
 ],

 "Deciding": [
  {
   "pole": "low",
   "text": "Before committing to a new supplier, a procurement lead schedules three separate meetings with the finance, legal, and operations teams to collect input. The decision is only announced once all three groups have confirmed they are comfortable with it.",
   "ambiguity_note": "Could seem like Trusting (building relationships), but the scene is about the decision process — who is consulted and when commitment is made — not about how relationships or trust are formed.",
  },
  {
   "pole": "high",
   "text": "After reviewing the options internally, a division head sends a company-wide message announcing the new policy, with a note that the decision has been made and implementation will begin next week. No prior consultation with affected teams is mentioned.",
   "ambiguity_note": "Could seem like Leading (authority exercised), but the scene focuses on the decision-making process — unilateral and announced — not on the communication style of a leader.",
  },
  {
   "pole": "low",
   "text": "A team reopens a discussion that was nominally closed in the previous sprint because two members were not present when the original call was made. The team lead insists that everyone affected should have a chance to weigh in before the plan is treated as final.",
   "ambiguity_note": "Could seem like Communicating (inclusive messaging), but the behaviour is about who must be aligned before a decision is binding — a Deciding dimension construct.",
  },
  {
   "pole": "high",
   "text": "During a product roadmap review, the product director listens to the team's presentations and then announces which features will be prioritised for the next quarter. The team is thanked for the input, and the meeting is closed.",
   "ambiguity_note": "Could seem like Leading (authority style), but the scene focuses on the decision model — one person makes the call after hearing input — not on leadership philosophy or hierarchy.",
  },
 ],

 "Trusting": [
  {
   "pole": "low",
   "text": "When a new vendor proposes a collaboration, a procurement manager responds by requesting case studies, references, and a track record of similar projects before scheduling any meeting. Trust will be extended once the vendor demonstrates relevant competence through evidence.",
   "ambiguity_note": "Could seem like Deciding (evaluation process), but the scene is specifically about how trust is established — through demonstrated performance — not about who decides or how.",
  },
  {
   "pole": "high",
   "text": "Before signing a contract with a new partner, a business development lead proposes three informal dinners spread over two months, saying that the team needs to 'get to know the people' before committing to anything formal.",
   "ambiguity_note": "Could seem like Scheduling (use of time), but the dinners are explicitly positioned as a trust-building mechanism, not a scheduling preference.",
  },
  {
   "pole": "low",
   "text": "A contractor is given increased responsibility after delivering two projects on time and within scope. Their manager explains that the added autonomy comes from the track record they have built, not from how long they have worked together.",
   "ambiguity_note": "Could seem like Evaluating (performance assessed), but the scene is about the basis for extending trust, not about delivering feedback on performance.",
  },
  {
   "pole": "high",
   "text": "At the start of a new cross-team initiative, a project sponsor organises a full-day offsite with no agenda items beyond shared meals and informal conversation. The sponsor says the work itself can only go well once the people involved actually know each other.",
   "ambiguity_note": "Could seem like Scheduling (time used for non-work), but the offsite is framed as trust infrastructure, not as a break from work or a scheduling norm.",
  },
 ],

 "Disagreeing": [
  {
   "pole": "low",
   "text": "During a strategy workshop, a participant directly challenges a colleague's proposal in front of the full group, listing specific objections and asking pointed questions. After a short debate the group moves on, and the two participants have coffee together afterward with no apparent tension.",
   "ambiguity_note": "Could seem like Leading (challenging authority), but the challenger addresses a peer's proposal in a peer forum — the scene is about norms around open debate, not hierarchy.",
  },
  {
   "pole": "high",
   "text": "A team member who disagrees with a project direction says nothing during the group review. Afterward, they speak quietly with the project lead one-on-one, framing their concern as a question rather than an objection.",
   "ambiguity_note": "Could seem like Communicating (indirect messaging), but the behaviour is specifically about how disagreement is handled — privately and softened — not about general communication style.",
  },
  {
   "pole": "low",
   "text": "In a quarterly review, an analyst interrupts the presenter to point out what they see as a flaw in the methodology, stating plainly that the numbers do not support the conclusion. The room engages in a brief back-and-forth before the presenter acknowledges the point.",
   "ambiguity_note": "Could seem like Evaluating (criticising work), but the scene is a peer disagreeing with an interpretation in real time, not a manager delivering a performance assessment.",
  },
  {
   "pole": "high",
   "text": "When a manager announces a change in process that several team members find inefficient, the team nods and says the plan sounds good. Later, a team member sends the manager a short private message suggesting 'one small thing' that might be worth reconsidering.",
   "ambiguity_note": "Could seem like Communicating (indirect channel), but the motivation is specifically conflict avoidance — disagreement is expressed only when it can be done privately and softly.",
  },
 ],

 "Scheduling": [
  {
   "pole": "low",
   "text": "A coordinator sends a meeting agenda forty-eight hours in advance and begins the session by stating that the group has exactly fifty minutes and will follow the agenda in order. When a discussion runs long, the coordinator cuts it off and moves to the next point.",
   "ambiguity_note": "Could seem like Leading (controlling the room), but the behaviour is about time management and schedule adherence, not about authority or hierarchy.",
  },
  {
   "pole": "high",
   "text": "Midway through a scheduled two-hour workshop, the facilitator notices the group is deeply engaged in an unplanned discussion and extends that segment by thirty minutes, dropping two agenda items entirely. The facilitator says the conversation is more valuable than sticking to the original plan.",
   "ambiguity_note": "Could seem like Deciding (making a call), but the decision is entirely about time and schedule flexibility, making Scheduling the primary dimension.",
  },
  {
   "pole": "low",
   "text": "A project manager sends a reminder twenty-four hours before each milestone, and when a team member flags a risk that might delay delivery, the manager immediately begins rescheduling upstream dependencies to protect the original deadline.",
   "ambiguity_note": "Could seem like Deciding (taking action), but the driver is the commitment to the fixed schedule, not a decision-making process.",
  },
  {
   "pole": "high",
   "text": "During a vendor meeting, the host pauses the formal agenda to introduce a colleague who has just joined the office, invites everyone to take a coffee break, and resumes the discussion twenty minutes later than planned without any acknowledgment of the delay.",
   "ambiguity_note": "Could seem like Trusting (relationship-building interruption), but the scene is about how time and schedule are treated — interruptions are normal and unproblematic — not about how trust is built.",
  },
 ],
}

# ── Country selection for distractors ─────────────────────────────────────────
MID = 50

def pick_options(dim, correct_country, pole):
    """Return [correct, near_correct, opposite, neutral] — all from different clusters."""
    pos = SCALES[dim]
    correct_val = pos[correct_country]
    candidates = [(c, v) for c, v in pos.items() if c != correct_country and c in CLUSTER]

    # near_correct: same pole, sep 15-30
    if pole == "low":
        near = [(c, v) for c, v in candidates if v < MID and 15 <= abs(v - correct_val) <= 35]
    else:
        near = [(c, v) for c, v in candidates if v > MID and 15 <= abs(v - correct_val) <= 35]
    near.sort(key=lambda x: abs(x[1] - correct_val))
    near_country = near[0][0] if near else candidates[0][0]

    # opposite: clearly opposite pole, sep > 40
    if pole == "low":
        opp = [(c, v) for c, v in candidates if v > MID + 15 and abs(v - correct_val) > 40]
    else:
        opp = [(c, v) for c, v in candidates if v < MID - 15 and abs(v - correct_val) > 40]
    opp.sort(key=lambda x: -abs(x[1] - correct_val))
    opp_country = opp[0][0] if opp else candidates[-1][0]

    # neutral: near midpoint
    neut = [(c, v) for c, v in candidates
            if 38 <= v <= 62 and c not in (near_country, opp_country)]
    neut.sort(key=lambda x: abs(x[1] - MID))
    neut_country = neut[0][0] if neut else candidates[1][0]

    return [correct_country, near_country, opp_country, neut_country]


def build_b3_items():
    items = []
    item_num = 0

    POLE_EXTREMES = {
        "Communicating": [
            ("the United States", "low"), ("Japan", "high"),
            ("Germany", "low"), ("Indonesia", "high"),
            ("the Netherlands", "low"), ("South Korea", "high"),
            ("Australia", "low"), ("China", "high"),
            ("Finland", "low"), ("Thailand", "high"),
        ],
        "Evaluating": [
            ("Switzerland", "low"), ("Thailand", "high"),
            ("the Netherlands", "low"), ("Japan", "high"),
            ("Denmark", "low"), ("Indonesia", "high"),
            ("Germany", "low"), ("South Korea", "high"),
            ("Finland", "low"), ("China", "high"),
        ],
        "Persuading": [
            ("the United States", "low"), ("Russia", "high"),
            ("Canada", "low"), ("Italy", "high"),
            ("Australia", "low"), ("France", "high"),
            ("the United Kingdom", "low"), ("Germany", "high"),
            ("the Netherlands", "low"), ("Spain", "high"),
        ],
        "Leading": [
            ("Denmark", "low"), ("Japan", "high"),
            ("Sweden", "low"), ("South Korea", "high"),
            ("the Netherlands", "low"), ("Indonesia", "high"),
            ("Norway", "low"), ("China", "high"),
            ("Israel", "low"), ("Nigeria", "high"),
        ],
        "Deciding": [
            ("Japan", "low"), ("Russia", "high"),
            ("Sweden", "low"), ("Nigeria", "high"),
            ("the Netherlands", "low"), ("China", "high"),
            ("Denmark", "low"), ("Saudi Arabia", "high"),
            ("Germany", "low"), ("Mexico", "high"),
        ],
        "Trusting": [
            ("the United States", "low"), ("Nigeria", "high"),
            ("the Netherlands", "low"), ("China", "high"),
            ("Germany", "low"), ("Saudi Arabia", "high"),
            ("Switzerland", "low"), ("Ghana", "high"),
            ("Denmark", "low"), ("Russia", "high"),
        ],
        "Disagreeing": [
            ("Israel", "low"), ("Thailand", "high"),
            ("France", "low"), ("Indonesia", "high"),
            ("Germany", "low"), ("Japan", "high"),
            ("the Netherlands", "low"), ("South Korea", "high"),
            ("Russia", "low"), ("Ghana", "high"),
        ],
        "Scheduling": [
            ("Switzerland", "low"), ("Nigeria", "high"),
            ("Germany", "low"), ("Ghana", "high"),
            ("Japan", "low"), ("Kenya", "high"),
            ("the Netherlands", "low"), ("India", "high"),
            ("Denmark", "low"), ("Saudi Arabia", "high"),
        ],
    }

    for dim, extremes in POLE_EXTREMES.items():
        scenarios = SCENARIOS[dim]

        for i, (correct_country, pole) in enumerate(extremes):
            if correct_country not in SCALES[dim]:
                continue
            if correct_country not in CLUSTER:
                continue

            pole_scenarios = [s for s in scenarios if s["pole"] == pole]
            scen = pole_scenarios[i % len(pole_scenarios)]

            options_list = pick_options(dim, correct_country, pole)
            opts_shuffled = options_list[:]
            random.shuffle(opts_shuffled)
            correct_key = ["A","B","C","D"][opts_shuffled.index(correct_country)]

            options_dict = {k: v for k, v in zip(["A","B","C","D"], opts_shuffled)}

            item_num += 1
            items.append({
                "id": f"B3-{item_num:03d}",
                "block": "B3",
                "dimension": dim,
                "pole": pole,
                "scenario": scen["text"],
                "question": f"A professional from which country is most likely to behave in the way described above?",
                "options": options_dict,
                "correct": correct_key,
                "correct_country": correct_country,
                "cluster_correct": CLUSTER.get(correct_country, "Unknown"),
                "weight": WEIGHT,
                "ambiguity_note": scen["ambiguity_note"],
            })

    return items


def report(items):
    from collections import Counter
    n = len(items)
    cd = Counter(it["correct"] for it in items)
    dims = Counter(it["dimension"] for it in items)
    poles = Counter(it["pole"] for it in items)
    clusters = Counter(it["cluster_correct"] for it in items)
    print(f"\n=== B3: {n} items ===")
    print(f"Correct-answer distribution: {dict(sorted(cd.items()))}")
    print(f"Pole distribution: {dict(poles)}")
    print(f"Per dimension: {dict(dims)}")
    print(f"Correct country clusters: {dict(clusters)}")


if __name__ == "__main__":
    random.seed(42)
    items = build_b3_items()
    report(items)

    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "raw"))
    os.makedirs(raw_dir, exist_ok=True)
    
    path = os.path.join(raw_dir, "b3_dataset.jsonl")
    
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"Successfully written dataset to: {path}")