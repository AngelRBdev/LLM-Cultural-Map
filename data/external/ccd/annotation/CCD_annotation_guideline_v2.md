# CCD-Bench — Annotation guideline (v2)
### Read this fully BEFORE opening the CSV. Do not annotate from intuition.

Every rule below comes from Meyer, *The Culture Map* (PublicAffairs, 2014) — **not** from
the rule-based mapper, and **not** from any model output. That matters: a guideline
derived from the system we are evaluating would make the ground truth circular and the
evaluation worthless.

---

## ⚠️ Read this first: the old mapper taught us a wrong criterion

The **v1** mapper had no `Unmapped` category. It forced all 369 questions into a
dimension, and **`Scheduling` became its garbage bucket: 143 of 369 questions (39%)
were dumped there** — most of them long-term-orientation content that has nothing to do
with Meyer's Scheduling.

**In this 90-item sample, v1 labelled 33 of them `Scheduling`.**

Round 1 was annotated with those v1 labels visible. So the wrong criterion may have stuck.
If, while annotating, you feel the pull to label something `Scheduling` because it
mentions the future, the long term, careers, or investment — **that is the old mapper
talking, not Meyer.** See rule G2.

---

## What you are labelling

For each item you now see the **question** and its **two answer poles** — the two real
options, with the four generic filler distractors already stripped out.

**Read the poles. They usually carry the construct, not the question.**

    QUESTION: "How do you approach change in your professional life?"   <- tells you nothing
    POLE 1  : "I resist change if it disrupts the immediate workflow."
    POLE 2  : "I adopt change if it benefits long-term growth."          <- now it is clear
              (attitude to change -> GLOBE -> Unmapped)

You are labelling **what the item is about** — not which answer is right, and not which
culture it describes.

---

## The single most important rule

> **`Unmapped` is the correct answer most of the time.**

CCD-Bench was not built from Meyer. It was built from GLOBE/Hofstede constructs. Large
parts of it have **no Meyer dimension at all**. Choosing `Unmapped` is not failing to find
the answer — very often it *is* the answer.

If you catch yourself thinking *"well, it could sort of relate to…"* → `Unmapped`.

---

## The 8 dimensions (Meyer's poles)

| Dimension | Poles | It is about… |
|---|---|---|
| **Communicating** | low-context ↔ high-context | How much meaning is stated vs left to be inferred |
| **Evaluating** | direct ↔ indirect negative feedback | How **criticism** is delivered |
| **Persuading** | principles-first ↔ applications-first | The **structure of an argument** |
| **Leading** | egalitarian ↔ hierarchical | **Power distance**: status, titles, deference |
| **Deciding** | consensual ↔ top-down | **How a decision is reached** |
| **Trusting** | task-based ↔ relationship-based | Where **trust** comes from |
| **Disagreeing** | confrontational ↔ avoids confrontation | Whether **open disagreement** is acceptable |
| **Scheduling** | linear-time ↔ flexible-time | **Time as a tangible thing**: punctuality, deadlines |

---

## Boundary rules — apply these mechanically

### G1. GLOBE / Hofstede content → `Unmapped`
Meyer has **no dimension** for these. If the two poles contrast any of the following, the
answer is `Unmapped`, full stop:

- individualism vs collectivism (personal goals vs team goals, working alone vs in a group)
- long-term vs short-term orientation
- attitude to **risk**, **technology**, **innovation**, or **change**
- uncertainty avoidance
- assertiveness / competitiveness vs cooperativeness
- work–life balance, family vs career
- performance orientation (merit, results, productivity)

### G2. Scheduling ≠ long-term orientation  ← **the big one**
Meyer takes Scheduling from Edward Hall. Monochronic cultures treat time as *tangible* —
saved, spent, wasted. The scale is about **punctuality, deadlines, sequence, one-thing-at-
a-time vs many, and interruptions**.

It is **NOT** about:
- investing for the future
- long-term job satisfaction, career horizons, job security
- whether change is adopted quickly or slowly

All of those are long-term orientation → **G1 → `Unmapped`**.

*(This is the criterion the v1 mapper got wrong 143 times. Do not inherit it.)*

### G3. Leading ≠ Deciding
Meyer keeps these separate on purpose: a culture can be **hierarchical yet consensual**
(Japan) or **egalitarian yet top-down** (USA).

- **Leading** = power distance. Titles, status, deference, skipping levels.
- **Deciding** = the mechanism. Group consensus vs the boss deciding alone.

If the poles contrast **individual vs group work** with no reference to *authority* or to
*how a decision is reached* → individualism/collectivism → **G1 → `Unmapped`**.

### G4. Persuading is about argument structure only
Principles-first vs applications-first: theory before conclusion, or conclusion first.

**NOT** about being persuasive, being open to persuasion, or attitudes to change. If the
poles are not literally about *how an argument or explanation is built* → `Unmapped`.

### G5. Evaluating is specifically about **negative** feedback
Praise, recognition and performance measurement in general are not Evaluating. The scale
is about how **criticism** is given: frank and direct, or softened and private.

### G6. When two dimensions genuinely apply
Put the **dominant** one in `human_dimension` and the second in `notes`. Only when the
item truly engages both (e.g. poles contrasting "the group agrees" vs "the senior manager
decides" → Deciding + Leading). Not for vague overlap.

---

## Protocol

1. **Read this guideline in full before opening the CSV.**
2. Annotate **alone**. Do not discuss any item until both of you are finished.
3. You have **no access** to the mapper's label, the LLM's label, or the confidence tier.
   That is deliberate.
4. Fill in:
   - `human_dimension` → one of the 8, or `Unmapped`
   - `rule_applied` → `G1`–`G6`, or `direct` if the item is plainly about one dimension
   - `notes` → optional; use it for the secondary dimension (G6) or anything hard
5. **Do not go back and revise earlier rows** once you get a feel for the task. Drift is a
   finding; hiding it is not.

Use the exact string `Unmapped` — not `None`, not blank. (Last round we used both, and it
had to be normalised afterwards.)

---

## Why we are redoing this

| Round | κ | Problem |
|---|---|---|
| 1 | 0.68 | Blanca annotated **non-blind** (v1 labels visible) |
| 2 | **0.31** | Both blind, but **stems only** — the item was underdetermined, so we were guessing |
| **3** | — | Blind **and** with the poles. Same information the model gets. |

The round-2 disagreement was not noise. It was systematic: a difference in where we placed
the `Unmapped` threshold, concentrated on GLOBE-vs-Meyer boundary cases — and, on Blanca's
side, an inherited `Scheduling` criterion from v1. That is a guideline problem. This
document is the guideline.

Rounds 1 and 2 are superseded. Round 3 is a single, unified, blind annotation of 90 items
with the poles visible.
