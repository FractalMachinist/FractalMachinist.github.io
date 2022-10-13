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

// --------- SkillSelectionFlags --------------

// Construct the initial SkillSelectionFlagsDiv
constructSkillSelectionFlagsDiv = () => {
    const SkillSelectionFlagsDiv = document.createElement('div')
    SkillSelectionFlagsDiv.setAttribute('id', 'SkillSelectionFlagsDiv');
    // SkillSelectionFlagsDiv.setAttribute(
    //     'style',
    //     'position:absolute; right:0; top:0; bottom:0; width:20px; z-index: -1;'
    // )

    return SkillSelectionFlagsDiv
}

var baseSkillSelectionFlagsDiv = constructSkillSelectionFlagsDiv()

const resumeBody = document.getElementById('resume_body')
resumeBody.appendChild(baseSkillSelectionFlagsDiv)

const scrollElem = document.getElementById('resume_main')

constructSkillSelectionFlags = () => {
    // Collect newest size information
    height = scrollElem.scrollHeight + scrollElem.getBoundingClientRect().top;

    console.log("Height is", height)
    // return
    
    getHeightFraction = (el) => el.getBoundingClientRect().top / height

    // Start constructing new SkillSelectionFlagsDiv
    const newSkillSelectionFlagsDiv = constructSkillSelectionFlagsDiv();

    
    // Construct and update Skill Selection Flags
    document.querySelectorAll(`#resume_main .Skill`).forEach(skill => {
        // Gather the position of the skill in the window
        const heightPercent = `${(getHeightFraction(skill)*99).toFixed(2)}%`;

        // Construct the associated flag and set its ties to styling and selectability
        const SkillSelectionFlag = document.createElement('div')
        SkillSelectionFlag.setAttribute('style', `position:absolute; top:${heightPercent};`)
        SkillSelectionFlag.setAttribute('data-skill', skill.dataset.skill)
        SkillSelectionFlag.classList.add('SkillSelectionFlag')

        // Sync the newly constructed flag with the current state of the skill
        Array.from(['Skill_Selected', 'Skill_Identified', 'Skill_Rejected']).forEach((skill_str) => {
            if (skill.classList.contains(skill_str)) {
                SkillSelectionFlag.classList.add(skill_str);
            }
        })

        // Allow flags to respond to their associated skills being moused over
        skill.addEventListener('mouseenter', (skill) => SkillSelectionFlag.classList.add('SourceSkillExpanded'))
        skill.addEventListener('mouseleave', (skill) => SkillSelectionFlag.classList.remove('SourceSkillExpanded'))

        // Add the constructed flag to the upcoming flags div
        newSkillSelectionFlagsDiv.appendChild(SkillSelectionFlag);
    })


    // Run *one* DOM update with the finished new flags
    resumeBody.replaceChild(newSkillSelectionFlagsDiv, baseSkillSelectionFlagsDiv)
    baseSkillSelectionFlagsDiv = newSkillSelectionFlagsDiv;

}

constructSkillSelectionFlags();


// Only rebuild the flags when the window's size has been stable for 200ms
// Credit to https://stackoverflow.com/a/15205745
var globalResizeTimer = null;
window.addEventListener('resize', () => {
    if (globalResizeTimer != null) window.clearTimeout(globalResizeTimer);
    globalResizeTimer = window.setTimeout(constructSkillSelectionFlags, 200);
})

// window.addEventListener('resize', constructSkillSelectionFlags);

