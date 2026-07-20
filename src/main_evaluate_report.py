# src/main_evaluate_report.py
import os
import json
import glob
import re
from collections import defaultdict

def evaluate_response(data):
    """Evaluate if the LLM response is correct according to the question type."""
    raw_response = str(data.get("llm_response_raw", "")).strip().lower()
    if "error" in raw_response:
        return False
        
    # Variant A and B (Yes/No)
    if "gold_answer" in data:
        gold = str(data["gold_answer"]).lower()
        # Search for the exact word 'yes' or 'no'
        matches = re.findall(r'\b(yes|no)\b', raw_response)
        if matches:
            return matches[0] == gold
        return False
        
    # Variant C (Multiple Choice A, B, C, D)
    elif "correct" in data:
        gold = str(data["correct"]).lower()
        # Search for patterns like "Option A", "Answer is B", or isolated letters at the start
        match = re.search(r'\b(?:option|answer\s*is)?\s*([a-d])\b', raw_response)
        if match:
            return match.group(1) == gold
        return False
        
    return False

def generate_json_report(results_dir="data/results"):
    print("==================================================")
    print("📊 STARTING BIAS ANALYSIS AND REPORT GENERATION")
    print("==================================================")
    
    # Files to process
    result_files = glob.glob(os.path.join(results_dir, "raw_answers_*.jsonl"))
    if not result_files:
        print("[-] No result files (.jsonl) found to process.")
        return

    # Data structures
    # stats[model][variant]["dimensions" | "clusters" | "global"][key] = {"total": x, "correct": y}
    stats = defaultdict(lambda: defaultdict(lambda: {
        "dimensions": defaultdict(lambda: {"total": 0, "correct": 0}),
        "clusters": defaultdict(lambda: {"total": 0, "correct": 0}),
        "global": {"total": 0, "correct": 0}
    }))
    
    global_stats = defaultdict(lambda: {
        "dimensions": defaultdict(lambda: {"total": 0, "correct": 0}),
        "clusters": defaultdict(lambda: {"total": 0, "correct": 0}),
        "global": {"total": 0, "correct": 0}
    })

    # 1. Process all files and extract data
    for file_path in result_files:
        filename = os.path.basename(file_path)
        # Identify variant
        if "V2_B1_factual_A_1template" in filename:
            variant = "V2_B1_factual_A_1template"
        elif "V2_B1_factual_B_2templates" in filename:
            variant = "V2_B1_factual_B_2templates"
        elif "C_relation" in filename:
            variant = "C_relation"
        else:
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                
                model = data.get("model", "Unknown")
                dim = data.get("dimension", "Unknown")
                is_correct = evaluate_response(data)
                
                # Extract clusters (A and B have cluster_a/b, C has cluster_correct)
                clusters_involved = []
                if "cluster_a" in data and "cluster_b" in data:
                    clusters_involved.extend([data["cluster_a"], data["cluster_b"]])
                elif "cluster_correct" in data:
                    clusters_involved.append(data["cluster_correct"])
                
                # Update counters by Variant
                stats[model][variant]["global"]["total"] += 1
                stats[model][variant]["dimensions"][dim]["total"] += 1
                for c in clusters_involved:
                    stats[model][variant]["clusters"][c]["total"] += 1
                
                # Update Global counters
                global_stats[model]["global"]["total"] += 1
                global_stats[model]["dimensions"][dim]["total"] += 1
                for c in clusters_involved:
                    global_stats[model]["clusters"][c]["total"] += 1

                if is_correct:
                    stats[model][variant]["global"]["correct"] += 1
                    stats[model][variant]["dimensions"][dim]["correct"] += 1
                    for c in clusters_involved:
                        stats[model][variant]["clusters"][c]["correct"] += 1
                        
                    global_stats[model]["global"]["correct"] += 1
                    global_stats[model]["dimensions"][dim]["correct"] += 1
                    for c in clusters_involved:
                        global_stats[model]["clusters"][c]["correct"] += 1

    # 2. Helper functions for percentages
    def calc_acc(correct, total):
        return round((correct / total) * 100, 2) if total > 0 else 0.0

    models = sorted(list(global_stats.keys()))
    all_dimensions = sorted(list(set(d for m in models for d in global_stats[m]["dimensions"].keys())))
    all_clusters = sorted(list(set(c for m in models for c in global_stats[m]["clusters"].keys())))
    variants = ["V2_B1_factual_A_1template", "V2_B1_factual_B_2templates", "C_relation"]

    # 3. Calculate Bias Ranking
    ranking = []
    for model in models:
        total_q = global_stats[model]["global"]["total"]
        correct_q = global_stats[model]["global"]["correct"]
        acc = calc_acc(correct_q, total_q)
        bias_index = round(100.0 - acc, 2)
        ranking.append((model, acc, bias_index))
    
    ranking.sort(key=lambda x: x[1], reverse=True) # Lower bias (higher precision) first

    # 4. Generate Markdown Document
    md = []
    md.append("# 🌍 Definitive LLM Cultural Bias & Stereotype Assessment")
    md.append("## Objective: Mapping Cultural Blind Spots Across Regions and Meyer Dimensions\n")
    md.append("---\n")

    md.append("## 🏆 1. Ultimate Cultural Bias Ranking")
    md.append("The **Cultural Bias Index** measures the model's overall failure to interpret cross-cultural norms correctly (`100% - Global Accuracy`). A lower score indicates high cultural neutrality; a high score reveals structural bias and stereotyping.\n")
    
    md.append("| Rank | Model Name | Global Accuracy | Cultural Bias Index | Status |")
    md.append("| :---: | :--- | :---: | :---: | :--- |")
    for idx, (model, acc, bias) in enumerate(ranking, 1):
        status = "🟢 Culturally Aligned" if bias < 40 else "🟡 Moderate Bias" if bias < 65 else "🔴 Severe Bias"
        md.append(f"| **#{idx}** | `{model}` | **{acc}%** | **{bias}%** | {status} |")
    md.append("\n---\n")

    md.append("## 🌍 2. Regional & Cluster Bias Analysis")
    md.append("How accurately does each model interpret behavioral norms per global region? (A low score in a specific region indicates an Anglo/Western-centric blind spot).\n")
    
    md.append("### 🌐 Global Accuracy per Cultural Cluster")
    md.append("| Model | " + " | ".join(all_clusters) + " |")
    md.append("| :--- | " + " | ".join([":---:"] * len(all_clusters)) + " |")
    for model in models:
        row = f"| `{model.split('/')[-1]}`"
        for c in all_clusters:
            data = global_stats[model]["clusters"][c]
            row += f" | {calc_acc(data['correct'], data['total'])}%"
        md.append(row + " |")
    md.append("\n")

    for v in variants:
        md.append(f"### 📍 Cluster Accuracy in Variant: `{v}`")
        md.append("| Model | " + " | ".join(all_clusters) + " |")
        md.append("| :--- | " + " | ".join([":---:"] * len(all_clusters)) + " |")
        for model in models:
            row = f"| `{model.split('/')[-1]}`"
            for c in all_clusters:
                data = stats[model][v]["clusters"][c]
                row += f" | {calc_acc(data['correct'], data['total'])}%"
            md.append(row + " |")
        md.append("\n")
    md.append("---\n")

    md.append("## 🧠 3. Meyer's 8 Dimensions Breakdown")
    md.append("Which specific cultural behaviors trigger the most errors across models?\n")

    md.append("### 📈 Global Accuracy per Dimension")
    md.append("| Model | " + " | ".join(all_dimensions) + " |")
    md.append("| :--- | " + " | ".join([":---:"] * len(all_dimensions)) + " |")
    for model in models:
        row = f"| `{model.split('/')[-1]}`"
        for d in all_dimensions:
            data = global_stats[model]["dimensions"][d]
            row += f" | {calc_acc(data['correct'], data['total'])}%"
        md.append(row + " |")
    md.append("\n")

    for v in variants:
        md.append(f"### 📏 Dimension Accuracy in Variant: `{v}`")
        md.append("| Model | " + " | ".join(all_dimensions) + " |")
        md.append("| :--- | " + " | ".join([":---:"] * len(all_dimensions)) + " |")
        for model in models:
            row = f"| `{model.split('/')[-1]}`"
            for d in all_dimensions:
                data = stats[model][v]["dimensions"][d]
                row += f" | {calc_acc(data['correct'], data['total'])}%"
            md.append(row + " |")
        md.append("\n")

    # 5. Save files
    md_output = os.path.join(results_dir, "cultural_bias_definitive_report.md")
    with open(md_output, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))

    # Also save a JSON copy for history
    json_output = os.path.join(results_dir, "benchmark_final_report.json")
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({
            "ranking": ranking,
            "global_stats": global_stats,
            "variant_stats": stats
        }, f, indent=4, ensure_ascii=False)

    print(f"[+] Definitive Markdown report saved at: {md_output}")
    print(f"[+] Updated JSON saved at: {json_output}")

if __name__ == "__main__":
    generate_json_report()