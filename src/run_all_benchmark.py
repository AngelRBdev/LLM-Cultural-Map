# src/run_all_benchmark.py
import os
import json
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm
from src.prompts.v2_prompts import get_v2_binary_prompt, get_v3_multiple_choice_prompt
from src.main_evaluate_report import generate_json_report

def run_dataset_evaluation(input_file: str, results_dir: str):
    """
    Orchestrates the evaluation of a JSONL file for the 5 language models.
    """
    if not os.path.exists(input_file):
        print(f"[-] Error: Data file not found at {input_file}")
        return

    base_name = os.path.basename(input_file).replace(".jsonl", "")
    print(f"\n🚀 Starting dataset processing: {base_name}")
    print("-" * 60)

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n[+] Evaluating Model: {model_name}")
        safe_model_name = model_name.replace("/", "_").replace(" ", "_")
        output_file = os.path.join(results_dir, f"raw_answers_{base_name}_{safe_model_name}.jsonl")
        
        # Write mode used to ensure a fresh start
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for idx, line in enumerate(infile):
                if not line.strip(): continue
                data = json.loads(line)
                
                question_id = data.get("id")
                scenario = data.get("scenario")
                is_multiple_choice = "options" in data  # Check if it is Variant C
                
                print(f"    -> Question {idx + 1} ({question_id})...")
                
                try:
                    if is_multiple_choice:
                        user_prompt = get_v3_multiple_choice_prompt(
                            scenario, 
                            data.get("question"), 
                            data.get("options")
                        )
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
                    print(f"    [!] Error in question {question_id}: {e}")
                    error_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": f"ERROR: {str(e)}",
                        "time_taken": 0.0
                    }
                    json.dump(error_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    continue

def main():
    DATA_DIR = "data/raw"
    RESULTS_DIR = "data/results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("==================================================================")
    print("🤖 STARTING AUTOMATIC BENCHMARK ORCHESTRATOR")
    print("==================================================================")

    # Define exact paths for the 3 native datasets
    DATASETS = [
        "V2_B1_factual_A_1template.jsonl",
        "V2_B1_factual_B_2templates.jsonl",
        "V2_B3_factual_C_relation.jsonl"
    ]

    # Sequential loop protected against catastrophic failures
    for ds in DATASETS:
        target_path = os.path.join(DATA_DIR, ds)
        try:
            run_dataset_evaluation(target_path, RESULTS_DIR)
        except Exception as main_e:
            print(f"\n[❌] Critical error processing dataset {ds}: {main_e}")
            print("Skipping to the next dataset to avoid stopping execution...\n")
            continue

    print("\n==================================================================")
    print("📊 ALL RESPONSES CAPTURED. GENERATING FINAL REPORT...")
    print("==================================================================")
    
    try:
        generate_json_report(RESULTS_DIR)
    except Exception as rep_e:
        print(f"[-] Could not consolidate final JSON: {rep_e}")

    print("\n[✅] Process finished completely.")

if __name__ == "__main__":
    main()