# 🌍 Definitive LLM Cultural Bias & Stereotype Assessment
## Objective: Mapping Cultural Blind Spots Across Regions and Meyer Dimensions

---

## 🏆 1. Ultimate Cultural Bias Ranking
The **Cultural Bias Index** measures the model's overall failure to interpret cross-cultural norms correctly (`100% - Global Accuracy`). A lower score indicates high cultural neutrality; a high score reveals structural bias and stereotyping.

| Rank | Model Name | Global Accuracy | Cultural Bias Index | Status |
| :---: | :--- | :---: | :---: | :--- |
| **#1** | `groq/openai/gpt-oss-20b` | **71.53%** | **28.47%** | 🟢 Culturally Aligned |
| **#2** | `groq/llama-3.1-8b-instant` | **48.06%** | **51.94%** | 🟡 Moderate Bias |
| **#3** | `cohere/command-r-08-2024` | **30.14%** | **69.86%** | 🔴 Severe Bias |
| **#4** | `groq/llama-3.3-70b-versatile` | **28.75%** | **71.25%** | 🔴 Severe Bias |

---

## 🌍 2. Regional & Cluster Bias Analysis
How accurately does each model interpret behavioral norms per global region? (A low score in a specific region indicates an Anglo/Western-centric blind spot).

### 🌐 Global Accuracy per Cultural Cluster
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 28.08% | 35.56% | 29.1% | 32.7% | 32.76% | 30.41% | 35.0% | 25.0% | 32.54% | 25.81% |
| `llama-3.1-8b-instant` | 52.74% | 48.89% | 51.49% | 50.31% | 57.76% | 44.59% | 55.0% | 44.08% | 47.62% | 45.97% |
| `llama-3.3-70b-versatile` | 26.71% | 28.15% | 28.36% | 28.3% | 27.59% | 29.05% | 26.67% | 23.68% | 31.75% | 23.39% |
| `gpt-oss-20b` | 76.03% | 73.33% | 70.9% | 79.87% | 71.55% | 72.3% | 80.83% | 69.74% | 72.22% | 62.9% |


### 📍 Cluster Accuracy in Variant: `V2_B1_factual_A_1template`
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 51.43% | 68.33% | 52.31% | 56.34% | 57.89% | 52.11% | 63.79% | 46.48% | 62.71% | 51.72% |
| `llama-3.1-8b-instant` | 51.43% | 55.0% | 56.92% | 52.11% | 57.89% | 46.48% | 51.72% | 45.07% | 52.54% | 48.28% |
| `llama-3.3-70b-versatile` | 34.29% | 25.0% | 27.69% | 26.76% | 33.33% | 28.17% | 24.14% | 23.94% | 38.98% | 25.86% |
| `gpt-oss-20b` | 85.71% | 88.33% | 76.92% | 83.1% | 80.7% | 83.1% | 91.38% | 77.46% | 88.14% | 70.69% |


### 📍 Cluster Accuracy in Variant: `V2_B1_factual_B_2templates`
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 5.8% | 3.33% | 7.69% | 4.29% | 8.62% | 9.86% | 8.47% | 4.23% | 6.78% | 3.45% |
| `llama-3.1-8b-instant` | 52.17% | 50.0% | 49.23% | 52.86% | 58.62% | 46.48% | 61.02% | 46.48% | 47.46% | 50.0% |
| `llama-3.3-70b-versatile` | 14.49% | 16.67% | 30.77% | 18.57% | 22.41% | 29.58% | 28.81% | 22.54% | 20.34% | 24.14% |
| `gpt-oss-20b` | 69.57% | 63.33% | 69.23% | 78.57% | 63.79% | 64.79% | 72.88% | 67.61% | 57.63% | 62.07% |


### 📍 Cluster Accuracy in Variant: `C_relation`
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 14.29% | 33.33% | 0.0% | 50.0% | 0.0% | 16.67% | 0.0% | 20.0% | 0.0% | 0.0% |
| `llama-3.1-8b-instant` | 71.43% | 20.0% | 0.0% | 33.33% | 0.0% | 0.0% | 0.0% | 20.0% | 12.5% | 0.0% |
| `llama-3.3-70b-versatile` | 71.43% | 86.67% | 0.0% | 72.22% | 0.0% | 33.33% | 33.33% | 30.0% | 62.5% | 0.0% |
| `gpt-oss-20b` | 42.86% | 53.33% | 0.0% | 72.22% | 0.0% | 33.33% | 33.33% | 30.0% | 62.5% | 12.5% |


---

## 🧠 3. Meyer's 8 Dimensions Breakdown
Which specific cultural behaviors trigger the most errors across models?

### 📈 Global Accuracy per Dimension
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 47.78% | 24.44% | 24.44% | 23.33% | 30.0% | 26.67% | 38.89% | 25.56% |
| `llama-3.1-8b-instant` | 44.44% | 47.78% | 47.78% | 44.44% | 46.67% | 54.44% | 50.0% | 48.89% |
| `llama-3.3-70b-versatile` | 57.78% | 5.56% | 20.0% | 62.22% | 16.67% | 31.11% | 17.78% | 18.89% |
| `gpt-oss-20b` | 85.56% | 74.44% | 55.56% | 81.11% | 86.67% | 57.78% | 50.0% | 81.11% |


### 📏 Dimension Accuracy in Variant: `V2_B1_factual_A_1template`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 52.5% | 55.0% | 50.0% | 52.5% | 55.0% | 52.5% | 80.0% | 50.0% |
| `llama-3.1-8b-instant` | 50.0% | 55.0% | 50.0% | 50.0% | 50.0% | 57.5% | 50.0% | 50.0% |
| `llama-3.3-70b-versatile` | 55.0% | 7.5% | 10.0% | 65.0% | 12.5% | 50.0% | 15.0% | 15.0% |
| `gpt-oss-20b` | 87.5% | 80.0% | 77.5% | 87.5% | 90.0% | 62.5% | 85.0% | 90.0% |


### 📏 Dimension Accuracy in Variant: `V2_B1_factual_B_2templates`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 50.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| `llama-3.1-8b-instant` | 50.0% | 52.5% | 57.5% | 50.0% | 50.0% | 52.5% | 50.0% | 47.5% |
| `llama-3.3-70b-versatile` | 57.5% | 2.5% | 17.5% | 60.0% | 10.0% | 10.0% | 10.0% | 15.0% |
| `gpt-oss-20b` | 92.5% | 87.5% | 32.5% | 85.0% | 90.0% | 57.5% | 15.0% | 77.5% |


### 📏 Dimension Accuracy in Variant: `C_relation`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 20.0% | 0.0% | 20.0% | 0.0% | 50.0% | 30.0% | 30.0% | 30.0% |
| `llama-3.1-8b-instant` | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 50.0% | 50.0% | 50.0% |
| `llama-3.3-70b-versatile` | 70.0% | 10.0% | 70.0% | 60.0% | 60.0% | 40.0% | 60.0% | 50.0% |
| `gpt-oss-20b` | 50.0% | 0.0% | 60.0% | 40.0% | 60.0% | 40.0% | 50.0% | 60.0% |

