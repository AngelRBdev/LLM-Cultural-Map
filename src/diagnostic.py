# src/diagnostic.py

import os
from dotenv import load_dotenv
import litellm

def run_diagnostics():
    print("="*50)
    print("🩺 INICIANDO DIAGNÓSTICO DEL SISTEMA 🩺")
    print("="*50)

    # 1. Verificar Variables de Entorno
    print("\n[TEST 1] Cargando variables de entorno...")
    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY detectada (Termina en ...{groq_key[-4:]})")
    else:
        print("❌ ERROR: No se encontró GROQ_API_KEY en el archivo .env")

    # 2. Verificar Rutas y Archivos
    print("\n[TEST 2] Verificando archivos de datos...")
    # Aseguramos que busque desde la carpeta donde está este script (src)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    b1_path = os.path.join(raw_dir, "B1_factual.jsonl")

    print(f"Ruta esperada para los datos: {raw_dir}")
    if not os.path.exists(raw_dir):
        print("❌ ERROR: La carpeta 'data/raw' NO existe o Python no la encuentra.")
    else:
        print("✅ Carpeta 'data/raw' encontrada.")
        
        if not os.path.exists(b1_path):
            print(f"❌ ERROR: El archivo '{b1_path}' NO existe.")
        else:
            print("✅ Archivo 'B1_factual.jsonl' encontrado.")
            try:
                with open(b1_path, 'r', encoding='utf-8') as f:
                    lineas = f.readlines()
                    print(f"✅ El archivo B1 tiene {len(lineas)} preguntas.")
                    if len(lineas) == 0:
                        print("❌ ERROR: El archivo está vacío.")
            except Exception as e:
                print(f"❌ ERROR al intentar leer el archivo: {e}")

    # 3. Verificar Conexión a la API (El modelo más estable y rápido)
    print("\n[TEST 3] Probando conexión real con la API de Groq...")
    try:
        response = litellm.completion(
            model="groq/llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Responde solo con la palabra 'Conectado'."}],
            max_tokens=10
        )
        respuesta_texto = response.choices[0].message.content.strip()
        print(f"✅ Conexión exitosa. El modelo dice: '{respuesta_texto}'")
    except Exception as e:
        print(f"❌ ERROR DE API: Falló la conexión con Groq. Detalles: {e}")

    print("\n" + "="*50)
    print("🏁 DIAGNÓSTICO FINALIZADO 🏁")
    print("="*50)

if __name__ == "__main__":
    run_diagnostics()