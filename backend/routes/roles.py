from flask import Blueprint, jsonify
from backend.services.role_helper import get_all_roles, get_role_by_id

roles_bp = Blueprint("roles", __name__)

@roles_bp.route("/roles", methods=["GET"])
def list_roles():
    roles = get_all_roles()
    return jsonify({"ok": True, "data": roles})

@roles_bp.route("/roles/<role_id>", methods=["GET"])
def get_role_detail(role_id):
    role = get_role_by_id(role_id)
    if not role:
        return jsonify({"ok": False, "error": "Role not found."}), 404
    return jsonify({"ok": True, "data": role})
