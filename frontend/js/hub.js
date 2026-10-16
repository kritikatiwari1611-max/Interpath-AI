// Learning & Practice Hub client logic

let allResources = [];
let currentCategory = "all";

async function loadHubResources() {
  const container = document.getElementById("resources-container");
  UI.showLoading(container, "Loading Learning & Practice Hub...");

  try {
    const res = await API.get("/api/resources");
    allResources = res.data || [];
    renderResources();
  } catch (err) {
    UI.toast("Failed to load resources: " + err.message, "error");
  }
}

function renderResources() {
  const container = document.getElementById("resources-container");
  const filtered = allResources.filter(r => currentCategory === "all" || r.category === currentCategory);

  container.innerHTML = "";
  if (filtered.length === 0) {
    UI.showEmpty(container, "No resources found in this category.");
    return;
  }

  filtered.forEach(r => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "14px";
    card.style.borderLeft = r.completed ? "4px solid #10b981" : "4px solid #e2e8f0";

    let categoryIcon = "📹 Video";
    if (r.category === "docs") categoryIcon = "📄 Docs";
    else if (r.category === "practice") categoryIcon = "💻 Practice";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div style="flex: 1; min-width: 260px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px;">
            <span class="badge badge-tech">${categoryIcon}</span>
            <span class="badge badge-bonus">${r.difficulty}</span>
            <span class="badge badge-important">${r.skill}</span>
            ${!r.verified ? '<span class="badge" style="background:#fef2f2; color:#b91c1c;">link not verified</span>' : ''}
          </div>
          <h3 style="font-size: 1.05rem; font-weight: 600; margin-bottom: 4px;">${r.title}</h3>
          <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">${r.description}</p>
          <div style="font-size: 0.78rem; color: #94a3b8;">Source: <strong>${r.source}</strong></div>
        </div>

        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
          <a href="${r.url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="padding: 6px 12px; font-size: 0.82rem;">
            Open Material ↗
          </a>
          <button class="btn ${r.completed ? 'btn-secondary' : 'btn-primary'}" style="padding: 6px 12px; font-size: 0.82rem;" onclick="toggleResource('${r.id}', ${!r.completed})">
            ${r.completed ? '✓ Completed' : 'Mark Completed'}
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

async function toggleResource(resourceId, completed) {
  try {
    await API.put(`/api/resources/${resourceId}/complete`, { completed });
    const target = allResources.find(r => r.id === resourceId);
    if (target) target.completed = completed;
    renderResources();
    UI.toast(completed ? "Marked as completed!" : "Marked as pending", "success");
  } catch (err) {
    UI.toast("Failed to update status: " + err.message, "error");
  }
}

function setCategoryFilter(category) {
  currentCategory = category;
  document.querySelectorAll(".hub-tab-btn").forEach(btn => {
    btn.classList.toggle("btn-primary", btn.dataset.cat === category);
    btn.classList.toggle("btn-secondary", btn.dataset.cat !== category);
  });
  renderResources();
}

document.addEventListener("DOMContentLoaded", () => {
  loadHubResources();
  document.querySelectorAll(".hub-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => setCategoryFilter(btn.dataset.cat));
  });
});
