// Step 4: Project Portfolio & Custom Project Management Logic

let currentProfile = null;
let recommendedProjects = [];
let customProjects = [];

async function initProjects() {
  const recContainer = document.getElementById("recommended-projects-container");
  const custContainer = document.getElementById("custom-projects-container");
  UI.showLoading(recContainer, "Loading recommended projects for your target role...");
  UI.showLoading(custContainer, "Loading your custom projects...");

  try {
    // 1. Fetch student profile
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};

    if (!currentProfile.selected_role_id) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return;
    }

    UI.renderStepBar(4, currentProfile);

    const roleBadge = document.getElementById("role-badge");
    if (roleBadge) {
      roleBadge.textContent = "Target: " + (currentProfile.role_title || currentProfile.selected_role_id);
    }

    // 2. Fetch projects
    const res = await API.get("/api/projects");
    recommendedProjects = res.data || [];
    customProjects = res.custom_projects || [];

    renderRecommendedProjects();
    renderCustomProjects();
  } catch (err) {
    UI.toast("Failed to load projects: " + err.message, "error");
  }
}

function renderRecommendedProjects() {
  const container = document.getElementById("recommended-projects-container");
  container.innerHTML = "";

  if (recommendedProjects.length === 0) {
    UI.showEmpty(container, "No recommended projects found for this role.");
    return;
  }

  recommendedProjects.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    if (p.is_recommended) {
      card.style.border = "1.5px solid #3b82f6";
    }

    const milestones = p.milestones || [];
    const doneMilestones = p.milestones_done || [];
    const isCompleted = p.status === "completed";
    const isInProgress = p.status === "in_progress";

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:12px;">
        <div style="flex:1; min-width:260px;">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            ${p.is_recommended ? '<span class="badge badge-tech">Role Capstone</span>' : ''}
            <h4 style="font-size:1.15rem; font-weight:700; color:#0f172a; margin:0;">${p.title}</h4>
          </div>
          <p style="font-size:0.88rem; color:#64748b; margin:6px 0 0 0;">${p.description}</p>
        </div>

        <!-- 3-Segmented status control -->
        <div>
          <div class="segmented-status-group">
            <button type="button" class="status-btn ${p.status === 'saved' || p.status === 'pending' ? 'active-pending' : ''}" onclick="updateProjectState('${p.id}', 'saved')">
              Pending / Saved
            </button>
            <button type="button" class="status-btn ${isInProgress ? 'active-in_progress' : ''}" onclick="updateProjectState('${p.id}', 'in_progress')">
              In Progress
            </button>
            <button type="button" class="status-btn ${isCompleted ? 'active-completed' : ''}" onclick="updateProjectState('${p.id}', 'completed')">
              ✓ Completed
            </button>
          </div>
        </div>
      </div>

      <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px;">
        <span class="badge badge-important">Est. ${p.estimated_time || '20 hrs'}</span>
        <span class="badge badge-bonus">${p.difficulty || 'Intermediate'}</span>
        ${(p.required_skills || []).map(s => `<span class="badge badge-tech">${s}</span>`).join("")}
      </div>

      ${p.learning_outcomes && p.learning_outcomes.length > 0 ? `
        <div style="margin-bottom:12px; font-size:0.82rem; color:#475569;">
          <strong>Learning Outcomes:</strong> ${p.learning_outcomes.join(" • ")}
        </div>
      ` : ''}

      <!-- Milestones Checklist -->
      <div style="background:#f8fafc; padding:12px 16px; border-radius:8px; border:1px solid #e2e8f0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <h5 style="font-size:0.85rem; font-weight:700; color:#1e293b; margin:0;">Milestones Checklist:</h5>
          <span style="font-size:0.78rem; color:#64748b;">${doneMilestones.length} of ${milestones.length} done</span>
        </div>
        <div style="display:flex; flex-direction:column; gap:6px;">
          ${milestones.map(m => {
            const isDone = doneMilestones.includes(m.id);
            return `
              <label style="display:flex; align-items:center; gap:8px; font-size:0.85rem; cursor:pointer; ${isDone ? 'text-decoration:line-through; color:#166534;' : 'color:#334155;'}">
                <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleMilestone('${p.id}', '${m.id}', this.checked)">
                ${m.title}
              </label>
            `;
          }).join("")}
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function renderCustomProjects() {
  const container = document.getElementById("custom-projects-container");
  container.innerHTML = "";

  if (customProjects.length === 0) {
    container.innerHTML = `
      <div style="padding:20px; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; text-align:center; color:#64748b; font-size:0.88rem;">
        No custom projects added yet. Use the form above to add your own personal projects.
      </div>
    `;
    return;
  }

  customProjects.forEach(cp => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.background = "#ffffff";
    card.style.border = "1px solid #e2e8f0";

    const techBadges = (cp.tech || "").split(",").map(t => t.trim()).filter(Boolean).map(t => `
      <span class="badge badge-important" style="font-size:0.75rem;">${t}</span>
    `).join("");

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:10px;">
        <div style="flex:1; min-width:240px;">
          <h4 style="font-size:1.1rem; font-weight:700; color:#0f172a; margin:0;">${cp.title}</h4>
          <p style="font-size:0.88rem; color:#475569; margin:4px 0 8px 0; line-height:1.4;">${cp.description}</p>
          <div style="display:flex; flex-wrap:wrap; gap:6px;">${techBadges}</div>
        </div>

        <div style="display:flex; align-items:center; gap:8px;">
          <select class="form-control" style="font-size:0.82rem; padding:4px 8px; width:130px;" onchange="updateCustomProjectState(${cp.id}, this.value)">
            <option value="in_progress" ${cp.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
            <option value="completed" ${cp.status === 'completed' ? 'selected' : ''}>Completed</option>
            <option value="saved" ${cp.status === 'saved' ? 'selected' : ''}>Saved</option>
          </select>
          <button type="button" class="btn btn-secondary" style="color:#ef4444; border-color:#fca5a5; padding:4px 10px; font-size:0.8rem;" onclick="deleteCustomProject(${cp.id})">
            Delete
          </button>
        </div>
      </div>

      <div style="padding-top:10px; border-top:1px solid #f1f5f9; display:flex; gap:16px; flex-wrap:wrap; font-size:0.82rem;">
        ${cp.github_link ? `
          <a href="${cp.github_link}" target="_blank" rel="noopener noreferrer" style="color:#2563eb; font-weight:600; text-decoration:none;">
            🐙 GitHub Repo ↗
          </a>
        ` : ''}
        ${cp.demo_link ? `
          <a href="${cp.demo_link}" target="_blank" rel="noopener noreferrer" style="color:#10b981; font-weight:600; text-decoration:none;">
            🔗 Live Demo ↗
          </a>
        ` : ''}
        ${cp.report_filename ? `
          <a href="/api/uploads/${cp.report_filename}" target="_blank" style="color:#8b5cf6; font-weight:600; text-decoration:none;">
            📄 View Project Report (${cp.report_original_name || 'PDF'}) ↗
          </a>
        ` : ''}
      </div>
    `;

    container.appendChild(card);
  });
}

async function updateProjectState(projectId, status) {
  const proj = recommendedProjects.find(p => p.id === projectId);
  const milestones = proj ? proj.milestones_done : [];
  try {
    await API.put(`/api/projects/${projectId}/status`, {
      status,
      milestones_done: milestones
    });
    if (proj) proj.status = status;
    renderRecommendedProjects();
    UI.toast(`Project status updated to ${status}`, "success");
  } catch (err) {
    UI.toast("Failed to update status: " + err.message, "error");
  }
}

async function toggleMilestone(projectId, milestoneId, isChecked) {
  const proj = recommendedProjects.find(p => p.id === projectId);
  if (!proj) return;

  let list = proj.milestones_done || [];
  if (isChecked) {
    if (!list.includes(milestoneId)) list.push(milestoneId);
  } else {
    list = list.filter(id => id !== milestoneId);
  }
  proj.milestones_done = list;

  const allMilestoneIds = (proj.milestones || []).map(m => m.id);
  const allFinished = allMilestoneIds.length > 0 && allMilestoneIds.every(id => list.includes(id));
  const newStatus = allFinished ? "completed" : (list.length > 0 ? "in_progress" : proj.status);

  try {
    await API.put(`/api/projects/${projectId}/status`, {
      status: newStatus,
      milestones_done: list
    });
    proj.status = newStatus;
    renderRecommendedProjects();
    UI.toast("Milestone progress saved!", "success");
  } catch (err) {
    UI.toast("Failed to update milestone: " + err.message, "error");
  }
}

async function updateCustomProjectState(projId, status) {
  try {
    await API.put(`/api/projects/custom/${projId}/status`, { status });
    const target = customProjects.find(p => p.id === projId);
    if (target) target.status = status;
    UI.toast(`Custom project status updated to ${status}`, "success");
  } catch (err) {
    UI.toast("Failed to update status: " + err.message, "error");
  }
}

async function deleteCustomProject(projId) {
  if (!confirm("Are you sure you want to delete this custom project?")) return;
  try {
    await API.delete(`/api/projects/custom/${projId}`);
    customProjects = customProjects.filter(p => p.id !== projId);
    renderCustomProjects();
    UI.toast("Project removed.", "success");
  } catch (err) {
    UI.toast("Failed to delete project: " + err.message, "error");
  }
}

async function handleCustomProjectSubmit(e) {
  e.preventDefault();
  const saveBtn = document.getElementById("save-cust-btn");
  saveBtn.disabled = true;

  const title = document.getElementById("cust-title").value.trim();
  const tech = document.getElementById("cust-tech").value.trim();
  const description = document.getElementById("cust-description").value.trim();
  const github_link = document.getElementById("cust-github").value.trim();
  const demo_link = document.getElementById("cust-demo").value.trim();
  const status = document.getElementById("cust-status").value;
  const reportFileInput = document.getElementById("cust-report");

  if (github_link && !github_link.startsWith("https://github.com/")) {
    UI.toast("GitHub URL must start with https://github.com/", "error");
    saveBtn.disabled = false;
    return;
  }

  const formData = new FormData();
  formData.append("title", title);
  formData.append("tech", tech);
  formData.append("description", description);
  formData.append("github_link", github_link);
  formData.append("demo_link", demo_link);
  formData.append("status", status);

  if (reportFileInput && reportFileInput.files.length > 0) {
    const file = reportFileInput.files[0];
    if (file.size > 2 * 1024 * 1024) {
      UI.toast("Project report exceeds 2 MB limit.", "error");
      saveBtn.disabled = false;
      return;
    }
    formData.append("report_file", file);
  }

  try {
    const res = await API.postForm("/api/projects/custom", formData);
    UI.toast("Custom project added successfully!", "success");
    document.getElementById("custom-project-form").reset();

    // Reload projects
    const projRes = await API.get("/api/projects");
    customProjects = projRes.custom_projects || [];
    renderCustomProjects();
  } catch (err) {
    UI.toast("Failed to save project: " + err.message, "error");
  } finally {
    saveBtn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initProjects();
  const form = document.getElementById("custom-project-form");
  if (form) {
    form.addEventListener("submit", handleCustomProjectSubmit);
  }
});
