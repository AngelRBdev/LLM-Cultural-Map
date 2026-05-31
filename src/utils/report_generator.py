# src/utils/report_generator.py

import os
import json
import glob

# Master dictionary to map countries to their 10 Cultural Clusters
COUNTRY_TO_CLUSTER = {
    "USA": "Anglo", "UK": "Anglo", "Australia": "Anglo", "Canada": "Anglo", "New Zealand": "Anglo", "Ireland": "Anglo",
    "Japan": "Confucian Asia", "China": "Confucian Asia", "South Korea": "Confucian Asia", "Singapore": "Confucian Asia", "Taiwan": "Confucian Asia", "Hong Kong": "Confucian Asia",
    "Russia": "Eastern Europe", "Poland": "Eastern Europe", "Greece": "Eastern Europe", "Hungary": "Eastern Europe", "Czech Republic": "Eastern Europe", "Romania": "Eastern Europe",
    "Germany": "Germanic Europe", "Netherlands": "Germanic Europe", "Switzerland": "Germanic Europe", "Austria": "Germanic Europe",
    "Brazil": "Latin America", "Mexico": "Latin America", "Argentina": "Latin America", "Colombia": "Latin America", "Chile": "Latin America", "Peru": "Latin America",
    "France": "Latin Europe", "Spain": "Latin Europe", "Italy": "Latin Europe", "Israel": "Latin Europe", "Portugal": "Latin Europe",
    "Egypt": "Middle East", "Turkey": "Middle East", "Morocco": "Middle East", "Kuwait": "Middle East", "Qatar": "Middle East", "Saudi Arabia": "Middle East", "UAE": "Middle East",
    "Sweden": "Nordic Europe", "Denmark": "Nordic Europe", "Finland": "Nordic Europe", "Norway": "Nordic Europe",
    "India": "Southern Asia", "Indonesia": "Southern Asia", "Thailand": "Southern Asia", "Philippines": "Southern Asia", "Malaysia": "Southern Asia", "Vietnam": "Southern Asia",
    "Nigeria": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa", "Zimbabwe": "Sub-Saharan Africa", "Zambia": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa", "Ghana": "Sub-Saharan Africa"
}

def generate_all_reports(results_dir: str = "data/results"):
    """Generates comprehensive reports (Global + Regional) for the 3 phases in English."""
    _generate_phase_report("B1", results_dir, "Yes/No type questions")
    _generate_phase_report("B2", results_dir, "Multi-Choice scenarios")
    _generate_phase_report("B3", results_dir, "approval rate and average judge scores")

