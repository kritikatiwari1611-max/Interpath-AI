// Step 3: Roadmap & Embedded Learning Hub Logic

let currentProfile = null;
let currentRoadmap = null;
let allResources = [];
let activeSkillTabs = {}; // skillKey -> 'video' | 'docs' | 'practice'

// Filter states
let filterDifficulty = "all";
let filterCategory = "all";
let filterStatus = "all";

async function initRoadmap() {
  const container = document.getElementById("roadmap-content");
  UI.showLoading(container, "Generating personalized roadmap and matching learning resources...");

  try {
    // 1. Fetch student profile
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};

    UI.renderStepBar(3, currentProfile);

    // 2. Fetch roadmap and resources in parallel
    const [roadmapRes, resourcesRes] = await Promise.all([
      API.get("/api/roadmap"),
      API.get("/api/resources")
    ]);

    currentRoadmap = roadmapRes.data;
    allResources = resourcesRes.data || [];

    renderRoadmapView();
  } catch (err) {
    UI.toast("Failed to load roadmap: " + err.message, "error");
  }
}

function renderRoadmapView() {
  const container = document.getElementById("roadmap-content");
  container.innerHTML = "";

  if (!currentRoadmap || !currentRoadmap.stages || currentRoadmap.stages.length === 0) {
    UI.showEmpty(container, "No roadmap stages available. Please select a target role first.");
    return;
  }

  // 1. Overall Progress Header Card
  const totalTasks = currentRoadmap.total_tasks || 0;
  const completedTasks = currentRoadmap.completed_tasks || 0;
  const progressPct = currentRoadmap.progress_pct || 0;

  // Calculate total estimated hours across all stages
  let totalHours = 0;
  (currentRoadmap.stages || []).forEach(st => {
    (st.tasks || []).forEach(t => { totalHours += (t.hours || 0); });
  });

  const topCard = document.createElement("div");
  topCard.className = "card";
  topCard.style.background = "linear-gradient(135deg, #ffffff 0%, #eff6ff 100%)";
  topCard.style.marginBottom = "24px";
  topCard.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
      <div>
        <span class="badge badge-tech" style="margin-bottom:6px;">Target: ${currentRoadmap.role_title}</span>
        <h2 style="font-size: 1.35rem; font-weight:700; color:#0f172a; margin:0;">Stage-by-Stage Roadmap & Learning Hub</h2>
        <p style="font-size: 0.88rem; color:#64748b; margin:4px 0 0 0;">
          Derived from your skill gaps. Practice each skill with integrated videos, docs, and exercises.
        </p>
      </div>

      <div style="min-width: 200px; text-align: right;">
        <div style="font-size: 2rem; font-weight: 800; color: #2563eb;">${progressPct}%</div>
        <div class="progress-bar-container" style="width: 200px; margin-bottom:4px;">
          <div class="progress-bar-fill" style="width: ${progressPct}%;"></div>
        </div>
        <span style="font-size: 0.8rem; color: #64748b;">
          ${completedTasks} of ${totalTasks} Tasks Completed • ~${totalHours} Total Hours
        </span>
      </div>
    </div>
  `;
  container.appendChild(topCard);

  // 2. Render each Stage
  (currentRoadmap.stages || []).forEach(stage => {
    const stageCard = document.createElement("div");
    stageCard.className = "card";
    stageCard.style.marginBottom = "24px";
    stageCard.style.borderLeft = "4px solid #2563eb";

    // Stage level progress
    const stageTasks = stage.tasks || [];
    const stageCompleted = stageTasks.filter(t => t.status === "completed").length;
    const stagePct = stageTasks.length > 0 ? Math.round((stageCompleted / stageTasks.length) * 100) : 0;
    const stageHours = stageTasks.reduce((sum, t) => sum + (t.hours || 0), 0);

    let stageHtml = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:30px; height:30px; border-radius:50%; background:#2563eb; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.9rem;">
            ${stage.stage_number}
          </span>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin: 0;">
              Stage ${stage.stage_number}: ${stage.name}
            </h3>
            <span style="font-size: 0.8rem; color: #64748b;">~${stageHours} Hours Estimated • ${stage.badge}</span>
          </div>
        </div>

        <div style="display:flex; align-items:center; gap:10px;">
          <div style="text-align:right;">
            <span style="font-size:0.85rem; font-weight:700; color:#2563eb;">${stagePct}% Done</span>
            <div class="progress-bar-container" style="width:120px; height:6px;">
              <div class="progress-bar-fill" style="width:${stagePct}%;"></div>
            </div>
          </div>
        </div>
      </div>
      <p style="font-size: 0.88rem; color: #475569; margin-bottom: 20px;">${stage.description}</p>
    `;

    // Tasks and embedded Learning Hub
    let tasksContainer = document.createElement("div");
    tasksContainer.style.display = "flex";
    tasksContainer.style.flexDirection = "column";
    tasksContainer.style.gap = "16px";

    stageTasks.forEach(task => {
      const taskDiv = document.createElement("div");
      taskDiv.style.padding = "16px";
      taskDiv.style.borderRadius = "8px";
      taskDiv.style.border = "1px solid #e2e8f0";
      taskDiv.style.background = task.status === "completed" ? "#f0fdf4" : "#ffffff";

      // Match learning resources for this task's topic or skill
      const taskSkill = (task.topic || "").toLowerCase();
      let matchedResources = allResources.filter(r => {
        const rSkill = (r.skill || "").toLowerCase();
        const rRole = (r.role_id || "").toLowerCase();
        return rSkill.includes(taskSkill) || taskSkill.includes(rSkill) || rRole === currentRoadmap.role_id;
      });

      // Active tab for this task
      const activeTab = activeSkillTabs[task.key] || "video";

      // Filter matched resources by the global filters
      let visibleResources = matchedResources.filter(r => {
        // category tab match
        if (filterCategory !== "all") {
          if (r.category !== filterCategory) return false;
        } else {
          if (r.category !== activeTab) return false;
        }

        // difficulty filter
        if (filterDifficulty !== "all") {
          const d = (r.difficulty || "").toLowerCase();
          if (filterDifficulty === "low" && !d.includes("beginner") && !d.includes("low")) return false;
          if (filterDifficulty === "medium" && !d.includes("intermediate") && !d.includes("medium")) return false;
          if (filterDifficulty === "high" && !d.includes("advanced") && !d.includes("high")) return false;
        }

        // status filter
        if (filterStatus !== "all") {
          if (r.status !== filterStatus) return false;
        }

        return true;
      });

      taskDiv.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
          <div style="flex:1; min-width:240px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-weight:700; font-size:0.95rem; color:#1e293b; ${task.status === 'completed' ? 'text-decoration:line-through; color:#166534;' : ''}">
                ${task.title}
              </span>
            </div>
            <p style="font-size:0.84rem; color:#64748b; margin:4px 0 0 0;">${task.description}</p>
            <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">
              ⏱ Est. Time: ${task.hours} hrs • Topic: ${task.topic}
            </div>
          </div>

          <!-- Segmented 3-button status control: Pending / In Progress / Completed -->
          <div>
            <div class="segmented-status-group">
              <button type="button" class="status-btn ${task.status === 'pending' ? 'active-pending' : ''}" onclick="changeTaskStatus('${task.key}', 'pending')">
                Pending
              </button>
              <button type="button" class="status-btn ${task.status === 'in_progress' ? 'active-in_progress' : ''}" onclick="changeTaskStatus('${task.key}', 'in_progress')">
                In Progress
              </button>
              <button type="button" class="status-btn ${task.status === 'completed' ? 'active-completed' : ''}" onclick="changeTaskStatus('${task.key}', 'completed')">
                ✓ Completed
              </button>
            </div>
          </div>
        </div>

        <!-- Embedded Learning Hub Section (3 Tabs: Videos, Notes/Docs, Practice Questions) -->
        <div style="margin-top:14px; padding-top:12px; border-top:1px dashed #cbd5e1;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
            <div style="font-size:0.82rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.5px;">
              Learning Hub Resources
            </div>

            <!-- Tab Buttons -->
            <div style="display:inline-flex; background:#f1f5f9; padding:2px; border-radius:6px; gap:2px;">
              <button type="button" style="padding:4px 10px; font-size:0.76rem; font-weight:600; border:none; border-radius:4px; cursor:pointer; background:${activeTab === 'video' ? '#ffffff' : 'transparent'}; color:${activeTab === 'video' ? '#2563eb' : '#64748b'};" onclick="switchSkillTab('${task.key}', 'video')">
                📹 Videos
              </button>
              <button type="button" style="padding:4px 10px; font-size:0.76rem; font-weight:600; border:none; border-radius:4px; cursor:pointer; background:${activeTab === 'docs' ? '#ffffff' : 'transparent'}; color:${activeTab === 'docs' ? '#2563eb' : '#64748b'};" onclick="switchSkillTab('${task.key}', 'docs')">
                📄 Notes & Docs
              </button>
              <button type="button" style="padding:4px 10px; font-size:0.76rem; font-weight:600; border:none; border-radius:4px; cursor:pointer; background:${activeTab === 'practice' ? '#ffffff' : 'transparent'}; color:${activeTab === 'practice' ? '#2563eb' : '#64748b'};" onclick="switchSkillTab('${task.key}', 'practice')">
                💡 Practice Questions
              </button>
            </div>
          </div>

          <!-- Resources List under current active tab -->
          <div style="display:flex; flex-direction:column; gap:8px;">
            ${visibleResources.length > 0 ? visibleResources.map(res => {
              const resStatus = res.status || (res.completed ? "completed" : "pending");
              return `
                <div style="padding:10px 12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                  <div style="flex:1; min-width:200px;">
                    <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                      <a href="${res.url}" target="_blank" rel="noopener noreferrer" style="font-weight:600; font-size:0.86rem; color:#2563eb; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
                        ${res.title} ↗
                      </a>
                      <span class="badge badge-important" style="font-size:0.7rem; padding:2px 6px;">${res.difficulty || 'All Levels'}</span>
                      <span style="font-size:0.75rem; color:#64748b;">via ${res.source || 'Curated'}</span>
                      ${!res.verified ? '<span class="badge" style="background:#fef3c7; color:#92400e; font-size:0.7rem;">link not verified</span>' : ''}
                    </div>
                    ${res.description ? `<p style="font-size:0.78rem; color:#64748b; margin:3px 0 0 0;">${res.description}</p>` : ''}
                  </div>

                  <!-- 3-Segmented status for resource -->
                  <div>
                    <div class="segmented-status-group">
                      <button type="button" class="status-btn ${resStatus === 'pending' ? 'active-pending' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changeResourceStatus('${res.id}', 'pending')">
                        Pending
                      </button>
                      <button type="button" class="status-btn ${resStatus === 'in_progress' ? 'active-in_progress' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changeResourceStatus('${res.id}', 'in_progress')">
                        In Progress
                      </button>
                      <button type="button" class="status-btn ${resStatus === 'completed' ? 'active-completed' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changeResourceStatus('${res.id}', 'completed')">
                        ✓ Done
                      </button>
                    </div>
                  </div>
                </div>
              `;
            }).join("") : `
              <div style="padding:10px 14px; background:#f8fafc; border-radius:6px; font-size:0.8rem; color:#94a3b8; font-style:italic;">
                No ${activeTab} resources matching current filters.
              </div>
            `}
          </div>
        </div>
      `;

      tasksContainer.appendChild(taskDiv);
    });

    stageCard.innerHTML = stageHtml;
    stageCard.appendChild(tasksContainer);
    container.appendChild(stageCard);
  });

  // 3. Navigation Footer
  const footerDiv = document.createElement("div");
  footerDiv.className = "step-nav-footer";
  footerDiv.innerHTML = `
    <div>
      <a href="/pages/skill-gap.html" class="btn btn-secondary">← Back: Skill Gap Analysis</a>
    </div>
    <div>
      <button class="btn btn-primary" onclick="window.location.href='/pages/projects.html'">
        Go to Project Recommendations →
      </button>
    </div>
  `;
  container.appendChild(footerDiv);
}

function switchSkillTab(taskKey, tabName) {
  activeSkillTabs[taskKey] = tabName;
  renderRoadmapView();
}

async function changeTaskStatus(taskKey, newStatus) {
  try {
    await API.put(`/api/roadmap/tasks/${taskKey}`, {
      status: newStatus,
      role_id: currentRoadmap.role_id
    });
    UI.toast(`Task marked as ${newStatus}!`, "success");

    // Refresh roadmap to get updated percentages immediately
    const res = await API.get("/api/roadmap");
    currentRoadmap = res.data;
    renderRoadmapView();
  } catch (err) {
    UI.toast("Failed to update task: " + err.message, "error");
  }
}

async function changeResourceStatus(resourceId, newStatus) {
  try {
    await API.put(`/api/resources/${resourceId}/status`, {
      status: newStatus
    });
    UI.toast(`Resource marked as ${newStatus}!`, "success");

    // Update in-memory resource list
    const target = allResources.find(r => r.id === resourceId);
    if (target) {
      target.status = newStatus;
      target.completed = (newStatus === "completed");
    }
    renderRoadmapView();
  } catch (err) {
    UI.toast("Failed to update resource: " + err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initRoadmap();

  // Filter change handlers
  document.getElementById("filter-difficulty").addEventListener("change", (e) => {
    filterDifficulty = e.target.value;
    renderRoadmapView();
  });
  document.getElementById("filter-category").addEventListener("change", (e) => {
    filterCategory = e.target.value;
    renderRoadmapView();
  });
  document.getElementById("filter-status").addEventListener("change", (e) => {
    filterStatus = e.target.value;
    renderRoadmapView();
  });
});
