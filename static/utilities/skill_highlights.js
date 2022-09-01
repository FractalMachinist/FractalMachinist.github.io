getSkills = (skill_str) => document.querySelectorAll(`[data-skill='${skill_str}']`)
onTheseSkillsClassList = (skill_str, classListFunc) => getSkills(skill_str).forEach((matching_skill) => classListFunc(matching_skill.classList))

setSkillClass = (skill_str, classStr = "Expanded") => onTheseSkillsClassList(skill_str, classList => classList.add(classStr))
rmvSkillClass = (skill_str, classStr = "Expanded") => onTheseSkillsClassList(skill_str, classList => classList.remove(classStr))
tglSkillClass = (skill_str, classStr = "Expanded") => onTheseSkillsClassList(skill_str, classList => classList.toggle(classStr))


Array.from(document.getElementsByClassName('Skill')).forEach(skill => {
    skill.addEventListener('mouseenter', (event) => setSkillClass(skill.dataset.skill));
    skill.addEventListener('mouseleave', (event) => rmvSkillClass(skill.dataset.skill));
    skill.addEventListener('click',      (event) => tglSkillClass(skill.dataset.skill, "Skill_Selected"))
    skill.addEventListener('click',      (event) => rmvSkillClass(skill.dataset.skill))
})