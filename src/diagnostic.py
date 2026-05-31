# src/diagnostic.py

import os
from dotenv import load_dotenv
import litellm

def run_diagnostics():
    print("="*50)
    print("🩺 STARTING SYSTEM DIAGNOSTICS 🩺")
    print("="*50)

    # 1. Verify Environment Variables
    print("\n[TEST 1] Loading environment variables...")
    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY detected (Ends in ...{groq_key[-4:]})")
    else:
        print("❌ ERROR: GROQ_API_KEY not found in .env file")

    # 2. Verify Paths and Files
    print("\n[TEST 2] Verifying data files...")
    # Ensure it searches from the folder where this script is located (src)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    b1_path = os.path.join(raw_dir, "B1_factual.jsonl")

    print(f"Expected data path: {raw_dir}")
    if not os.path.exists(raw_dir):
        print("❌ ERROR: 'data/raw' folder DOES NOT exist or Python cannot find it.")
    else:
        print("✅ 'data/raw' folder found.")
        
        if not os.path.exists(b1_path):
            print(f"❌ ERROR: The file '{b1_path}' DOES NOT exist.")
        else:
            print("✅ File 'B1_factual.jsonl' found.")
            try:
                with open(b1_path, 'r', encoding='utf-8') as f:
                    lineas = f.readlines()
                    print(f"✅ The B1 file has {len(lineas)} questions.")
                    if len(lineas) == 0:
                        print("❌ ERROR: The file is empty.")
            except Exception as e:
                print(f"❌ ERROR trying to read the file: {e}")

    # 3. Verify API Connection (The most stable and fast model)
    print("\n[TEST 3] Testing real connection with Groq API...")
    try:
        response = litellm.completion(
            model="groq/llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Reply only with the word 'Connected'."}],
            max_tokens=10
        )
        respuesta_texto = response.choices[0].message.content.strip()
        print(f"✅ Connection successful. The model says: '{respuesta_texto}'")
    except Exception as e:
        print(f"❌ ERROR connecting to API: {e}")

if __name__ == "__main__":
    run_diagnostics()