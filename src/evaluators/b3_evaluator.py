# src/evaluators/b3_evaluator.py

import os
import json
import re
from time import sleep  # <-- Correct import
from src.config import MODELS_TO_EVALUATE, B3_EVALUATION_THRESHOLD
from src.prompts.system_roles import EVALUATOR_SYSTEM_ROLE
from src.prompts.b3_prompts import get_b3_answering_prompt, get_b3_judge_prompt
from src.models.llm_client import call_llm

def clean_model_name(model_name: str) -> str:
    return model_name.replace("/", "_").replace(" ", "_")

def extract_score(text: str) -> float:
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", text)
        if match:
            score = float(match.group())
            return max(0.0, min(1.0, score))
    except Exception:
        pass
    return 0.0

def evaluate_b3(raw_data_path: str, results_dir: str) -> None:
    if not os.path.exists(raw_data_path):
        print(f"Error: Could not find data file at {raw_data_path}")
        return

    os.makedirs(results_dir, exist_ok=True)

    for evaluated_model in MODELS_TO_EVALUATE:
        print(f"\n========== Target Model: {evaluated_model} ==========")
        
        safe_model_name = clean_model_name(evaluated_model)
        output_file = os.path.join(results_dir, f"B3_results_{safe_model_name}.jsonl")
        
        judge_models = [m for m in MODELS_TO_EVALUATE if m != evaluated_model]
        
        with open(raw_data_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_idx, line in enumerate(infile):
                if not line.strip():
                    continue
                    
                data = json.loads(line)
                scenario = data.get("scenario", "")
                question = data.get("question", "")
                rubric = data.get("rubric", {})
                
                print(f"[{evaluated_model}] Generating answer {line_idx + 1}...")
                
                try:
                    # 1. Target generates answer
                    answering_prompt = get_b3_answering_prompt(scenario, question)
                    target_response = call_llm(evaluated_model, EVALUATOR_SYSTEM_ROLE, answering_prompt)
                    
                    target_answer = target_response["response_text"]
                    target_time = target_response["time_taken"]
                    
                    sleep(2)
                    
                    # 2. Judges evaluate
                    judge_scores = {}
                    print(f"   -> Sending to {len(judge_models)} judges...")
                    
                    for judge in judge_models:
                        try:
                            judge_prompt = get_b3_judge_prompt(scenario, question, rubric, target_answer)
                            judge_response = call_llm(judge, EVALUATOR_SYSTEM_ROLE, judge_prompt)
                            clean_score = extract_score(judge_response["response_text"])
                            judge_scores[judge] = clean_score
                            
                            sleep(4) 
                            
                        except Exception as judge_e:
                            print(f"      [!] Judge {judge} failed to score. Error: {str(judge_e)}")
                    
                    # If ALL judges failed, we can't score this question
                    if not judge_scores:
                        print("      [!] All judges failed. Skipping question.")
                        continue
                        
                    # 3. Calculate Final Results
                    avg_score = sum(judge_scores.values()) / len(judge_scores)
                    is_correct = bool(avg_score >= B3_EVALUATION_THRESHOLD)
                    
                    print(f"   -> Avg Score: {avg_score:.2f} | Passed: {is_correct}")
                    
                    # 4. Save Record
                    result_record = {
                        **data,
                        "model": evaluated_model,
                        "llm_response_raw": target_answer,
                        "time_taken": target_time,
                        "judge_scores": judge_scores,
                        "average_score": avg_score,
                        "is_correct": is_correct
                    }
                    if "rubric" in result_record:
                        del result_record["rubric"]
                    
                    json.dump(result_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                except Exception as e:
                    print(f"Failed to process question {line_idx + 1}. Error: {e}")
                    
    print("\n========== B3 Complete! ==========")