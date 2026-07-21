# 🌍 Cultural Bias Benchmark System for LLMs

## 1. System Overview & Theoretical Foundation
The **Cultural Bias Benchmark System** is an automated, enterprise-grade evaluation framework engineered to measure, analyze, and quantify how different Large Language Models (LLMs) handle cross-cultural business communication, organizational behavior, and systemic cultural biases. 

The system’s core architecture is deeply grounded in two foundational frameworks of intercultural management:
* **Erin Meyer’s 8 Cultural Dimensions:** Evaluates communication styles and workplace dynamics across *Communicating, Evaluating, Persuading, Leading, Deciding, Trusting, Disagreeing, and Scheduling*.
* **GLOBE Study Cultural Clusters:** Groups and maps behavioral responses across **10 Global Cultural Clusters** (such as *Anglo, Germanic Europe, Nordic Europe, Latin Europe, Eastern Europe, Latin America, Middle East, Southern Asia, Sub-Saharan Africa, and Confucian Asia*).

---

## 2. Core Evaluation Phases & Architecture
To rigorously test model performance across various cognitive and behavioral levels, the system implements an escalating three-phase evaluation pipeline:

* **Phase B1 (Factual Knowledge):** Utilizes binary (`Yes/No`) comparative queries to test a model's foundational comprehension of cultural behavioral polarities and patterns between specific country pairs.
* **Phase B2 (Applied / Relational Reasoning):** Employs multiple-choice workplace scenario items depicting cross-cultural miscommunications or friction, challenging the model to correctly identify root cultural causes versus non-cultural administrative, technical, or interpersonal distractors.
* **Phase B3 (Behavioral Identification):** Presents granular workplace behavioral scenarios where models must deduce the most likely country of origin using multi-choice regional and cultural distractors distributed across varying degrees of pole separation.

---

## 3. System Directory Structure & Components
The repository is structured into distinct, modular functional directories:

```text
cultural_bias_benchmark/
│
├── data/
│   ├── generators/          # Programmatic dataset generators (generate_b1.py, generate_b2.py, generate_b3.py)
│   ├── raw/                 # Source JSONL benchmark datasets (b1_dataset.jsonl, b2_dataset.jsonl, b3_dataset.jsonl)
│   └── results/             # Generated raw LLM response logs (e.g., b1_answers_[model].jsonl)
│
├── external_evaluations/    # Complementary external mapping studies and datasets (CCD, Eticor)
├── reports/                 # Compiled analytical Markdown evaluation reports (cultural_bias_report.md)
│
├── src/
│   ├── config.py            # Global configuration (LiteLLM models, thresholds, cultural clusters mapping)
│   ├── main_run_benchmark.py# Primary orchestrator script for querying model APIs
│   ├── main_evaluate_report.py # Evaluation engine that parses responses and compiles metrics
│   └── models/              # API clients and fault-tolerant retry logic (LiteLLM + Tenacity)
│
├── .env                     # Environment variables (Private API Keys)
├── requirements.txt         # Python project dependencies
└── README.md                # System documentation
```

---

## 4. Execution Pipeline & Workflow
The benchmark system operates through two primary entry points that separate model inference from analytical reporting:

1. **Inference Execution (`src/main_run_benchmark.py`):**
   * Iterates through the models defined in `src/config.py`.
   * Automatically detects question formats (binary vs. multi-option dictionaries).
   * Interacts with language models via LiteLLM, writing raw logs sequentially into `data/results/` using a standardized naming convention (`b1_answers_[model].jsonl`, `b2_answers_[model].jsonl`, `b3_answers_[model].jsonl`).

2. **Evaluation & Reporting Engine (`src/main_evaluate_report.py`):**
   * Parses raw response files from `data/results/` without requiring live model API calls.
   * Applies regular expression matching to extract correct answers, calculating granular accuracies per cultural cluster and Meyer dimension.
   * Generates a comprehensive summary document and saves it directly to **`reports/cultural_bias_report.md`**.

---

## 5. Configuration & Supported Models
Model behaviors, evaluation thresholds, and cultural cluster definitions are centrally managed in `src/config.py`. By default, the system evaluates models via LiteLLM, supporting providers such as:
* `groq/llama-3.1-8b-instant`
* `groq/llama-3.3-70b-versatile`
* `cohere/command-r-08-2024`
* `groq/openai/gpt-oss-20b`

---

## 6. Quick Start & Setup Guide

### Step 1: Installation
Clone the repository and install the required Python dependencies listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 2: Environment Configuration
Create a `.env` file in the root directory to store your private API keys required by LiteLLM:
```text
OPENAI_API_KEY="your_key_here"
GEMINI_API_KEY="your_key_here"
GROQ_API_KEY="your_key_here"
COHERE_API_KEY="your_key_here"
```

> *Security Note: Ensure your `.env` file is included inside your `.gitignore` file to prevent accidental credential leakage.*

### Step 3: Running the Benchmark System
To execute model evaluations across all datasets and automatically trigger the report generation module, run:
```bash
python src/main_run_benchmark.py