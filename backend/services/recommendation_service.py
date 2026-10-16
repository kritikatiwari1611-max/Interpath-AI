import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR

_RESOURCES_CACHE = []
_PROJECTS_CACHE = []

def get_all_resources() -> list:
    global _RESOURCES_CACHE
    if not _RESOURCES_CACHE:
        path = KNOWLEDGE_BASE_DIR / "resources.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _RESOURCES_CACHE = json.load(f)
    return _RESOURCES_CACHE

def get_all_projects() -> list:
    global _PROJECTS_CACHE
    if not _PROJECTS_CACHE:
        path = KNOWLEDGE_BASE_DIR / "projects.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _PROJECTS_CACHE = json.load(f)
    return _PROJECTS_CACHE

def recommend_projects_for_role(role_id: str, missing_skills: list = None) -> list:
    projects = get_all_projects()
    if not projects:
        return []
    
    # Filter projects matching role_id or general
    role_projects = [p for p in projects if p.get("role_id") == role_id or p.get("role_id") == "all"]
    return role_projects if role_projects else projects[:3]
