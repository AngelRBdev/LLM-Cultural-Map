# src/main_debug.py

import os
from src.config import MODELS_TO_EVALUATE
from src.models.llm_client import call_llm

def run_step_by_step_debugger():
    print("="*70)
    print("🕵️‍♂️ INICIANDO MODO DEBUG INTERACTIVO PASO A PASO 🕵️‍♂️")
    print("="*70)

    for model in MODELS_TO_EVALUATE:
        print("\n" + "#"*70)
        print(f"🤖 EVALUANDO MODELO: {model}")
        print("#"*70)
        
        # --- TEST 1: CONEXIÓN BÁSICA ---
        input("\n[Pausa] Presiona ENTER para probar conexión básica...")
        try:
            sys_role = "Eres un asistente útil."
            prompt = "Responde exactamente con la palabra: Conectado."
            res = call_llm(model, sys_role, prompt)
            print(f"✅ ÉXITO BÁSICO | El modelo respondió: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO DE API | {e}")
            print("⚠️ Saltando este modelo porque ni siquiera conecta.\n")
            continue

        # --- TEST 2: SIMULACIÓN B1 (FACTUAL) ---
        input("\n[Pausa] Presiona ENTER para probar una pregunta estilo B1...")
        try:
            sys_role = "Answer ONLY with 'Yes' or 'No'. Do not add any punctuation."
            prompt = "Is it customary to bow in Japan when greeting someone in a business context?"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ ÉXITO B1 | El modelo respondió: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ ERROR EN B1 | {e}")

        # --- TEST 3: SIMULACIÓN B2 (MÚLTIPLE OPCIÓN) ---
        input("\n[Pausa] Presiona ENTER para probar una pregunta estilo B2...")
        try:
            sys_role = "Answer ONLY with the letter of the correct option (A, B, C, or D)."
            prompt = "What is the capital of France?\nA) London\nB) Paris\nC) Rome\nD) Berlin"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ ÉXITO B2 | El modelo respondió: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ ERROR EN B2 | {e}")

        # --- TEST 4: SIMULACIÓN B3 (JUEZ) ---
        input("\n[Pausa] Presiona ENTER para probar al modelo como Juez B3...")
        try:
            sys_role = "You are an impartial judge. Reply ONLY with a float number between 0.0 and 1.0."
            prompt = "Score this response: 'I think communication is key'. Score:"
            res = call_llm(model, sys_role, prompt)
            print(f"✅ ÉXITO B3 | El modelo evaluó con: '{res['response_text']}'")
        except Exception as e:
            print(f"❌ ERROR EN B3 | {e}")

    print("\n" + "="*70)
    print("🏁 DEBUG FINALIZADO. Revisa qué modelos o fases tienen una '❌'")
    print("="*70)

if __name__ == "__main__":
    run_step_by_step_debugger()