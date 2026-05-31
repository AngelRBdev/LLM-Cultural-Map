# src/prompts/b2_prompts.py

def get_b2_user_prompt(scenario: str, question: str, options: dict) -> str:
    """
    Generates a strict prompt for B2 relational multiple-choice evaluation.
    """
    options_text = "\n".join([f"{key}: {val}" for key, val in options.items()])
    
    return f"""Task: Analyze the cross-cultural business scenario provided below and determine the most accurate interpretation based on cultural dimension principles.

Scenario:
{scenario}

Question:
{question}

Options:
{options_text}

CRITICAL FORMAT INSTRUCTIONS:
1. Respond with EXACTLY ONE CHARACTER: the uppercase letter corresponding to the correct option (e.g., A, B, C, or D).
2. Do NOT include any punctuation, quotation marks, spaces, explanations, or conversational filler.
3. Failure to comply with this single-character rule will result in an immediate parsing error.

Output character:"""