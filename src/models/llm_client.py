# src/models/llm_client.py
import time
import litellm
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=20),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception)
)
def call_llm(model_name: str, user_prompt: str) -> dict:
    """
    Calls the LLM using LiteLLM sending ONLY the user prompt.
    Removes <think> tags if the model is a reasoning model.
    """
    # Send only the user role, without a system prompt
    messages = [
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
        time.sleep(2.5)  # Safety throttle
        
        raw_text = response.choices[0].message.content.strip()
        
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()
            
        return {
            "response_text": raw_text,
            "time_taken": end_time - start_time
        }
        
    except Exception as e:
        print(f"\n      [!] API error (retrying): {e}")
        raise e