# 🌍 Definitive LLM Cultural Bias & Stereotype Assessment
## Objective: Mapping Cultural Blind Spots Across Regions and Meyer Dimensions

---

## 🏆 1. Ultimate Cultural Bias Ranking
The **Cultural Bias Index** measures the model's overall failure to interpret cross-cultural norms correctly (`100% - Global Accuracy`). A lower score indicates high cultural neutrality; a high score reveals structural bias and stereotyping.

| Rank | Model Name | Global Accuracy | Cultural Bias Index | Status |
| :---: | :--- | :---: | :---: | :--- |
| **#1** | `groq/openai/gpt-oss-20b` | **74.31%** | **25.69%** | 🟢 Culturally Aligned |
| **#2** | `groq/llama-3.3-70b-versatile` | **62.36%** | **37.64%** | 🟢 Culturally Aligned |
| **#3** | `cohere/command-r-08-2024` | **59.86%** | **40.14%** | 🟡 Moderate Bias |
| **#4** | `groq/llama-3.1-8b-instant` | **58.33%** | **41.67%** | 🟡 Moderate Bias |

---

## 🌍 2. Regional & Cluster Bias Analysis
How accurately does each model interpret behavioral norms per global region? (A low score in a specific region indicates an Anglo/Western-centric blind spot).

### 🌐 Global Accuracy per Cultural Cluster
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 63.45% | 65.19% | 60.0% | 63.06% | 67.23% | 56.55% | 68.29% | 57.72% | 65.12% | 55.47% |
| `llama-3.1-8b-instant` | 62.76% | 59.26% | 61.54% | 58.6% | 68.07% | 54.48% | 63.41% | 57.05% | 62.79% | 59.38% |
| `llama-3.3-70b-versatile` | 66.21% | 65.19% | 60.0% | 63.06% | 65.55% | 62.07% | 62.6% | 58.39% | 69.77% | 57.03% |
| `gpt-oss-20b` | 77.24% | 80.74% | 72.31% | 80.25% | 75.63% | 77.93% | 78.05% | 72.48% | 76.74% | 67.97% |


### 📍 Cluster Accuracy in Dataset: `b1`
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 51.43% | 68.33% | 52.31% | 56.34% | 57.89% | 52.11% | 63.79% | 46.48% | 62.71% | 51.72% |
| `llama-3.1-8b-instant` | 51.43% | 55.0% | 56.92% | 52.11% | 57.89% | 46.48% | 51.72% | 45.07% | 52.54% | 48.28% |
| `llama-3.3-70b-versatile` | 34.29% | 25.0% | 27.69% | 26.76% | 33.33% | 28.17% | 24.14% | 23.94% | 38.98% | 25.86% |
| `gpt-oss-20b` | 85.71% | 88.33% | 76.92% | 83.1% | 80.7% | 83.1% | 91.38% | 77.46% | 88.14% | 70.69% |


### 📍 Cluster Accuracy in Dataset: `b2`
| Model | Anglo | Confucian Asia | Eastern Europe | Germanic Europe | Latin America | Latin Europe | Middle East | Nordic Europe | Southern Asia | Sub-Saharan Africa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 80.88% | 70.0% | 72.13% | 73.53% | 77.05% | 64.71% | 75.81% | 75.0% | 75.81% | 66.13% |
| `llama-3.1-8b-instant` | 73.53% | 73.33% | 70.49% | 72.06% | 78.69% | 67.65% | 77.42% | 75.0% | 79.03% | 77.42% |
| `llama-3.3-70b-versatile` | 98.53% | 100.0% | 98.36% | 98.53% | 96.72% | 100.0% | 100.0% | 98.53% | 100.0% | 93.55% |
| `gpt-oss-20b` | 72.06% | 80.0% | 72.13% | 79.41% | 72.13% | 76.47% | 67.74% | 73.53% | 67.74% | 72.58% |


### 📍 Cluster Accuracy in Dataset: `b3`
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
| `command-r-08-2024` | 52.22% | 65.56% | 62.22% | 67.78% | 63.33% | 35.56% | 62.22% | 70.0% |
| `llama-3.1-8b-instant` | 47.78% | 67.78% | 55.56% | 66.67% | 57.78% | 46.67% | 52.22% | 72.22% |
| `llama-3.3-70b-versatile` | 74.44% | 48.89% | 56.67% | 80.0% | 56.67% | 71.11% | 54.44% | 56.67% |
| `gpt-oss-20b` | 83.33% | 77.78% | 63.33% | 86.67% | 80.0% | 58.89% | 62.22% | 82.22% |


### 📏 Dimension Accuracy in Dataset: `b1`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 52.5% | 55.0% | 50.0% | 52.5% | 55.0% | 52.5% | 80.0% | 50.0% |
| `llama-3.1-8b-instant` | 50.0% | 55.0% | 50.0% | 50.0% | 50.0% | 57.5% | 50.0% | 50.0% |
| `llama-3.3-70b-versatile` | 55.0% | 7.5% | 10.0% | 65.0% | 12.5% | 50.0% | 15.0% | 15.0% |
| `gpt-oss-20b` | 87.5% | 80.0% | 77.5% | 87.5% | 90.0% | 62.5% | 85.0% | 90.0% |


### 📏 Dimension Accuracy in Dataset: `b2`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 60.0% | 92.5% | 85.0% | 100.0% | 75.0% | 20.0% | 52.5% | 100.0% |
| `llama-3.1-8b-instant` | 57.5% | 97.5% | 75.0% | 100.0% | 75.0% | 35.0% | 55.0% | 100.0% |
| `llama-3.3-70b-versatile` | 95.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 92.5% | 100.0% |
| `gpt-oss-20b` | 87.5% | 95.0% | 50.0% | 97.5% | 75.0% | 60.0% | 42.5% | 80.0% |


### 📏 Dimension Accuracy in Dataset: `b3`
| Model | Communicating | Deciding | Disagreeing | Evaluating | Leading | Persuading | Scheduling | Trusting |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command-r-08-2024` | 20.0% | 0.0% | 20.0% | 0.0% | 50.0% | 30.0% | 30.0% | 30.0% |
| `llama-3.1-8b-instant` | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 50.0% | 50.0% | 50.0% |
| `llama-3.3-70b-versatile` | 70.0% | 10.0% | 70.0% | 60.0% | 60.0% | 40.0% | 60.0% | 50.0% |
| `gpt-oss-20b` | 50.0% | 0.0% | 60.0% | 40.0% | 60.0% | 40.0% | 50.0% | 60.0% |

