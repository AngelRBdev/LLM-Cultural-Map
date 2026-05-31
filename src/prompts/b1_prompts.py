# src/prompts/b1_prompts.py

def get_b1_user_prompt(question: str, options: dict) -> str:
    """
    Generates a highly strict prompt for B1 factual binary evaluation.
    """
    options_text = "\n".join([f"{key}: {val}" for key, val in options.items()])
    
    return f"""Task: Answer the following factual question regarding global cross-cultural business norms.

Question:
{question}

Options:
{options_text}

CRITICAL FORMAT INSTRUCTIONS:
1. Respond with EXACTLY ONE CHARACTER: the uppercase letter corresponding to the correct option (A or B).
2. Do NOT include any punctuation, quotation marks, spaces, explanations, or introductory/concluding remarks.
3. Any response containing more than a single letter will cause the parsing engine to fail.

Output character:"""