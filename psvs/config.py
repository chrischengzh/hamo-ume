"""
PSVS Configuration Constants
"""

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyAg7u3Pf2YmIw_qTc0YIFViLT3La3WT6qU"
GEMINI_MODEL = "gemini-3-flash-preview"  # Using gemini-3-flash-preview as requested

# Generation parameters
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_output_tokens": 2048,
}

# Trajectory history settings
MAX_TRAJECTORY_HISTORY = 50  # Keep last 50 PSVS positions

# Stress thresholds (from status_transform.json)
STRESS_THRESHOLD_POSITIVE_TO_NEGATIVE = 4.0
STRESS_THRESHOLD_NEGATIVE_TO_NEUROTIC = 7.0

# Message filtering - skip PSVS update for very short messages
MIN_MESSAGE_LENGTH_FOR_PSVS_UPDATE = 3  # Skip messages like "ok", "hi", "no"

# Homeostatic target values (orange center)
HOMEOSTATIC_VALUES = {
    "respect": "尊重",
    "control": "掌控",
    "appreciation": "欣赏",
    "recognition": "认同",
}

# Quadrant characteristics for prompt generation
QUADRANT_CHARACTERISTICS = {
    "expert": {
        "name": "专家型 (EXPERT)",
        "traits": ["明晰事理来龙去脉", "答疑解惑获得尊重"],
        "strengths": ["analytical", "fact-based", "prudent", "detail-oriented"],
        "challenges": ["overthinking", "avoidance", "delay decision-making"],
        "neurotic_pattern": "拖延症 - procrastination",
    },
    "supporter": {
        "name": "支持型 (SUPPORTER)",
        "traits": ["实现他人的期望", "获得他人的认同"],
        "strengths": ["supportive", "trusting", "empathetic", "collaborative"],
        "challenges": ["people-pleasing", "self-erasing", "over-accommodation"],
        "neurotic_pattern": "抑郁症 - depression from self-neglect",
    },
    "leader": {
        "name": "领导型 (LEADER)",
        "traits": ["获得全程决断权力", "获得对事情的掌控"],
        "strengths": ["decisive", "results-driven", "confident", "action-oriented"],
        "challenges": ["domineering", "controlling", "my-way-or-highway"],
        "neurotic_pattern": "躁狂症 - mania from over-control",
    },
    "dreamer": {
        "name": "梦想型 (DREAMER)",
        "traits": ["与人分享新奇特", "获得他人的欣赏"],
        "strengths": ["inspiring", "enthusiastic", "creative", "visionary"],
        "challenges": ["attention-seeking", "narcissistic", "boundary issues"],
        "neurotic_pattern": "NPD - narcissistic personality disorder",
    },
}

# Energy state guidance
ENERGY_STATE_GUIDANCE = {
    "positive": {
        "zone": "正能态 (Homeostatic)",
        "color": "橙色中心区域",
        "characteristics": ["尊重", "掌控", "欣赏", "认同"],
        "goal": "Maintain balance and stability",
    },
    "negative": {
        "zone": "负能态 (Unstable)",
        "color": "灰色中间区域",
        "characteristics": ["懒散-逃避", "过敏-独断", "过敏-攻击", "过敏-默认"],
        "goal": "Move toward positive zone through agency and boundaries",
    },
    "neurotic": {
        "zone": "神经态 (Crisis)",
        "color": "红色外围区域",
        "characteristics": ["拖延症", "躁狂症", "抑郁症", "NPD"],
        "goal": "Urgent intervention needed - restore to negative then positive",
    },
}
