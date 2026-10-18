// Roles page logic: fetch 12+ roles, handle search/filtering, confirm role change, and navigate to Step 2

let allRoles = [];
let currentProfile = null;
let currentSelectedRoleId = "";
let pendingRoleChange = null;

async function initRoles() {
  const container = document.getElementById("roles-grid");
  UI.showLoading(container, "Loading career roles...");

  try {
    // 1. Get student profile to highlight selected role and render step bar
    const profileRes = await API.get("/api/profile");
    currentProfile = profileRes.data.profile || {};
    currentSelectedRoleId = currentProfile.selected_role_id || "";

    UI.renderStepBar(1, currentProfile);

    // 2. Fetch all roles
    const rolesRes = await API.get("/api/roles");
    allRoles = rolesRes.data || [];

    renderRoles(allRoles);
    updateBannerAndButtons();
  } catch (err) {
    UI.toast("Failed to load roles: " + err.message, "error");
  }
}

function updateBannerAndButtons() {
  const banner = document.getElementById("selected-role-banner");
  const bannerTitle = document.getElementById("banner-role-title");
  const bannerDesc = document.getElementById("banner-role-desc");
  const footerBtn = document.getElementById("footer-continue-btn");
  const continueBtn = document.getElementById("continue-skill-gap-btn");

  const selectedRole = allRoles.find(r => r.id === currentSelectedRoleId);

  if (selectedRole) {
    if (banner) {
      banner.style.display = "block";
      bannerTitle.textContent = selectedRole.title;
      bannerDesc.textContent = selectedRole.description;
    }
    if (footerBtn) {
      footerBtn.disabled = false;
      footerBtn.onclick = () => window.location.href = "/pages/skill-gap.html";
    }
    if (continueBtn) {
      continueBtn.onclick = () => window.location.href = "/pages/skill-gap.html";
    }
  } else {
    if (banner) banner.style.display = "none";
    if (footerBtn) {
      footerBtn.disabled = true;
      footerBtn.onclick = null;
    }
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
    card.style.cursor = "pointer";
    if (isSelected) {
      card.style.borderColor = "#2563eb";
      card.style.boxShadow = "0 0 0 2px #2563eb";
      card.style.backgroundColor = "#f8faff";
    }

    // Required skills badges
    const skillsHtml = role.requiredSkills.slice(0, 6).map(s => {
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
          ${isSelected ? '<span class="badge badge-bonus" style="font-size: 0.8rem; padding: 4px 8px;">✓ Selected</span>' : ''}
        </div>
        <p style="font-size: 0.88rem; color: #64748b; line-height: 1.5; margin-bottom: 16px;">${role.description}</p>
        
        <div style="margin-bottom: 16px;">
          <div style="font-size: 0.78rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px;">Key Required Skills</div>
          <div style="display:flex; flex-wrap:wrap;">${skillsHtml}</div>
        </div>
      </div>

      <div style="padding-top: 16px; border-top: 1px solid #e2e8f0; display:flex; flex-direction:column; gap: 8px;">
        <button class="btn ${isSelected ? 'btn-secondary' : 'btn-primary'}" style="width: 100%; padding: 8px 14px; font-size: 0.88rem;" onclick="requestSelectRole('${role.id}', '${role.title}')">
          ${isSelected ? 'Selected (Active Target)' : 'Select This Role'}
        </button>
        ${isSelected ? `
          <button class="btn btn-primary" style="width: 100%; padding: 10px 14px; font-weight: 600; font-size: 0.9rem;" onclick="window.location.href='/pages/skill-gap.html'">
            Continue to Skill Gap Analysis →
          </button>
        ` : ''}
      </div>
    `;

    container.appendChild(card);
  });
}

function requestSelectRole(roleId, title) {
  if (currentSelectedRoleId && currentSelectedRoleId !== roleId) {
    // Show confirmation modal
    pendingRoleChange = { roleId, title };
    const modal = document.getElementById("role-confirm-modal");
    if (modal) modal.style.display = "flex";
  } else {
    executeSelectRole(roleId, title);
  }
}

async function executeSelectRole(roleId, title) {
  try {
    await API.put("/api/profile/role", { role_id: roleId });
    currentSelectedRoleId = roleId;
    if (currentProfile) currentProfile.selected_role_id = roleId;
    UI.toast(`Target role updated to '${title}'!`, "success");
    UI.renderStepBar(1, currentProfile);
    renderRoles(allRoles);
    updateBannerAndButtons();
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

  // Confirmation modal listeners
  const modal = document.getElementById("role-confirm-modal");
  const cancelBtn = document.getElementById("cancel-change-btn");
  const confirmBtn = document.getElementById("confirm-change-btn");

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      pendingRoleChange = null;
      if (modal) modal.style.display = "none";
    });
  }

  if (confirmBtn) {
    confirmBtn.addEventListener("click", () => {
      if (pendingRoleChange) {
        executeSelectRole(pendingRoleChange.roleId, pendingRoleChange.title);
        pendingRoleChange = null;
      }
      if (modal) modal.style.display = "none";
    });
  }
});
