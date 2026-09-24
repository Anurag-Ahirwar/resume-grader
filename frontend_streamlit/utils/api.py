import requests
from utils.auth import get_auth_header

API_BASE = "http://127.0.0.1:8000"

def upload_pdfs(files):
    url = f"{API_BASE}/resumes/upload"
    response = requests.post(url, files=files, headers=get_auth_header())
    return response.json()

def upload_csv(csv_bytes, filename="resumes.csv"):
    url = f"{API_BASE}/resumes/upload-csv"
    response = requests.post(
        url,
        files={"file": (filename, csv_bytes, "text/csv")},
        headers=get_auth_header(),
    )
    response.raise_for_status()
    return response.json()

def process_resume(upload_id):
    url = f"{API_BASE}/resumes/process/{upload_id}"
    response = requests.post(url, headers=get_auth_header())
    return response.json()

def get_resume_list(params=None):
    url = f"{API_BASE}/resumes"
    response = requests.get(url, params=params or {}, headers=get_auth_header())
    return response.json()

def get_resume_detail(resume_id):
    url = f"{API_BASE}/resumes/{resume_id}"
    response = requests.get(url, headers=get_auth_header())
    return response.json()

def export_as(format):
    url = f"{API_BASE}/export/{format}"
    response = requests.get(url, headers=get_auth_header())
    return response

def reset_db():
    return requests.post(f"{API_BASE}/admin/reset-db", headers=get_auth_header()).json()
