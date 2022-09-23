getSkills = (skill_str) => document.querySelectorAll(`[data-skill='${skill_str}']`)
onTheseSkillsClassList = (skill_str, classListFunc) => getSkills(skill_str).forEach((matching_skill) => classListFunc(matching_skill.classList))

setSkillClass = (skill_str, classStr = "Expanded") => onTheseSkillsClassList(skill_str, classList => classList.add(classStr))
rmvSkillClass = (skill_str, classStr = "Expanded") => onTheseSkillsClassList(skill_str, classList => classList.remove(classStr))

triSkillClass = (skill_str, classStr = "Skill_Selected") => onTheseSkillsClassList(skill_str, (classList) => {
    var options = new Set(["Skill_Selected", "Skill_Identified", "Skill_Rejected"]);

    if (classStr == "Skill_Selected" && (classList.contains("Skill_Identified") || classList.contains("Skill_Rejected"))){
        // If it's a neutral click and the skill is already Identified or Rejected, put the skill back to neutral.
        // This is only the right design decision if users rarely want to switch directly from I/R to S.
        // During early testing, it seemed simple that clearing many skills should mean just clicking on them. I'm open to feedback.
        classList.remove(...options);
    } else {
        options.delete(classStr);
        classList.remove(...options);
        classList.toggle(classStr);
    }
})



Array.from(document.getElementsByClassName('Skill')).forEach(skill => {
    skill.addEventListener('mouseenter', (event) => setSkillClass(skill.dataset.skill));
    skill.addEventListener('mouseleave', (event) => rmvSkillClass(skill.dataset.skill));
    skill.addEventListener('click',      (event) => triSkillClass(skill.dataset.skill, event.ctrlKey ? "Skill_Rejected"   : event.altKey ? "Skill_Identified" : "Skill_Selected"));
})