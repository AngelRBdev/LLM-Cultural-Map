# src/main_b3.py
from src.evaluators.b3_evaluator import evaluate_b3

def main():
    print("==================================================")
    print("🚀 INICIANDO FASE B3: RAZONAMIENTO Y JUECES 🚀")
    print("==================================================")
    
    # 1. Apuntamos a la carpeta 'raw' para obtener los datos base
    input_file_path = "data/raw/B3_reasoning.jsonl"
    output_directory = "data/results"
    
    # 2. Llamamos al evaluador con el nombre correcto
    evaluate_b3(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ EJECUCIÓN B3 FINALIZADA. Revisa la carpeta data/results/")

if __name__ == "__main__":
    main()