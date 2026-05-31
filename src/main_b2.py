# src/main_b2.py
from src.evaluators.b2_evaluator import evaluate_b2

def main():
    print("==================================================")
    print("🚀 INICIANDO FASE B2: CONOCIMIENTO RELACIONAL 🚀")
    print("==================================================")
    
    # 1. Apuntamos a la carpeta 'raw' porque tiene las soluciones ('correct')
    input_file_path = "data/raw/B2_relational.jsonl"
    output_directory = "data/results"
    
    # 2. Llamamos al evaluador con el nombre correcto
    evaluate_b2(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ EJECUCIÓN B2 FINALIZADA. Revisa la carpeta data/results/")

if __name__ == "__main__":
    main()