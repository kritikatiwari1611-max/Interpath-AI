// Roadmap interactive logic: render 4 stages, toggle task status (pending/in_progress/completed)

let currentRoadmap = null;

async function loadRoadmap() {
  const container = document.getElementById("roadmap-content");
  UI.showLoading(container, "Generating customized 4-stage roadmap...");

  try {
    const res = await API.get("/api/roadmap");
    const data = res.data;

    if (!data.role_selected) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 24px;">
          <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Role Selected</h3>
          <p style="color: #64748b; margin-bottom: 20px;">Pick your target internship role to unlock your tailored roadmap.</p>
          <a href="/pages/roles.html" class="btn btn-primary">Choose a Target Role</a>
        </div>
      `;
      return;
    }

    currentRoadmap = data;
    renderRoadmap(data);
  } catch (err) {
    UI.toast("Failed to load roadmap: " + err.message, "error");
  }
}

function renderRoadmap(data) {
  const container = document.getElementById("roadmap-content");
  container.innerHTML = `
    <!-- Top Progress Card -->
    <div class="card" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
      <div>
        <span class="badge badge-tech">Target: ${data.role_title}</span>
        <h2 style="font-size: 1.35rem; font-weight:700; margin-top:6px;">Personalized Learning & Project Roadmap</h2>
        <p style="font-size: 0.88rem; color:#64748b;">Stages are uniquely derived from your current skill gaps.</p>
      </div>

      <div style="min-width: 200px; text-align: right;">
        <div style="font-size: 1.8rem; font-weight: 800; color: #2563eb;">${data.progress_pct}%</div>
        <div class="progress-bar-container">
          <div class="progress-bar-fill" style="width: ${data.progress_pct}%;"></div>
        </div>
        <span style="font-size: 0.8rem; color: #64748b;">${data.completed_tasks} of ${data.total_tasks} Tasks Completed</span>
      </div>
    </div>

    <!-- 4 Stages Timeline -->
    <div style="display: flex; flex-direction: column; gap: 24px;">
      ${data.stages.map(st => `
        <div class="card" style="border-left: 4px solid #2563eb;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="width:28px; height:28px; border-radius:50%; background:#2563eb; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem;">
                ${st.stage_number}
              </span>
              <h3 style="font-size: 1.15rem; font-weight: 700;">Stage ${st.stage_number}: ${st.name}</h3>
            </div>
            <span class="badge badge-important">${st.badge}</span>
          </div>
          <p style="font-size: 0.88rem; color: #64748b; margin-bottom: 16px;">${st.description}</p>

          <!-- Task List for this stage -->
          <div style="display:flex; flex-direction:column; gap: 10px;">
            ${st.tasks.map(t => {
              const isCompleted = t.status === "completed";
              const isInProgress = t.status === "in_progress";
              return `
                <div style="padding: 12px 16px; background: ${isCompleted ? '#f0fdf4' : '#f8fafc'}; border: 1px solid ${isCompleted ? '#bbf7d0' : '#e2e8f0'}; border-radius: 8px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                  <div style="flex: 1; min-width: 240px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                      <span style="font-weight: 600; font-size: 0.92rem; ${isCompleted ? 'text-decoration: line-through; color: #166534;' : ''}">
                        ${t.title}
                      </span>
                      <span class="badge ${isCompleted ? 'badge-bonus' : (isInProgress ? 'badge-important' : 'badge-tech')}" style="font-size:0.75rem;">
                        ${t.status}
                      </span>
                    </div>
                    <p style="font-size: 0.82rem; color: #64748b; margin-top: 4px;">${t.description}</p>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">Est. Time: ${t.hours} hrs • Topic: ${t.topic}</div>
                  </div>

                  <!-- Status Selector -->
                  <div style="display:flex; gap: 6px;">
                    <select class="form-control" style="font-size: 0.8rem; padding: 4px 8px; width: 130px;" onchange="updateTaskStatus('${t.key}', this.value)">
                      <option value="pending" ${t.status === 'pending' ? 'selected' : ''}>Pending</option>
                      <option value="in_progress" ${t.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                      <option value="completed" ${t.status === 'completed' ? 'selected' : ''}>Completed</option>
                    </select>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

async function updateTaskStatus(taskKey, newStatus) {
  try {
    await API.put(`/api/roadmap/tasks/${taskKey}`, {
      status: newStatus,
      role_id: currentRoadmap.role_id
    });
    UI.toast(`Task marked as ${newStatus}!`, "success");
    // Reload roadmap to recalculate percentage
    loadRoadmap();
  } catch (err) {
    UI.toast("Failed to update task: " + err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadRoadmap();
});
