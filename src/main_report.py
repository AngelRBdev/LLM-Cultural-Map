# src/main_report.py
from src.utils.report_generator import generate_all_reports

def main():
    print("==================================================")
    print("📋 CONSOLIDANDO TODOS LOS INFORMES (GLOBAL + REGIONAL)")
    print("==================================================")
    
    generate_all_reports()
    
    print("\n✅ Proceso terminado. Revisa los archivos 'Reporte_XX_Completo.md' en tu carpeta data/results/")

if __name__ == "__main__":
    main()