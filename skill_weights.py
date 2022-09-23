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
        "Unix":0.01,
        "Soft":0.05,
        "Python":0.01
    }, index=pd.Index(skill_cat.category_to_skills.keys(), name="category")).fillna(0)


def get_job_skill_weights(raw_job_details:dict, list_weight:float = 4/5.0, collapse_categories=True, use_category_bias=True):
    # Construct dataframe from raw job details, 
    #   summing between skills listed under multiple teal categories, 
    #   and filtered by skills I have categories for (a loose standin for skills present on the resume).
    job_skill_text_data = pd.concat(
        {key: jsw.extract_skill_counts(value) for key, value in raw_job_details.items()},
        names=["id"]
    ).groupby(level=["id","skill","skill text"]).sum()#.query("`skill`.isin(@skill_cat.skill_to_categories.keys())").sort_index()

    # Compute the share of their job each entry represents
    jst_counts = job_skill_text_data.pop("count")
    job_skill_text_data["share of job"] = jst_counts / jst_counts.groupby(level="id").sum()

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
            "skill text default":skill_cat.skill_to_skill_title[skill_name],
            "num categories":len(categories_skill_is_in), # This skill will appear in `n` categories, so we'll divide it by `n` to keep it conserved.
        } for job_id in raw_job_details.keys()
            for skill_name, categories_skill_is_in in skill_cat.skill_to_categories.items()
                for category in categories_skill_is_in
    ]).set_index(["id", "category", "skill"])
    
    # Join information about (how popular a skill was in the job listing) with 
    #     (how many categories that skill is represented in) setting a default `1` for uncategorized skillls
    #     and a default `0` popularity for skills not in the listing.
    # Skills which are not in the listing have 'NaN' in their `skill text` column, and a waiting replacement in
    #     their `skill text default` column.

    jcst_data = job_skill_text_data.reset_index("skill text").join(jobs_categories_skills_data, how='outer')
    jcst_data.fillna({
            "num categories":1, 
            "share of job":0, 
            "skill text":jcst_data.pop("skill text default")
        }, inplace=True)

    # Normalize against double-counting skills which appear in multiple categories, by dividing by however many categories they're in.
    jcst_data["share of job"] = jcst_data["share of job"] / jcst_data.pop("num categories")

    # Return to desired index configuration
    jcst_data = jcst_data.reset_index().set_index(["id", "category", "skill", "skill text"]).sort_index()

    # Separately from how popular a skill was in the job listing, some skills need to be displayed because
    #     they are in a category of skills the listing mentions often, but they are not mentioned by name.
    #
    # To manage this, skills contribute indirectly to all the other skills they share a category with.
    #
    # Each skill keeps `list_weight` of its `share of job` for itself, contributing directly to its weight.
    #
    # Additionally, `1-list_weight` of each skill's `share of job` gets divided equally between all the categories
    #     that skill is in, then sub-divided equally between all the skills in that category.
    #
    # skill -(divides evenly between)-> categories skill is in -(divides evenly between)-> skills in that category
    # --NOT--
    # skill -(divides evenly between)-> every skill in every category skill is in
    #
    # --Example--
    # If skill S is in category 'A' with 10 skills (A1-A9 and S), and in category 'B' with 3 total (B1, B2, and S),
    # and S is only in those 2 categories,
    #     A1 will receive   1/10 * 1/2 * (1-list_weight)   of S's share of the job listing,
    # and B1 will receive   1/3  * 1/2 * (1-list_weight)   of S's share of the job listing,
    # and S  will receive   1/10 * 1/2 * (1-list_weight)   of its own share via category A,
    # and S  will receive   1/3  * 1/2 * (1-list_weight)   of its own share via category B.
    # Additionally, S will receive from A1-A9, and from B1-2, in the same way.
    #
    # In practice, this second 'implied' contribution is averaged within each job&category and added
    #     to each skill's first 'direct' contribution. 
    #
    # Because pandas does wonderful broadcasting,
    #     the mean of a category's indirect contribution broadcasts to all the skills in that category,
    #     conserving our total weights so that each job's weights sum to 1.
    #
    # Finally, this is assigned to a new 'skill weight' column, preserving each skill's original share of 
    #     the base listing. This is not *strictly* necessary for the final product, but it's excellent
    #     for development and debugging.

    jcst_data["skill weight"] = (jcst_data["share of job"]*list_weight + (jcst_data["share of job"]*(1-list_weight)).groupby(level=[0,1]).mean())


    # Some categories are foundational, even when they aren't mentioned at all.
    # Skills in thouse categories should be biased towards getting displayed.
    # Currently, this is done in a way which conserves total weight per job.
    # Modify these biases above.
    if use_category_bias:
        jcst_data["skill weight"] = (jcst_data["skill weight"] * (1-category_biases.sum())) + (category_biases/jcst_data.groupby(level=["id","category"]).size())
    
    # Sometimes, it's useful to know the category which provided a skill's indirect contribution.
    # However, by default, skills don't get displayed with their category, so sum out the categories.
    if collapse_categories:
        return jcst_data.groupby(level=["id","skill","skill text"]).sum()
    else:
        return jcst_data


    