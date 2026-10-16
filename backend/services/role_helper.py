import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR

# Global dictionary cache for rapid in-memory lookups
# Label: DICTIONARY DATA STRUCTURE - Role lookup by id O(1)
_ROLES_CACHE = {}

def get_all_roles():
    """Loads and returns all roles from knowledge_base/roles.json."""
    global _ROLES_CACHE
    if not _ROLES_CACHE:
        roles_path = KNOWLEDGE_BASE_DIR / "roles.json"
        if not roles_path.exists():
            return []
        with open(roles_path, "r", encoding="utf-8") as f:
            roles_list = json.load(f)
            # Store in dictionary by id
            for r in roles_list:
                _ROLES_CACHE[r["id"]] = r
    return list(_ROLES_CACHE.values())

def get_role_by_id(role_id: str):
    """Fetches a specific role definition by role_id in O(1) time."""
    get_all_roles()
    return _ROLES_CACHE.get(role_id)
