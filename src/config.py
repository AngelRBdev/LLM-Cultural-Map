# src/config.py
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ==========================================
# 1. MODEL CONFIGURATION (LiteLLM Format)
# ==========================================
MODELS_TO_EVALUATE = [
    "groq/llama-3.1-8b-instant",             # 1. META Family (Light - 8B)
    "groq/llama-3.3-70b-versatile",          # 2. META Family (Giant - 70B)
    "cohere/command-r-08-2024",              # 3. COHERE Family
    "groq/openai/gpt-oss-20b",               # 4. OPENAI Family
    "groq/qwen/qwen3-32b"                    # 5. ALIBABA Family
]

# ==========================================
# 2. EVALUATION THRESHOLDS
# ==========================================
B3_EVALUATION_THRESHOLD = 0.75

# ==========================================
# 3. CULTURAL CLUSTERS MAPPING
# ==========================================
CULTURAL_CLUSTERS = {
    "Anglo": [
        "Australia", "Canada (English-speaking)", "England", "Ireland", 
        "New Zealand", "South Africa (White sample)", "United States", 
        "USA", "UK", "Canada"
    ],
    "Confucian Asia": [
        "China", "Hong Kong", "Japan", "Singapore", "South Korea", "Taiwan"
    ],
    "Eastern Europe": [
        "Albania", "Czech Republic", "Georgia", "Greece", "Hungary", 
        "Kazakhstan", "Poland", "Russia", "Slovenia"
    ],
    "Germanic Europe": [
        "Austria", "Germany", "The Netherlands", "Netherlands", 
        "Switzerland (German Speaking)"
    ],
    "Latin America": [
        "Argentina", "Bolivia", "Brazil", "Colombia", "Costa Rica", 
        "Ecuador", "El Salvador", "Guatemala", "México", "Mexico", "Venezuela"
    ],
    "Latin Europe": [
        "France", "Israel", "Italy", "Portugal", "Spain", 
        "Switzerland (French-speaking)", "Switzerland"
    ],
    "Middle East": [
        "Egypt", "Kuwait", "Morocco", "Qatar", "Turkey", "Saudi Arabia", "UAE", "Lebanon"
    ],
    "Nordic Europe": [
        "Denmark", "Finland", "Sweden", "Norway"
    ],
    "Southern Asia": [
        "India", "Indonesia", "Iran", "Malaysia", "The Philippines", "Philippines", "Thailand", "Pakistan"
    ],
    "Sub-Saharan Africa": [
        "Namibia", "Nigeria", "South Africa (Black sample)", "South Africa", "Zambia", "Zimbabwe", "Ghana", "Kenya"
    ]
}