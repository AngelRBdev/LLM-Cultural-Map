# src/main_report.py
from src.utils.report_generator import generate_all_reports

def main():
    print("==================================================")
    print("📋 CONSOLIDATING ALL REPORTS (GLOBAL + REGIONAL)")
    print("==================================================")
    
    generate_all_reports()
    
    print("\n✅ Process finished. Check the 'Report_XX_Complete.md' files in your data/results/ folder")

if __name__ == "__main__":
    main()