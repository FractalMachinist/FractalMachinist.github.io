import pandas as pd, skill_cat, multiprocessing.dummy
import jobs_skills_weights as jsw

def get_job_descriptions(raw_job_details:dict) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id":key, 
            "job description": data["attributes"]["job_description"]
        } for key, data in raw_job_details.items()
    ]).set_index("id")

def get_job_skills_data(raw_job_details:dict) -> pd.DataFrame:
    return pd.concat(
        {key: jsw.extract_skills_data(value) for key, value in raw_job_details.items()},
        names=["id"]
    )

category_biases = pd.Series({
        "Code":0.3,
        "Data":0.2,
        "Writing":0.1,
        "Soft":0.1,
    }, index=pd.Index(skill_cat.category_to_skills.keys(), name="category")).fillna(0)



def get_job_skill_weights(raw_job_details:dict, list_weight:float = 4/5.0, collapse_categories=True, use_category_bias=True):
    # Construct dataframe from raw job details, 
    #   summing between skills listed under multiple teal categories, 
    #   and filtered by skills I have categories for (a loose standin for skills present on the resume).
    job_skills_data = get_job_skills_data(raw_job_details=raw_job_details)\
        .groupby(level=[0,2]).sum()\
        .query("`skill`.isin(@skill_cat.skill_to_categories.keys())")

    # Compute the share of each job a skill appears to represent.
    job_skills_data["share of job"] = job_skills_data["count"] / job_skills_data["count"].groupby("id").sum()

    # Prepare a dataframe of every combination of (job, category, skill-in-category), 
    #   prefilled with the share of the job listing each skill represents or zero if not present, 
    #   divided equally among the categories that skill is in.
    #
    # This could probably be done with some kind of numpy iterable, which could be a lot faster.
    # #OPTIMIZE_IF_NEEDED
    jobs_categories_skills_data = pd.DataFrame([{
            "id":job_id,
            "category":category,
            "skill":skill_name,
            "share of job":job_skills_data["share of job"].get((job_id, skill_name), 0)/float(len(categories_skill_is_in)),
        } for job_id in raw_job_details.keys()
            for skill_name, categories_skill_is_in in skill_cat.skill_to_categories.items()
                for category in categories_skill_is_in
    ]).set_index(["id", "category", "skill"]).sort_index() # Sort the index so it's easy to read. Not a requirement.
    

    # This relies on pandas' implicit joins.
    # 
    # We want to conserve the `share of job` totals, 
    #   while allowing the presence of some skills to imply the importance
    #   of other skills in the same category.
    #
    # For each (job, category, skill) nicknamed `jcs`:
    #   - `list_weight` * `share of job` contributes directly to that `jcs`'s final weight. I would call this the `listed contribution`,
    #       because it arises directly from whether a skill was listed in the job posting.
    #   - `1-list_weight`*`share of job` is divided equally among all `jcs`s in that (job, category). 
    #       This is done by grouping by (job, category) and taking the mean. I would call this the `implicit contribution`.
    #
    # When `implicit contribution` gets added to `listed contribution`, pandas implies a join across common columns in their MultiIndex.
    # Specifically, this join duplicates the `implicit contribution` from each (job, category) to every `jcs` within that (job, category).
    # Because `implicit contribution`s get averaged over `n` `jcs`s within a (job, category), 
    #   then duplicated over those same `n` `jcs`s, 
    #   the total contribution is conserved.
    soj = jobs_categories_skills_data.pop("share of job")
    category_skill_weighted_contributions = soj*list_weight + (soj*(1-list_weight)).groupby(level=[0,1]).mean()


    # It may be desirable to include some categories, even if they weren't listed in the job posting.
    if use_category_bias:
        category_skill_weighted_contributions += category_biases



    # If `collapse_categories` is truthy,
    #   sum each skill's weighted contribution from all the categories that skill is in, returning the weighted contribution of each skill to each job.
    # Else,
    #   return the weighted contribution broken down by category and skill (for analysis purposes).
    if collapse_categories:
        return category_skill_weighted_contributions.groupby(level=[0, 2]).sum()
    else:
        return category_skill_weighted_contributions





    