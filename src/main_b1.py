# src/main_b1.py
from src.evaluators.b1_evaluator import evaluate_b1

def main():
    print("==================================================")
    print("🚀 INICIANDO FASE B1: CONOCIMIENTO FACTUAL 🚀")
    print("==================================================")
    
    # 1. Apuntamos a la carpeta 'raw' porque ES LA ÚNICA QUE TIENE LAS SOLUCIONES
    input_file_path = "data/raw/B1_factual.jsonl"
    output_directory = "data/results"
    
    # 2. Llamamos al evaluador
    evaluate_b1(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ EJECUCIÓN B1 FINALIZADA. Revisa la carpeta data/results/")

if __name__ == "__main__":
    main()