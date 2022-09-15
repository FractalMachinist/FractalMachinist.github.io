import json, requests, pandas as pd, multiprocessing.dummy, pathlib, stemming, skill_cat
__location__ = pathlib.Path(__file__).parent

# TODO: I should/could probably directly use the tool Teal is using. They support it on GitHub.

def teal_auth_header(fpath:str=f"{__location__}/personal_track/teal_auth.txt"):
    # TODO: Request new auth headers when this one fails
    with open(fpath, 'r') as teal_auth_header_f:
        auth_header = teal_auth_header_f.read()
    return auth_header

def download_user_job_posts(*args, enforce_bookmarked:bool=True, **kwargs):
    auth_header = teal_auth_header(*args, **kwargs)
    p = multiprocessing.dummy.Pool()
    return list(p.map(
        lambda job: requests.get(f"https://company.service.tealhq.com/user_job_posts/{job['id']}", headers={'Authorization':auth_header}).json()["data"],
        requests.get(f"https://company.service.tealhq.com/user_job_posts{'?include_states=bookmarked' if enforce_bookmarked else ''}", headers={"Authorization":auth_header}).json()["data"]))


def get_jobs_skills_weights(*args, **kwargs):
    jobs_skills = pd.DataFrame([
        {
            ("post", "id"):post["id"],
            ("post", "name"): post["attributes"]["company_name"], 
            ("post", "excitement"): post["attributes"]["excitement"],
            ("skill", "category"): post_skill_details["category"],
            ("skill", "name"): post_skill_key, 
            ("skill", "name_stem"): stemming.stem(post_skill_key.lower()),
            ("skill", "count"):max(1, len(post_skill_details["positions"])), # Teal reports some skills, but doesn't assign them in-text presence. Minimum 1 as a guess.
        } for post in download_user_job_posts(*args, **kwargs)
            for post_skill_key, post_skill_details in post["attributes"]["skills"]["tealPhrases"].items()
    ])
    jobs_skills.columns = pd.MultiIndex.from_tuples(jobs_skills.columns)

    jobs_skill_total = jobs_skills.groupby(("post", "id")).agg(job_skill_total=(("skill", "count"), "sum"))
    jobs_skills[("skill", "share")] = jobs_skills.apply(lambda js: js[("skill", "count")] / jobs_skill_total.loc[js[("post", "id")]], axis=1)
    jobs_skills = jobs_skills.drop(("skill", "count"), axis=1)
    
    
    
    jobs_skills[("resume", "category")] = [
        skill_cat.skill_to_categories.get(js, set()) 
        for js in jobs_skills[("skill", "name_stem")]
    ]
    
    return jobs_skills.set_index([("post", "name"), ("post", "id"), ("skill", "name_stem"), ("skill", "name")]).sort_index()