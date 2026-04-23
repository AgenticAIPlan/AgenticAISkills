# === LLM API Configuration ===
# The script uses an OpenAI-compatible endpoint. You can point it at Novita,
# Anthropic (via Claude-OpenAI compatible endpoint), OpenAI directly, or any
# provider that exposes /chat/completions in OpenAI format.
LLM_API_KEY = "your-api-key-here"
LLM_BASE_URL = "https://api.novita.ai/v3/openai"  # example: Novita

# Writer model: plans topics and drafts posts
MODEL_NAME = "zai-org/glm-4.7"

# Reviewer model: audits drafts (SHOULD differ from MODEL_NAME to avoid
# same-model self-praise). Pick a model from a different provider or a
# different generation.
REVIEWER_MODEL = "zai-org/glm-5"

# === Account & Content Settings ===
ACCOUNT_NAME = "your-account-handle"
TARGET_AUDIENCE = "North American AI developers and builders"
LANGUAGE = "English"
CONTENT_STYLE = "Technical insights with marketing promotion for <your product>"

# === Directories ===
MATERIALS_DIR = "materials"
OUTPUT_DIR = "output"
