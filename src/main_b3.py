# src/main_b3.py
from src.evaluators.b3_evaluator import evaluate_b3

def main():
    print("==================================================")
    print("🚀 STARTING PHASE B3: REASONING AND JUDGES 🚀")
    print("==================================================")
    
    # 1. Point to the 'raw' folder to get the base data
    input_file_path = "data/raw/B3_reasoning.jsonl"
    output_directory = "data/results"
    
    # 2. Call the evaluator with the correct name
    evaluate_b3(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ PHASE B3 COMPLETED. Check the data/results/ directory.")

if __name__ == "__main__":
    main()