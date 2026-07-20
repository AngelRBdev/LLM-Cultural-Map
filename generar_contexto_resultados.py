# generar_contexto_resultados.py
import os
import json

# Carpetas o archivos que queremos ignorar para que el archivo no pese gigas
IGNORAR_CARPETAS = {'.git', '__pycache__', '.venv', 'external'}
IGNORAR_ARCHIVOS = {'generar_contexto_resultados.py', 'contexto.txt', 'code2prompt-x86_64-pc-windows-msvc.exe', 'LLM-Cultural-Map-main.zip'}

with open("contexto.txt", "w", encoding="utf-8") as f_out:
    # 1. Grabar la estructura del árbol de archivos
    f_out.write("Project Path: cultural_bias_benchmark\n\nSource Tree:\n```txt\ncultural_bias_benchmark\n")
    for raiz, dirs, archivos in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORAR_CARPETAS]
        nivel = raiz.replace('.', '').count(os.sep)
        sangria = '│   ' * nivel
        
        nombre_carpeta = os.path.basename(raiz)
        if nombre_carpeta and nombre_carpeta != '.':
            f_out.write(f"{sangria}├── {nombre_carpeta}\n")
            
        for archivo in archivos:
            if archivo not in IGNORAR_ARCHIVOS:
                f_out.write(f"{sangria}│   ├── {archivo}\n")
    f_out.write("```\n\n")

    # 2. Leer y volcar el contenido de los archivos de texto/código y RESULTADOS
    for raiz, dirs, archivos in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORAR_CARPETAS]
        for archivo in archivos:
            if archivo in IGNORAR_ARCHIVOS:
                continue
                
            ruta_completa = os.path.join(raiz, archivo)
            ruta_relativa = os.path.relpath(ruta_completa, '.')
            
            f_out.write(f"`{ruta_relativa}`:\n\n")
            
            # Si es un JSONL de resultados, volcamos unas líneas de muestra para analizar el formato y errores
            if archivo.endswith('.jsonl') and 'results' in ruta_completa:
                f_out.write("```jsonl\n[MUESTRA DE RESULTADOS GENERADOS]\n")
                try:
                    with open(ruta_completa, "r", encoding="utf-8") as f_in:
                        lineas = f_in.readlines()
                        # Ponemos las primeras 5 líneas y las últimas 5 líneas para ver si hay cortes o errores
                        for linea in lineas[:5]:
                            f_out.write(linea)
                        if len(lineas) > 10:
                            f_out.write("... [LÍNEAS INTERMEDIAS OMITIDAS] ...\n")
                            for linea in lineas[-5:]:
                                f_out.write(linea)
                except Exception as e:
                    f_out.write(f"[Error leyendo histórico de resultados: {e}]\n")
                f_out.write("```\n\n")
            
            # Si son scripts de código (.py, .md, .txt), los volcamos enteros
            elif archivo.endswith(('.py', '.md', '.txt', '.json', '.jsonl')):
                f_out.write("```\n")
                try:
                    with open(ruta_completa, "r", encoding="utf-8") as f_in:
                        f_out.write(f_in.read())
                except Exception as e:
                    f_out.write(f"[No se pudo leer el archivo: {e}]\n")
                f_out.write("```\n\n")

print("¡Hecho! Se ha generado tu nuevo archivo 'contexto.txt' incluyendo el estado de tus resultados.")