# src/run_b3_variant_c.py
import os
import json
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm
from src.prompts.v2_prompts import get_v3_multiple_choice_prompt

def run_variant_c():
    INPUT_FILE = "data/raw/V2_B3_factual_C_relation.jsonl"
    RESULTS_DIR = "data/results"
    
    if not os.path.exists(INPUT_FILE):
        print(f"[-] Error: File not found at {INPUT_FILE}")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("==================================================")
    print("🚀 STARTING INPUT: VARIANT C (MULTIPLE CHOICE)")
    print("==================================================")

    for model_name in MODELS_TO_EVALUATE:
        print(f"\nEvaluating Model: {model_name}")
        safe_model_name = model_name.replace("/", "_").replace(" ", "_")
        output_file = os.path.join(RESULTS_DIR, f"raw_answers_C_relation_{safe_model_name}.jsonl")
        
        with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for idx, line in enumerate(infile):
                if not line.strip(): continue
                data = json.loads(line)
                
                print(f"[{model_name}] Question {idx + 1} ({data.get('id')})...")
                try:
                    # Pass the scenario, question, and option dictionary (A, B, C, D) in a structured way
                    user_prompt = get_v3_multiple_choice_prompt(
                        data.get("scenario"), 
                        data.get("question"), 
                        data.get("options")
                    )
                    api_response = call_llm(model_name, user_prompt)
                    
                    result_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": api_response["response_text"],
                        "time_taken": api_response["time_taken"]
                    }
                    json.dump(result_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                except Exception as e:
                    print(f"   [!] Error in {data.get('id')}: {e}")
                    error_record = {**data, "model": model_name, "llm_response_raw": f"ERROR: {e}", "time_taken": 0.0}
                    json.dump(error_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    continue

if __name__ == "__main__":
    run_variant_c()