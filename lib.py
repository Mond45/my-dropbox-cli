from typing import Optional

import requests

from constants import API_BASE_URL


def natural_size(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def register(username: str, password: str):
    r = requests.post(
        f"{API_BASE_URL}/register", json={"username": username, "password": password}
    )
    r.raise_for_status()


def login(username: str, password: str):
    r = requests.post(
        f"{API_BASE_URL}/login", json={"username": username, "password": password}
    )
    r.raise_for_status()
    return r.json()["token"]


def logout(token: str):
    r = requests.post(f"{API_BASE_URL}/logout", headers={"x-session-token": token})
    r.raise_for_status()


def put_file(token: str, file_name: str, content: str):
    r = requests.put(
        f"{API_BASE_URL}/file",
        headers={"x-session-token": token},
        json={"file_name": file_name, "content": content},
    )
    r.raise_for_status()


def get_file(token: str, file_name: str, username: Optional[str] = None):
    r = requests.get(
        f"{API_BASE_URL}/file",
        headers={"x-session-token": token},
        params={"file_name": file_name, "username": username},
    )
    r.raise_for_status()
    return r.content


def list_files(token: str):
    r = requests.get(f"{API_BASE_URL}/files", headers={"x-session-token": token})
    r.raise_for_status()
    return r.json()


def share_file(token: str, file_name: str, target_username: str):
    r = requests.post(
        f"{API_BASE_URL}/share",
        headers={"x-session-token": token},
        json={"file_name": file_name, "username": target_username},
    )
    r.raise_for_status()
