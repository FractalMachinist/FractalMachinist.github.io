import json

skill_to_categories = None
category_to_skills = None
def _refresh():
    global skill_to_categories
    global category_to_skills
    with open("personal_track/category_to_skills.json", 'r') as sc_f:
        category_to_skills = {s: set(cs) for s, cs in json.load(sc_f).items()}

    skill_to_categories = {}
    for cat, skills in category_to_skills.items():
        for skill in skills:
            skill_to_categories.setdefault(skill, set()).add(cat)
            
_refresh()