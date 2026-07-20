# src/prompts/v2_prompts.py

def get_v2_binary_prompt(scenario: str) -> str:
    """
    Strict prompt for variants A and B (Yes/No questions).
    """
    return f"""{scenario}

CRITICAL INSTRUCTIONS:
- Respond with EXACTLY ONE WORD: "Yes" or "No".
- Do NOT include punctuation, quotation marks, spaces, or any explanation.
- Your output must be strictly a single word.

Response:"""


def get_v3_multiple_choice_prompt(scenario: str, question: str, options: dict) -> str:
    """
    Strict prompt for variant C (Multiple choice A, B, C, D).
    """
    options_text = "\n".join([f"{key}: {val}" for key, val in options.items()])
    
    return f"""Scenario:
{scenario}

Question:
{question}

Options:
{options_text}

CRITICAL FORMAT INSTRUCTIONS:
1. Respond with EXACTLY ONE CHARACTER: the uppercase letter corresponding to the correct option (A, B, C, or D).
2. Do NOT include punctuation, quotation marks, spaces, or any explanation.
3. Your output must be strictly a single character.

Response:"""