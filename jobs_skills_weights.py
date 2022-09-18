import json, requests, pandas as pd, multiprocessing.dummy, pathlib, stemming, skill_cat
__location__ = pathlib.Path(__file__).parent

# TODO: I should/could probably directly use the tool Teal is using. They support it on GitHub.

def teal_auth_header(fpath:str=f"{__location__}/personal_track/teal_auth.txt"):
    # TODO: Request new auth headers when this one fails
    with open(fpath, 'r') as teal_auth_header_f:
        auth_header = teal_auth_header_f.read()
    return auth_header

def download_user_job_posts(*args, bookmarked:bool=True, **kwargs):
    auth_header = teal_auth_header(*args, **kwargs)
    p = multiprocessing.dummy.Pool()
    return list(p.map(
        lambda job: requests.get(f"https://company.service.tealhq.com/user_job_posts/{job['id']}", headers={'Authorization':auth_header}).json()["data"],
        requests.get(f"https://company.service.tealhq.com/user_job_posts{'?include_states=bookmarked' if bookmarked else ''}", headers={"Authorization":auth_header}).json()["data"]))


def get_jobs(*args, bookmarked:bool=True, **kwargs):
    auth_header = teal_auth_header(*args, **kwargs)
    job_data = requests.get(f"https://company.service.tealhq.com/user_job_posts{'?include_states=bookmarked' if bookmarked else ''}", headers={"Authorization":auth_header}).json()["data"]
    
    jobs = pd.DataFrame(job_data)
    jobs = jobs.join(pd.DataFrame(jobs.pop("attributes").values.tolist()))[["id", "company_name", "location", "role", "url", "excitement"]]
    return jobs.set_index(["id"])


def get_job_details(job_id, *args, auth_header=None, **kwargs):
    if auth_header is None:
        auth_header = teal_auth_header(*args, **kwargs)
    
    return requests.get(f"https://company.service.tealhq.com/user_job_posts/{job_id}", headers={'Authorization':auth_header}).json()["data"]

# def job_skills(job_id, *args, auth_header=None, **kwargs):
#     if auth_header is None:
#         auth_header = teal_auth_header(*args, **kwargs)
    
#     skills_data = requests.get(f"https://company.service.tealhq.com/user_job_posts/{job_id}", headers={'Authorization':auth_header}).json()["data"]["attributes"]["skills"]["tealPhrases"]
    
#     return skills_data


def extract_skills_data(job_details):
    return pd.DataFrame([{
            "name stem":stemming.stem(skill_name.lower()),
            "name teal":skill_name,
            "count":max(1, len(skill_data["positions"])),
            "teal category":skill_data["category"]
        } for skill_name, skill_data in job_details["attributes"]["skills"]["tealPhrases"].items()
        ], columns=["name stem", "name teal", "count", "teal category"]).groupby(["teal category", "name stem"]).agg({"count":"sum"})

