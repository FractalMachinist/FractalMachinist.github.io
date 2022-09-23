Array.from(document.querySelectorAll(`[data-skill-weight='0.0'][data-skill-share-of-job='0.0']`)).forEach(emptySkill => {
    emptySkill.classList.add("Skill_Identified");
})

Array.from(document.querySelectorAll(`:not([data-skill-share-of-job='0.0'])`)).forEach(emptySkill => {
    emptySkill.classList.add("Skill_Selected");
})