# src/main_run_benchmark.py
import os
import json
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm
from src.prompts.v2_prompts import get_v2_binary_prompt, get_v3_multiple_choice_prompt

def run_benchmark(input_file: str, results_dir: str):
    if not os.path.exists(input_file):
        print(f"[-] Error: File not found at {input_file}")
        return

    os.makedirs(results_dir, exist_ok=True)
    base_name = os.path.basename(input_file).replace(".jsonl", "")

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n========== Evaluating Model: {model_name} | Dataset: {base_name} ==========")
        
        safe_model_name = model_name.replace("/", "_").replace(" ", "_")
        # The output filename will include the dataset name to prevent mixing
        output_file = os.path.join(results_dir, f"raw_answers_{base_name}_{safe_model_name}.jsonl")
        
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for idx, line in enumerate(infile):
                if not line.strip(): continue
                
                data = json.loads(line)
                question_id = data.get("id")
                scenario = data.get("scenario")
                
                # DYNAMIC DETECTION: If JSON contains the key 'options', it is multiple choice
                is_multiple_choice = "options" in data
                
                print(f"[{model_name}] Processing question {idx + 1} ({question_id})...")
                
                try:
                    if is_multiple_choice:
                        user_prompt = get_v3_multiple_choice_prompt(scenario, data.get("question"), data.get("options"))
                    else:
                        user_prompt = get_v2_binary_prompt(scenario)
                        
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
                    print(f"   [!] Error on question {question_id}: {e}")
                    error_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": f"ERROR: {str(e)}",
                        "time_taken": 0.0
                    }
                    json.dump(error_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    continue

    print(f"\n[+] Benchmark execution finished for dataset: {base_name}")

if __name__ == "__main__":
    DATA_DIR = "data/raw"
    RESULTS_DIR = "data/results"
    
    # List of the 3 native datasets in the raw folder
    DATASETS = [
        "V2_B1_factual_A_1template.jsonl",
        "V2_B1_factual_B_2templates.jsonl",
        "V2_B3_factual_C_relation.jsonl"
    ]
    
    # Loop to run all 3 datasets sequentially across the 5 models
    for ds in DATASETS:
        target_path = os.path.join(DATA_DIR, ds)
        run_benchmark(target_path, RESULTS_DIR)