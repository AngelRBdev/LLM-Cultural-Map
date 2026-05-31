# src/evaluators/b1_evaluator.py

import os
import json
from src.config import MODELS_TO_EVALUATE
from src.prompts.system_roles import EVALUATOR_SYSTEM_ROLE
from src.prompts.b1_prompts import get_b1_user_prompt
from src.models.llm_client import call_llm

def clean_model_name(model_name: str) -> str:
    return model_name.replace("/", "_").replace(" ", "_")

def evaluate_b1(raw_data_path: str, results_dir: str) -> None:
    if not os.path.exists(raw_data_path):
        print(f"❌ Error: Data file not found at {raw_data_path}")
        return

    os.makedirs(results_dir, exist_ok=True)

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n========== Evaluating Model on B1: {model_name} ==========")
        
        safe_model_name = clean_model_name(model_name)
        output_file = os.path.join(results_dir, f"B1_results_{safe_model_name}.jsonl")
        
        with open(raw_data_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_idx, line in enumerate(infile):
                if not line.strip(): continue
                    
                data = json.loads(line)
                question_id = data.get("id", f"B1_{line_idx}")
                question_text = data.get("question", "")
                options = data.get("options", {})
                correct_answer = data.get("correct", data.get("correct_answer", ""))
                
                print(f"[{model_name}] Processing question {line_idx + 1} ({question_id})...")
                
                try:
                    user_prompt = get_b1_user_prompt(question_text, options)
                    api_response = call_llm(model_name, EVALUATOR_SYSTEM_ROLE, user_prompt)
                    
                    llm_answer = api_response["response_text"]
                    time_taken = api_response["time_taken"]
                    
                    is_correct = False
                    if llm_answer and llm_answer.strip():
                        first_char = llm_answer.strip()[0].upper()
                        is_correct = (first_char == correct_answer.upper())
                    
                    result_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": llm_answer,
                        "time_taken": time_taken,
                        "is_correct": is_correct
                    }
                    
                    # Save immediately to the JSONL
                    json.dump(result_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                except Exception as e:
                    # If the model runs out of tokens or times out, this failsafe triggers:
                    print(f"      ⚠️ skipping question {question_id} due to API error: {e}")
                    
                    # Save an error record so the JSONL file does not get corrupted
                    error_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": f"API_ERROR: {str(e)}",
                        "time_taken": 0.0,
                        "is_correct": False
                    }
                    json.dump(error_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                    # IMPORTANT: continue with the next question instead of breaking the loop
                    continue
                    
    print("\n========== Phase B1 Completed ==========")