def _generate_phase_report(phase: str, results_dir: str, desc: str):
    files = glob.glob(os.path.join(results_dir, f"{phase}_results_*.jsonl"))
    if not files:
        print(f"⚠️ Warning: No files found for Phase {phase}")
        return
        
    global_data = {}    
    regional_data = {}  
    all_clusters = set()

    # 1. Read and group data
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                model = data.get("model", "Unknown")
                
                # --- SMART REGION EXTRACTION ---
                clusters_in_question = []
                
                if "clusters" in data and isinstance(data["clusters"], list):
                    clusters_in_question.extend(data["clusters"])
                elif "cluster" in data and isinstance(data["cluster"], str):
                    clusters_in_question.append(data["cluster"])
                else:
                    countries = []
                    if "countries" in data and isinstance(data["countries"], list):
                        countries.extend(data["countries"])
                    elif "country" in data and isinstance(data["country"], str):
                        countries.append(data["country"])
                        
                    for c in countries:
                        if c in COUNTRY_TO_CLUSTER:
                            clusters_in_question.append(COUNTRY_TO_CLUSTER[c])
                            
                if not clusters_in_question:
                    clusters_in_question = ["Unknown"]
                clusters_in_question = list(set(clusters_in_question))
                # -------------------------------
                
                if model not in global_data:
                    global_data[model] = {"total": 0, "correct": 0, "score": 0.0, "time": 0.0}
                    regional_data[model] = {}
                
                is_correct = data.get("is_correct") is True
                avg_score = data.get("average_score", 0.0)
                time_taken = data.get("time_taken", 0.0)
                
                # Sum into Global stats
                global_data[model]["total"] += 1
                if is_correct: global_data[model]["correct"] += 1
                global_data[model]["score"] += avg_score
                global_data[model]["time"] += time_taken
                
                # Sum into Regional stats
                for cluster in clusters_in_question:
                    if cluster not in regional_data[model]:
                        regional_data[model][cluster] = {"total": 0, "correct": 0, "score": 0.0}
                    
                    regional_data[model][cluster]["total"] += 1
                    if is_correct: regional_data[model][cluster]["correct"] += 1
                    regional_data[model][cluster]["score"] += avg_score
                    
                    all_clusters.add(cluster)

    # 2. Build the Markdown document
    lines = [f"# 📊 Comprehensive Report - Phase {phase}"]
    lines.append(f"This report shows the performance in {desc}.\n")
    
    # --- TABLE 1: GLOBAL SUMMARY ---
    lines.append("## 🌍 Global Summary")
    if phase == "B3":
        lines.append("| Evaluated Model | Questions | Passed | Pass Rate | Judge Score (%) | Avg Time (s) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for model, stats in global_data.items():
            pr = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0
            avg_s = (stats["score"] / stats["total"]) * 100 if stats["total"] else 0  
            avg_t = stats["time"] / stats["total"] if stats["total"] else 0
            lines.append(f"| **{model}** | {stats['total']} | {stats['correct']} | **{pr:.2f}%** | **{avg_s:.2f}%** | {avg_t:.2f}s |")
    else:
        lines.append("| Model | Questions | Correct | Accuracy (%) | Avg Time (s) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")
        for model, stats in global_data.items():
            acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0
            avg_t = stats["time"] / stats["total"] if stats["total"] else 0
            lines.append(f"| **{model}** | {stats['total']} | {stats['correct']} | **{acc:.2f}%** | {avg_t:.2f}s |")
            
    lines.append("\n---\n")
    
    # --- TABLE 2: REGIONAL BREAKDOWN ---
    lines.append("## 🗺️ Cultural Region Breakdown (Bias Analysis)")
    metric_name = "Average Judge Score (%)" if phase == "B3" else "Accuracy (%)"
    lines.append(f"Metric used: **{metric_name}**\n")
    
    clusters_list = sorted([c for c in all_clusters if c != "Unknown"])
    if not clusters_list and "Unknown" in all_clusters:
        clusters_list = ["Unknown"]
        
    header = "| Model | " + " | ".join(clusters_list) + " |"
    separator = "| :--- | " + " | ".join([":---:" for _ in clusters_list]) + " |"
    lines.extend([header, separator])
    
    # Individual model rows
    for model in global_data.keys():
        row = f"| **{model}** |"
        for cluster in clusters_list:
            stats = regional_data[model].get(cluster, {"total": 0, "correct": 0, "score": 0.0})
            if stats["total"] > 0:
                if phase == "B3":
                    val = (stats["score"] / stats["total"]) * 100  
                    row += f" **{val:.1f}%** |"
                else:
                    val = (stats["correct"] / stats["total"]) * 100
                    row += f" **{val:.1f}%** |"
            else:
                row += " N/A |"
        lines.append(row)
        
    # --- NEW ROW: REGIONAL AVERAGE ---
    avg_row = "| 🎯 **REGIONAL AVERAGE** |"
    for cluster in clusters_list:
        sum_total = 0
        sum_correct = 0
        sum_score = 0.0
        
        for model in global_data.keys():
            stats = regional_data[model].get(cluster, {"total": 0, "correct": 0, "score": 0.0})
            sum_total += stats["total"]
            sum_correct += stats["correct"]
            sum_score += stats["score"]
            
        if sum_total > 0:
            if phase == "B3":
                val = (sum_score / sum_total) * 100
                avg_row += f" **{val:.1f}%** |"
            else:
                val = (sum_correct / sum_total) * 100
                avg_row += f" **{val:.1f}%** |"
        else:
            avg_row += " N/A |"
            
    lines.append(avg_row)
        
    # 3. Save the file
    output_file = os.path.join(results_dir, f"Report_{phase}_Complete.md")
    os.makedirs(results_dir, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"✅ Report {phase} successfully generated in English! -> {output_file}")