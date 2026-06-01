# 🌍 Cultural Bias Benchmark for LLMs

## Overview
The **Cultural Bias Benchmark** is an automated evaluation framework designed to measure and analyze how different Large Language Models (LLMs) handle cross-cultural business communication, organizational behavior, and cultural biases. 

The evaluation is grounded in **Erin Meyer's 8 Cultural Dimensions** (Communicating, Evaluating, Persuading, Leading, Deciding, Trusting, Disagreeing, and Scheduling) and groups responses across **10 Global Cultural Clusters**.

## 🏗️ Project Architecture

``` text
cultural_bias_benchmark/
│
├── data/
│   ├── raw/                 # Original JSONL datasets (with solutions)
│   ├── processed/           # Cleaned datasets for evaluation (without solutions)
│   └── results/             # Generated LLM responses and final Markdown reports
│
├── src/
│   ├── config.py            # Global configuration (Models, Thresholds, Clusters)
│   ├── main.py              # Main orchestrator script
│   ├── prompts/             # Strict system and user prompts for each phase
│   ├── models/              # API clients and retry logic (LiteLLM + Tenacity)
│   ├── evaluators/          # Evaluation logic for B1, B2, and B3 phases
│   └── utils/               # Data processing and report generation tools
│
├── .env                     # Environment variables (API Keys)
└── requirements.txt         # Python dependencies
```

## 🧠 Evaluation Phases

The benchmark tests models across three escalating levels of complexity:

1. **Phase B1 (Factual):** Binary (Yes/No) questions testing factual knowledge of cultural norms. Evaluated by strict character matching.
2. **Phase B2 (Relational):** Multiple-choice scenarios involving interactions between two different cultural regions. Evaluated by strict character matching.
3. **Phase B3 (Reasoning):** Complex, open-ended scenarios. This phase utilizes an **LLM-as-a-Judge** methodology. The target model generates a short essay, which is then scored (0.0 to 1.0) by the other 4 models in the benchmark against a gold-standard rubric. An average score of `>= 0.75` is considered a pass.

## 🚀 Setup and Installation

**1. Clone the repository and navigate to the root folder.**

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure Environment Variables:**
Create a `.env` file in the root directory and add your API keys for the providers you intend to use via LiteLLM:
```text
OPENAI_API_KEY="your_key_here"
GEMINI_API_KEY="your_key_here"
MISTRAL_API_KEY="your_key_here"
HUGGINGFACE_API_KEY="your_key_here"
```

*Note: Ensure your `.env` file is added to `.gitignore` to prevent leaking API keys.*

## ⚙️ Usage

**Step 1: Prepare the Data**
Before running the benchmark, you must clean the raw data to hide the solutions from the models.
```bash
python src/utils/data_handler.py
```
*This will read files from `data/raw/` and generate `_processed` versions in `data/processed/`.*

**Step 2: Run the Benchmark**
Execute the main orchestrator to start the evaluation across all models and phases.
```bash
python -m src.main
```

## 📊 Reporting
Once the benchmark completes, a comprehensive Markdown report (`benchmark_final_report.md`) is automatically generated in the `data/results/` directory. 

The report breaks down the performance of each model by:
- Overall Accuracy
- Average Time taken per query
- Accuracy across the 8 Meyer's Cultural Dimensions
- Accuracy across the 10 Global Cultural Clusters