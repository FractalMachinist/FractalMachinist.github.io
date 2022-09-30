from jobs_skills_weights import teal_auth_header
import datetime, requests

stati = {
    "applying":"38b09bef-2c24-48b0-984a-fa0e5b0c060a",
    "applied":"5689f93d-a084-489c-9a6a-7d74b155b49a",
    "archived":"525a1031-d9be-46fe-b825-c75588a25caf"
}

def mark_status(job_id, status_key_or_id='applied', *args, **kwargs):
    auth_header = teal_auth_header(*args, **kwargs);
    
    json = {
        "data":{
            "type":"user_job_posts",
            "relationships":{"status":{"data":{
                "type":"status",
                "id":stati.get(status_key_or_id.lower(), status_key_or_id)
            }}}
        }
    }
    
    if json["data"]["relationships"]["status"]["data"]["id"] == stati["applied"]:
        json["data"]["attributes"] = {"applied_at":datetime.date.today().strftime("%Y-%m-%dT%H:%M")}
    
    return requests.put(
        f"https://company.service.tealhq.com/user_job_posts/{job_id}",
        json=json,
        headers={"Authorization":auth_header,
                 "Content-type":'application/vnd.api+json'}
    )