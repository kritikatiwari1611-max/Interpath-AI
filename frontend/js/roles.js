// Roles page logic: fetch 12+ roles, handle search/filtering, and update target role

let allRoles = [];
let currentSelectedRoleId = "";

async function initRoles() {
  const container = document.getElementById("roles-grid");
  UI.showLoading(container, "Loading career roles...");

  try {
    // 1. Get student current profile to highlight selected role
    const profileRes = await API.get("/api/profile");
    currentSelectedRoleId = profileRes.data.profile.selected_role_id || "";

    // 2. Fetch all roles
    const rolesRes = await API.get("/api/roles");
    allRoles = rolesRes.data || [];

    renderRoles(allRoles);
  } catch (err) {
    UI.toast("Failed to load roles: " + err.message, "error");
  }
}

function renderRoles(roles) {
  const container = document.getElementById("roles-grid");
  container.innerHTML = "";

  if (roles.length === 0) {
    UI.showEmpty(container, "No matching roles found.");
    return;
  }

  roles.forEach((role) => {
    const isSelected = (role.id === currentSelectedRoleId);
    const card = document.createElement("div");
    card.className = "card";
    card.style.display = "flex";
    card.style.flexDirection = "column";
    card.style.justifyContent = "space-between";
    card.style.transition = "transform 0.2s, border-color 0.2s";
    if (isSelected) {
      card.style.borderColor = "#2563eb";
      card.style.boxShadow = "0 0 0 2px #2563eb";
    }

    // Required skills badges
    const skillsHtml = role.requiredSkills.slice(0, 5).map(s => {
      let badgeClass = "badge-important";
      if (s.importance === "core") badgeClass = "badge-core";
      else if (s.importance === "bonus") badgeClass = "badge-bonus";
      return `<span class="badge ${badgeClass}" style="margin: 2px;">${s.name}</span>`;
    }).join("");

    card.innerHTML = `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 12px;">
          <div>
            <span class="badge ${role.category === 'Technical' ? 'badge-tech' : 'badge-important'}" style="margin-bottom: 6px;">${role.category}</span>
            <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a;">${role.title}</h3>
          </div>
          ${isSelected ? '<span class="badge badge-bonus" style="font-size: 0.8rem; padding: 4px 8px;">Active Target Role</span>' : ''}
        </div>
        <p style="font-size: 0.88rem; color: #64748b; line-height: 1.5; margin-bottom: 16px;">${role.description}</p>
        
        <div style="margin-bottom: 16px;">
          <div style="font-size: 0.78rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px;">Key Required Skills</div>
          <div style="display:flex; flex-wrap:wrap;">${skillsHtml}</div>
        </div>
      </div>

      <div style="padding-top: 16px; border-top: 1px solid #e2e8f0; display:flex; gap: 8px;">
        <button class="btn ${isSelected ? 'btn-secondary' : 'btn-primary'}" style="flex: 1; padding: 8px 14px; font-size: 0.85rem;" onclick="selectRole('${role.id}', '${role.title}')">
          ${isSelected ? 'Selected (Active)' : 'Select Target Role'}
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

async function selectRole(roleId, title) {
  try {
    await API.put("/api/profile/role", { role_id: roleId });
    currentSelectedRoleId = roleId;
    UI.toast(`Target role updated to '${title}'! Roadmap and skill gap recalculated.`, "success");
    renderRoles(allRoles);
  } catch (err) {
    UI.toast("Failed to update role: " + err.message, "error");
  }
}

function filterRoles() {
  const query = document.getElementById("search-input").value.toLowerCase();
  const category = document.getElementById("category-filter").value;

  const filtered = allRoles.filter(r => {
    const matchesQuery = r.title.toLowerCase().includes(query) || 
                         r.description.toLowerCase().includes(query) ||
                         r.requiredSkills.some(s => s.name.toLowerCase().includes(query));
    const matchesCategory = (category === "all" || r.category.toLowerCase() === category.toLowerCase());
    return matchesQuery && matchesCategory;
  });

  renderRoles(filtered);
}

document.addEventListener("DOMContentLoaded", () => {
  initRoles();
  document.getElementById("search-input").addEventListener("input", filterRoles);
  document.getElementById("category-filter").addEventListener("change", filterRoles);
});
