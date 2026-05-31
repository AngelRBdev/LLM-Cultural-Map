import json
import os

def process_data_files(raw_dir: str, processed_dir: str) -> None:
    """
    Reads raw JSONL files, removes the 'correct' and 'rubric' keys,
    and saves them to the processed directory with '_processed' appended to the filename.
    """
    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)

    # Files to process
    files = [
        "B1_factual.jsonl",
        "B2_relational.jsonl", 
        "B3_reasoning.jsonl"
    ]

    for filename in files:
        raw_path = os.path.join(raw_dir, filename)
        
        # Split filename to insert '_processed' before the extension
        base_name, ext = os.path.splitext(filename)
        processed_filename = f"{base_name}_processed{ext}"
        processed_path = os.path.join(processed_dir, processed_filename)

        # Check if file exists before opening
        if not os.path.exists(raw_path):
            print(f"Warning: File not found -> {raw_path}")
            continue

        with open(raw_path, 'r', encoding='utf-8') as infile, \
             open(processed_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                if not line.strip():
                    continue
                
                # Parse the JSON line
                data = json.loads(line)
                
                # Remove 'correct' key (for B1 and B2)
                if 'correct' in data:
                    del data['correct']
                    
                # Remove 'rubric' key (for B3)
                if 'rubric' in data:
                    del data['rubric']
                
                # Write the cleaned JSON object back exactly as it was
                json.dump(data, outfile, ensure_ascii=False)
                outfile.write('\n')
                
        print(f"Successfully processed: {filename} -> {processed_filename}")

if __name__ == "__main__":
    # Define paths relative to the script location
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RAW_DIRECTORY = os.path.join(BASE_DIR, "data", "raw")
    PROCESSED_DIRECTORY = os.path.join(BASE_DIR, "data", "processed")
    
    print("Starting data processing...")
    process_data_files(RAW_DIRECTORY, PROCESSED_DIRECTORY)
    print("Data processing complete.")