# src/prompts/b3_prompts.py

def get_b3_answering_prompt(scenario: str, question: str, word_limit: int = 150) -> str:
    """
    Generates the prompt for the evaluated model to produce an open-ended analysis.
    """
    return f"""Task: Analyze the following cross-cultural business scenario and provide a comprehensive, rigorous expert analysis addressing the specific question.

Scenario:
{scenario}

Question:
{question}

CRITICAL CONSTRAINTS:
1. Your response must be highly concise, structured, and completely direct.
2. You must strictly adhere to a maximum length of {word_limit} words. Do not exceed this limit under any circumstances.
3. Do not include introductory pleasantries, meta-commentary, or fluff; start immediately with your analytical breakdown.

Expert Analysis:"""


def get_b3_judge_prompt(scenario: str, question: str, rubric: dict, model_answer: str) -> str:
    """
    Generates the highly strict prompt for the judge LLMs to return a precise similarity score.
    """
    rubric_text = "\n".join([f"- {key.capitalize()}: {val}" for key, val in rubric.items()])
    
    return f"""Task: Act as an uncompromising, authoritative referee evaluating an AI-generated answer against a strict gold-standard evaluation rubric.

Context Scenario:
{scenario}

Evaluation Question:
{question}

Gold-Standard Rubric Requirements:
{rubric_text}

AI-Generated Answer to Evaluate:
\"\"\"
{model_answer}
\"\"\"

CRITICAL EVALUATION & FORMAT INSTRUCTIONS:
1. Score the answer from 0.0 to 1.0 based on how comprehensively and accurately it satisfies all structural components of the rubric.
   - 1.0: Perfect alignment; captures the exact essence of identification, explanation, and solution.
   - 0.0: Completely irrelevant, incorrect, or empty.
2. Your output must be ONLY a single floating-point numerical score (e.g., 0.85).
3. Do NOT provide any justification, commentary, markdown wrappers, or surrounding text. Output only the number.

Output numerical score:"""