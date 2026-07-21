# src/run_b2_benchmark.py
import os
import json
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm
from src.prompts.v2_prompts import get_v3_multiple_choice_prompt

def run_b2_benchmark(input_file: str, results_dir: str):
    if not os.path.exists(input_file):
        print(f"[-] Error: File not found at {input_file}")
        return

    os.makedirs(results_dir, exist_ok=True)

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n========== Evaluating Model: {model_name} | Dataset: b2_dataset ==========")
        
        safe_model_name = model_name.replace("/", "_").replace(" ", "_")
        # El archivo de salida adopta exactamente el formato: b2_answers_[nombre_del_modelo].jsonl
        output_file = os.path.join(results_dir, f"b2_answers_{safe_model_name}.jsonl")
        
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for idx, line in enumerate(infile):
                if not line.strip(): continue
                
                data = json.loads(line)
                question_id = data.get("id")
                scenario = data.get("scenario")
                
                # B2 es de opción múltiple, por lo que utiliza las opciones del JSON
                print(f"[{model_name}] Processing question {idx + 1} ({question_id})...")
                
                try:
                    user_prompt = get_v3_multiple_choice_prompt(
                        scenario, 
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

    print(f"\n[+] Benchmark execution finished for dataset: b2_dataset")

if __name__ == "__main__":
    DATA_DIR = "data/raw"
    RESULTS_DIR = "data/results"
    
    target_path = os.path.join(DATA_DIR, "b2_dataset.jsonl")
    run_b2_benchmark(target_path, RESULTS_DIR)