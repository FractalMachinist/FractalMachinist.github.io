import pandas as pd, skill_cat, multiprocessing.dummy
import jobs_skills_weights as jsw

def get_job_descriptions(raw_job_details:dict) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id":key, 
            "job description": data["attributes"]["job_description"]
        } for key, data in raw_job_details.items()
    ]).set_index("id")

def get_job_skill_counts(raw_job_details:dict) -> pd.DataFrame:
    return pd.concat(
        {key: jsw.extract_skill_counts(value) for key, value in raw_job_details.items()},
        names=["id"]
    )

# What fraction of a resume should be guaranteed dedicated to these categories?
category_biases = pd.Series({
        "Data Code":0.05,
        "Data Engineering":0.1,
        "Writing":0.05,
        "Soft":0.1,
        "Unix":0.025,
        "Python":0.1,
    }, index=pd.Index(skill_cat.category_to_skills.keys(), name="category")).fillna(0)


def get_job_skill_weights(raw_job_details:dict, list_weight:float = 4/5.0, collapse_categories=True, use_category_bias=True):
    # Construct dataframe from raw job details, 
    #   summing between skills listed under multiple teal categories, 
    #   and filtered by skills I have categories for (a loose standin for skills present on the resume).
    job_skill_text_shares = pd.concat(
        {key: jsw.extract_skill_counts(value) for key, value in raw_job_details.items()},
        names=["id"]
    ).groupby(level=["id","skill","skill text"]).sum().query("`skill`.isin(@skill_cat.skill_to_categories.keys())").sort_index()

    # Compute the share of their job each entry represents
    jst_counts = job_skill_text_shares.pop("count")
    job_skill_text_shares["share of job"] = jst_counts / jst_counts.groupby(level="id").sum()

    # Prepare a dataframe of every combination of (job, category, skill-in-category), 
    #   prefilled with the share of the job listing each skill represents or zero if not present, 
    #   divided equally among the categories that skill is in.
    #
    # This could probably be done with some kind of numpy iterable, which could be a lot faster.
    # #OPTIMIZE_IF_NEEDED
    jcs_num_categories = pd.DataFrame([{
            "id":job_id,
            "category":category,
            "skill":skill_name,
            "share of job":len(categories_skill_is_in), # This skill will appear in `n` categories, so we'll divide it by `n` to keep it conserved.
        } for job_id in raw_job_details.keys()
            for skill_name, categories_skill_is_in in skill_cat.skill_to_categories.items()
                for category in categories_skill_is_in
    ]).set_index(["id", "category", "skill"])
    
    # TODO: Document!
    jcst_data = (job_skill_text_shares / jcs_num_categories).reset_index().fillna({"share of job":0}) # jcst_data => jobs_categories_skills_text_data
    jcst_data["skill text"].fillna(jcst_data["skill"].apply(skill_cat.skill_to_skill_title.get), inplace=True)
    jcst_data = jcst_data.set_index(["id","category","skill","skill text"]).sort_index().rename(columns={"share of job":"skill weight"})


    # TODO: Document!
    jcst_wc = (jcst_data*list_weight + (jcst_data*(1-list_weight)).groupby(level=[0,1]).mean())


    # TODO: Document!
    if use_category_bias:
        jcst_wc["skill weight"] = (jcst_wc["skill weight"] * (1-category_biases.sum())) + (category_biases/jcst_wc.groupby(level=["id","category"]).size())
    
    if collapse_categories:
        return jcst_wc.groupby(level=["id","skill","skill text"]).sum()
    else:
        return jcst_wc


    