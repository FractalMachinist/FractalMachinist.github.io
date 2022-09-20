import json

skill_to_categories = None
category_to_skills = None
skill_to_skill_title = None
def _refresh():
    global skill_to_categories
    global category_to_skills
    global skill_to_skill_title
    with open("personal_track/category_to_skills.json", 'r') as sc_f:
        category_to_skills = {cat: set(skills) for cat, skills in json.load(sc_f).items()}

    skill_to_categories = {}
    skill_to_skill_title = {}
    for cat, skills in category_to_skills.items():
        for skill in skills:
            skill_to_categories.setdefault(skill.lower(), set()).add(cat)
            skill_to_skill_title[skill.lower()] = skill
            
_refresh()