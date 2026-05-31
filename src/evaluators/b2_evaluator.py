# src/evaluators/b2_evaluator.py

import os
import json
from src.config import MODELS_TO_EVALUATE
from src.prompts.system_roles import EVALUATOR_SYSTEM_ROLE
from src.prompts.b2_prompts import get_b2_user_prompt
from src.models.llm_client import call_llm

def clean_model_name(model_name: str) -> str:
    """Replaces slashes and spaces to create safe filenames."""
    return model_name.replace("/", "_").replace(" ", "_")

def evaluate_b2(raw_data_path: str, results_dir: str) -> None:
    """
    Evaluates all models on the B2 (Relational) dataset.
    """
    if not os.path.exists(raw_data_path):
        print(f"Error: Could not find data file at {raw_data_path}")
        return

    os.makedirs(results_dir, exist_ok=True)

    for model in MODELS_TO_EVALUATE:
        print(f"\n========== Starting Evaluation for Model: {model} (B2) ==========")
        
        safe_model_name = clean_model_name(model)
        output_file = os.path.join(results_dir, f"B2_results_{safe_model_name}.jsonl")
        
        with open(raw_data_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_idx, line in enumerate(infile):
                if not line.strip():
                    continue
                    
                data = json.loads(line)
                scenario = data.get("scenario", "")
                question = data.get("question", "")
                options = data.get("options", {})
                correct_answer = data.get("correct", data.get("correct_answer", ""))
                
                # Generate the strict prompt for B2
                user_prompt = get_b2_user_prompt(scenario, question, options)
                
                print(f"[{model}] Processing question {line_idx + 1} ({data.get('id')})...")
                
                try:
                    # Call the LLM
                    api_response = call_llm(
                        model_name=model,
                        system_prompt=EVALUATOR_SYSTEM_ROLE,
                        user_prompt=user_prompt
                    )
                    
                    llm_answer_raw = api_response["response_text"]
                    time_taken = api_response["time_taken"]
                    
                    # Clean the LLM response to get just the letter
                    llm_answer_clean = llm_answer_raw.strip().strip(".'\"").upper()
                    if len(llm_answer_clean) > 0:
                        llm_answer_clean = llm_answer_clean[0]
                    
                    # Compare with the correct answer
                    is_correct = (llm_answer_clean == correct_answer)
                    
                    # Prepare the result record
                    result_record = {
                        **data,
                        "model": model,
                        "llm_response_raw": llm_answer_raw,
                        "llm_response_clean": llm_answer_clean,
                        "is_correct": is_correct,
                        "time_taken": time_taken
                    }
                    
                    # Write to the results file
                    json.dump(result_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                except Exception as e:
                    print(f"Failed to process question {data.get('id')} for model {model}. Error: {e}")
                    
    print("\n========== B2 Evaluation Complete! ==========")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RAW_B2_PATH = os.path.join(BASE_DIR, "data", "raw", "B2_relational.jsonl")
    RESULTS_DIRECTORY = os.path.join(BASE_DIR, "data", "results")
    
    evaluate_b2(RAW_B2_PATH, RESULTS_DIRECTORY)