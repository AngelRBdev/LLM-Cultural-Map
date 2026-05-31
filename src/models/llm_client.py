# src/models/llm_client.py

import time
import litellm
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=20),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception)
)
def call_llm(model_name: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Calls the specified LLM using LiteLLM with automatic retries and a rate-limit throttle.
    Includes a filter to remove <think> tags from reasoning models like Qwen.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    start_time = time.time()
    
    try:
        response = litellm.completion(
            model=model_name,
            messages=messages,
            temperature=0.0
        )
        
        end_time = time.time()
        
        # Automatic 2.5-second delay to prevent saturating free APIs
        time.sleep(2.5)
        
        # 1. Extract the raw text
        raw_text = response.choices[0].message.content.strip()
        
        # 2. Smart filter: If the model "thinks" (e.g., Qwen3), remove the thought process
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()
            
        return {
            "response_text": raw_text,
            "time_taken": end_time - start_time
        }
        
    except Exception as e:
        print(f"\n      [!] API Error intercepted (waiting to retry): {e}")
        raise e