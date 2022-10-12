Array.from(document.querySelectorAll(`:not(.Skill)[data-cnh-density]`)).forEach(densityElem => {
    dataset = densityElem.dataset
    density = (parseFloat(dataset.cnhDensity)*100).toFixed(3)+"ppl"
    weight = (parseFloat(dataset.cnhWeight) * 100).toFixed(3)+"%"
    cost = parseFloat(dataset.cnhCost).toFixed(1)
    
    densityElem.title = `${density} (${weight}/${cost})`
})

Array.from(document.querySelectorAll(`.Skill[data-cnh-density]`)).forEach(densityElem => {
    densityElem.title = (densityElem.dataset.skillWeight*100).toFixed(2)+"%"
})


Array.from(document.querySelectorAll(`[data-cnh-met-threshold="False"]`)).forEach(weakElem => {
    weakElem.style.setProperty("text-decoration", "line-through");
})


Array.from(document.querySelectorAll(`.Skill`)).forEach(
    densityElem => densityElem.classList.add(densityElem.dataset.cnhMetThreshold=="True" ? 'Skill_Selected' : 'Skill_Rejected')
)


