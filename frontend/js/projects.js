// Project recommendations client logic: milestones, status updates

let allProjects = [];

async function loadProjects() {
  const container = document.getElementById("projects-container");
  UI.showLoading(container, "Fetching role-recommended projects...");

  try {
    const res = await API.get("/api/projects");
    allProjects = res.data || [];
    renderProjects();
  } catch (err) {
    UI.toast("Failed to load projects: " + err.message, "error");
  }
}

function renderProjects() {
  const container = document.getElementById("projects-container");
  container.innerHTML = "";

  if (allProjects.length === 0) {
    UI.showEmpty(container, "No projects currently recommended.");
    return;
  }

  allProjects.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    if (p.is_recommended) {
      card.style.border = "1.5px solid #3b82f6";
    }

    const milestones = p.milestones || [];
    const doneMilestones = p.milestones_done || [];

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
        <div>
          ${p.is_recommended ? '<span class="badge badge-tech" style="margin-bottom: 4px;">Recommended for Your Target Role</span>' : ''}
          <h3 style="font-size: 1.15rem; font-weight: 700;">${p.title}</h3>
          <p style="font-size: 0.88rem; color: #64748b; margin-top: 4px;">${p.description}</p>
        </div>
        <div style="display: flex; gap: 8px;">
          <select class="form-control" style="font-size: 0.82rem; padding: 4px 8px; width: 140px;" onchange="updateProjectState('${p.id}', this.value)">
            <option value="saved" ${p.status === 'saved' ? 'selected' : ''}>Saved</option>
            <option value="in_progress" ${p.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
            <option value="completed" ${p.status === 'completed' ? 'selected' : ''}>Completed</option>
          </select>
        </div>
      </div>

      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;">
        <span class="badge badge-important">Est. ${p.estimated_time}</span>
        <span class="badge badge-bonus">${p.difficulty}</span>
        ${(p.required_skills || []).map(s => `<span class="badge badge-tech">${s}</span>`).join("")}
      </div>

      <!-- Milestones Checklist -->
      <div style="background: #f8fafc; padding: 14px 16px; border-radius: 8px; border: 1px solid #e2e8f0;">
        <h4 style="font-size: 0.88rem; font-weight: 600; margin-bottom: 8px; color: #0f172a;">Project Milestones:</h4>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${milestones.map(m => {
            const isDone = doneMilestones.includes(m.id);
            return `
              <label style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; cursor: pointer; ${isDone ? 'text-decoration: line-through; color: #166534;' : ''}">
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

async function updateProjectState(projectId, status) {
  const proj = allProjects.find(p => p.id === projectId);
  const milestones = proj ? proj.milestones_done : [];
  try {
    await API.put(`/api/projects/${projectId}/status`, {
      status,
      milestones_done: milestones
    });
    if (proj) proj.status = status;
    UI.toast(`Project status updated to ${status}`, "success");
  } catch (err) {
    UI.toast("Failed to update status: " + err.message, "error");
  }
}

async function toggleMilestone(projectId, milestoneId, isChecked) {
  const proj = allProjects.find(p => p.id === projectId);
  if (!proj) return;

  let list = proj.milestones_done || [];
  if (isChecked) {
    if (!list.includes(milestoneId)) list.push(milestoneId);
  } else {
    list = list.filter(id => id !== milestoneId);
  }
  proj.milestones_done = list;

  // If all milestones checked, auto-suggest marked as completed
  const allMilestoneIds = (proj.milestones || []).map(m => m.id);
  const allFinished = allMilestoneIds.length > 0 && allMilestoneIds.every(id => list.includes(id));
  const newStatus = allFinished ? "completed" : (list.length > 0 ? "in_progress" : proj.status);

  try {
    await API.put(`/api/projects/${projectId}/status`, {
      status: newStatus,
      milestones_done: list
    });
    proj.status = newStatus;
    renderProjects();
    UI.toast("Milestone progress saved!", "success");
  } catch (err) {
    UI.toast("Failed to save milestone: " + err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProjects();
});
