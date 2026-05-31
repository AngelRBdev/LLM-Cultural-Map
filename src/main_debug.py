# src/main_debug.py

import os
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm

def run_step_by_step_debugger():
    print("="*70)
    print("🕵️‍♂️ STARTING INTERACTIVE STEP-BY-STEP DEBUG MODE 🕵️‍♂️")
    print("="*70)

    for model in MODELS_TO_EVALUATE:
        print("\n" + "#"*70)
        print(f"🤖 EVALUATING MODEL: {model}")
        print("#"*70)
        
        # --- TEST 1: BASIC CONNECTION ---
        input("\n[Pause] Press ENTER to test basic connection...")
        try:
            sys_role = "You are a helpful assistant."
            prompt = "Reply exactly with the word: Connected."
            res = call_llm(model, sys_role, prompt)
            print(f"✅ BASIC SUCCESS | The model replied: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ CRITICAL API ERROR | {e}")
            print("⚠️ Skipping this model because it cannot even connect.\n")
            continue

        # --- TEST 2: B1 SIMULATION (FACTUAL) ---
        input("\n[Pause] Press ENTER to test a B1-style question...")
        try:
            sys_role = "Answer ONLY with the letter of the correct option (A or B)."
            prompt = "Is the Earth flat or round?\nA) Flat\nB) Round"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ B1 SUCCESS | The model replied: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ B1 ERROR | {e}")

        # --- TEST 3: B2 SIMULATION (MULTIPLE CHOICE) ---
        input("\n[Pause] Press ENTER to test a B2-style question...")
        try:
            sys_role = "Answer ONLY with the letter of the correct option (A, B, C, or D)."
            prompt = "What is the capital of France?\nA) London\nB) Paris\nC) Rome\nD) Berlin"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ B2 SUCCESS | The model replied: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ B2 ERROR | {e}")

        # --- TEST 4: B3 SIMULATION (JUDGE) ---
        input("\n[Pause] Press ENTER to test the model as a B3 Judge...")
        try:
            sys_role = "You are an impartial judge. Reply ONLY with a float number between 0.0 and 1.0."
            prompt = "Score this response: 'I think communication is key'. Score:"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ B3 SUCCESS | The judge replied: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ B3 ERROR | {e}")

    print("\n========================================================")
    print("🏁 INTERACTIVE DEBUGGING FINISHED")
    print("========================================================")

if __name__ == "__main__":
    run_step_by_step_debugger()