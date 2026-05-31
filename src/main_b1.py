# src/main_b1.py
from src.evaluators.b1_evaluator import evaluate_b1

def main():
    print("==================================================")
    print("🚀 STARTING PHASE B1: FACTUAL KNOWLEDGE 🚀")
    print("==================================================")
    
    # 1. Point to the 'raw' folder because IT IS THE ONLY ONE WITH THE SOLUTIONS
    input_file_path = "data/raw/B1_factual.jsonl"
    output_directory = "data/results"
    
    # 2. Call the evaluator
    evaluate_b1(raw_data_path=input_file_path, results_dir=output_directory)
    
    print("\n✅ PHASE B1 COMPLETED. Check the data/results/ directory.")

if __name__ == "__main__":
    main()