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
        print(f"❌ Error: No se encontró el archivo de datos en {raw_data_path}")
        return

    os.makedirs(results_dir, exist_ok=True)

    for model_name in MODELS_TO_EVALUATE:
        print(f"\n========== Evaluando Modelo en B1: {model_name} ==========")
        
        safe_model_name = clean_model_name(model_name)
        output_file = os.path.join(results_dir, f"B1_results_{safe_model_name}.jsonl")
        
        with open(raw_data_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_idx, line in enumerate(infile):
                if not line.strip():
                    continue
                    
                data = json.loads(line)
                question_id = data.get("question_id", f"B1_{line_idx}")
                question_text = data.get("question", "")
                options = data.get("options", {})
                correct_answer = data.get("correct", data.get("correct_answer", ""))
                
                print(f"[{model_name}] Procesando pregunta {line_idx + 1} ({question_id})...")
                
                # Modificación Clave: Bloque try/except individual por pregunta para evitar congelamientos
                try:
                    user_prompt = get_b1_user_prompt(question_text, options)
                    
                    # Llamada al cliente LLM
                    api_response = call_llm(
                        model_name=model_name,
                        system_prompt=EVALUATOR_SYSTEM_ROLE,
                        user_prompt=user_prompt
                    )
                    
                    llm_answer = api_response["response_text"]
                    time_taken = api_response["time_taken"]
                    
                    # Verificamos si acertó (evaluación estricta de la primera letra)
                    is_correct = False
                    if llm_answer and llm_answer.strip():
                        first_char = llm_answer.strip()[0].upper()
                        is_correct = (first_char == correct_answer.upper())
                    
                    # Estructuramos el resultado exitoso
                    result_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": llm_answer,
                        "time_taken": time_taken,
                        "is_correct": is_correct
                    }
                    
                    # Guardamos inmediatamente en el JSONL
                    json.dump(result_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                except Exception as e:
                    # Si el modelo se queda sin tokens o da timeout, se activa este salvavidas:
                    print(f"      ⚠️ saltando pregunta {question_id} debido a un error de API: {e}")
                    
                    # Guardamos un registro de error para que el archivo JSONL no quede corrupto
                    error_record = {
                        **data,
                        "model": model_name,
                        "llm_response_raw": f"ERROR_API: {str(e)}",
                        "time_taken": 0.0,
                        "is_correct": False
                    }
                    json.dump(error_record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    
                    # IMPORTANTE: continua con la siguiente pregunta en vez de romper el bucle
                    continue
                    
    print("\n========== Fase B1 Completada ==========")