# src/main_b2.py
from src.evaluators.b2_evaluator import evaluate_b2

def main():
    print("==================================================")
    print("🚀 STARTING PHASE B2: RELATIONAL KNOWLEDGE 🚀")
    print("==================================================")
    
    # 1. Point to the 'raw' folder because it has the solutions ('correct')
    input_file_path = "data/raw/B2_relational.jsonl"
    output_directory = "data/results"
    
    # 2. Call the evaluator with the correct name
    evaluate_b2(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ PHASE B2 COMPLETED. Check the data/results/ directory.")

if __name__ == "__main__":
    main()