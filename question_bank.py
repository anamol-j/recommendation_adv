import random

GENDER_QUESTION = {
    "id": "gender",
    "label": "Gender",
    "type": "radio",
    "options": ["Male", "Female", "Non-Binary", "Prefer not to say"]
}

QUESTION_BANK = [
    {
        "id": "name",
        "label": "What should we call you?",
        "type": "text"
    },
    {
        "id": "age_range",
        "label": "Your age range",
        "type": "radio",
        "options": ["18-24", "25-34", "35-44", "45-54", "55+"]
    },
    {
        "id": "style_goal",
        "label": "What's your main style goal?",
        "type": "multiselect",
        "options": [
            "Complement my natural features",
            "Looking chic and fashionable",
            "Standing out from the crowd",
            "Shopping smart and buying less"
        ]
    },
    {
        "id": "difficult_occasion",
        "label": "Which occasions are hardest to dress for?",
        "type": "multiselect",
        "options": ["Work", "Workout", "Party", "Everyday", "Weekend", "Beach Wear"]
    },
    {
        "id": "style_preference",
        "label": "Style Preference",
        "type": "multiselect",
        "options": ["Trendy", "Timeless"]
    },
    {
        "id": "preferred_fit",
        "label": "Preferred Fit",
        "type": "radio",
        "options": ["Slim Fit", "Regular Fit", "Relaxed Fit"]
    },
    {
        "id": "outfit_boldness",
        "label": "Outfit Boldness",
        "type": "radio",
        "options": ["Safe & Classic", "Balanced", "Edgy & Daring"]
    },
    {
        "id": "color_comfort",
        "label": "Color Comfort",
        "type": "radio",
        "options": ["Neutrals & Basics", "Moderate Color", "Bright & Vibrant"]
    }
]

def get_random_questions(total=6):
    remaining = total - 1
    return [GENDER_QUESTION] + random.sample(QUESTION_BANK, remaining)
