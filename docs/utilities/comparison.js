// Array.from(document.querySelectorAll(`.Skill[data-skill-weight='0.0'][data-skill-share-of-job='0.0']`)).forEach(emptySkill => {
//     emptySkill.classList.add("Skill_Identified");
// })

Array.from(document.querySelectorAll(`.Skill:not([data-skill-share-of-job='0.0'])`)).forEach(emptySkill => {
    emptySkill.classList.add("Skill_Selected");
})




Array.from(document.querySelectorAll(`[data-cnh-density]`)).forEach(densityElem => {
    densityElem.title = densityElem.dataset.cnhDensity
})


Array.from(document.querySelectorAll(`[data-cnh-met-threshold="False"]`)).forEach(weakElem => {
    weakElem.style.setProperty("text-decoration", "line-through");
})


Array.from(document.querySelectorAll(`.Skill[data-cnh-met-threshold="False"][data-skill-share-of-job='0.0']`)).filter(
    dE => !dE.classList.contains('Skill_Identified')
).forEach(
    densityElem => densityElem.classList.add('Skill_Rejected')
)


