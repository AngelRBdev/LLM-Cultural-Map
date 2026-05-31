# 📊 Comprehensive Report - Phase B3
This report shows the performance in approval rate and average judge scores.

## 🌍 Global Summary
| Evaluated Model | Questions | Passed | Pass Rate | Judge Score (%) | Avg Time (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **cohere/command-r-08-2024** | 40 | 6 | **15.00%** | **64.81%** | 9.64s |
| **groq/llama-3.1-8b-instant** | 40 | 7 | **17.50%** | **63.01%** | 0.76s |
| **groq/llama-3.3-70b-versatile** | 40 | 22 | **55.00%** | **72.83%** | 0.90s |
| **groq/openai/gpt-oss-20b** | 13 | 13 | **100.00%** | **91.16%** | 1.50s |
| **groq/qwen/qwen3-32b** | 40 | 39 | **97.50%** | **90.27%** | 1.81s |

---

## 🗺️ Cultural Region Breakdown (Bias Analysis)
Metric used: **Average Judge Score (%)**

| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **cohere/command-r-08-2024** | **68.4%** | **62.3%** | **73.4%** | **62.9%** | **60.3%** | **67.9%** | **67.0%** | **61.3%** | **60.1%** | **64.6%** |
| **groq/llama-3.1-8b-instant** | **63.6%** | **62.6%** | **60.2%** | **62.6%** | **65.0%** | **65.9%** | **66.8%** | **60.4%** | **59.8%** | **64.1%** |
| **groq/llama-3.3-70b-versatile** | **71.9%** | **72.1%** | **80.4%** | **72.9%** | **72.5%** | **68.4%** | **75.2%** | **71.0%** | **71.6%** | **73.9%** |
| **groq/openai/gpt-oss-20b** | **90.8%** | **94.2%** | **87.5%** | **93.9%** | **87.8%** | **93.3%** | **93.3%** | **90.8%** | **89.5%** | **93.3%** |
| **groq/qwen/qwen3-32b** | **92.2%** | **92.1%** | **89.9%** | **90.6%** | **85.6%** | **90.6%** | **92.9%** | **88.9%** | **89.8%** | **89.1%** |
| 🎯 **REGIONAL AVERAGE** | **75.5%** | **73.5%** | **76.7%** | **73.9%** | **72.7%** | **74.4%** | **76.1%** | **72.4%** | **72.0%** | **74.1%** |