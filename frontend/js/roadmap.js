// Step 3: Roadmap, Embedded Learning Hub, and AI Weekly Study Plan Logic

let currentProfile = null;
let currentRoadmap = null;
let allResources = [];
let activeSkillTabs = {}; // skillKey -> 'video' | 'docs' | 'practice'
let skillExplanationsMap = {}; // skill_name (lowercase) -> explanation object

// Weekly Plan state
let currentPlan = null;
let activeRoadmapTab = "roadmap"; // "roadmap" | "plan"

// Filter states for Roadmap Hub
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

    // 2. Fetch roadmap, resources, and skill explanations in parallel
    const [roadmapRes, resourcesRes, explRes] = await Promise.all([
      API.get("/api/roadmap"),
      API.get("/api/resources"),
      API.get("/api/roadmap/skill-explanations").catch(() => ({ data: { explanations: [] } }))
    ]);

    currentRoadmap = roadmapRes.data;
    allResources = resourcesRes.data || [];

    // Index skill explanations
    const explanations = (explRes.data && explRes.data.explanations) || [];
    skillExplanationsMap = {};
    explanations.forEach(e => {
      if (e.skill) {
        skillExplanationsMap[e.skill.toLowerCase().trim()] = e;
      }
    });

    renderRoadmapView();

    // Also fetch existing plan in background if any
    loadWeeklyPlan();
  } catch (err) {
    UI.toast("Failed to load roadmap: " + err.message, "error");
  }
}

// ---------------------------------------------------------------------
// Tab Switching: Roadmap vs Weekly Study Plan
// ---------------------------------------------------------------------
function switchRoadmapTab(tab) {
  activeRoadmapTab = tab;
  const roadmapSection = document.getElementById("roadmap-view-section");
  const planSection = document.getElementById("plan-view-section");
  const roadmapBtn = document.getElementById("tab-roadmap-btn");
  const planBtn = document.getElementById("tab-plan-btn");

  if (tab === "roadmap") {
    roadmapSection.style.display = "block";
    planSection.style.display = "none";
    roadmapBtn.className = "btn btn-primary";
    planBtn.className = "btn btn-secondary";
  } else {
    roadmapSection.style.display = "none";
    planSection.style.display = "block";
    roadmapBtn.className = "btn btn-secondary";
    planBtn.className = "btn btn-primary";
    renderWeeklyPlanView();
  }
}

// ---------------------------------------------------------------------
// Render Stage-by-Stage Roadmap & Embedded Learning Hub
// ---------------------------------------------------------------------
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
        <span class="badge badge-tech" style="margin-bottom:6px;">Target: ${escapeHtml(currentRoadmap.role_title)}</span>
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

    const stageTasks = stage.tasks || [];
    const stageCompleted = stageTasks.filter(t => t.status === "completed").length;
    const stagePct = stageTasks.length > 0 ? Math.round((stageCompleted / stageTasks.length) * 100) : 0;
    const stageHours = stageTasks.reduce((sum, t) => sum + (t.hours || 0), 0);

    let stageHeaderHtml = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:30px; height:30px; border-radius:50%; background:#2563eb; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.9rem;">
            ${stage.stage_number}
          </span>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin: 0;">
              Stage ${stage.stage_number}: ${escapeHtml(stage.name)}
            </h3>
            <span style="font-size: 0.8rem; color: #64748b;">~${stageHours} Hours Estimated • ${escapeHtml(stage.badge || '')}</span>
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
      <p style="font-size: 0.88rem; color: #475569; margin-bottom: 20px;">${escapeHtml(stage.description)}</p>
    `;

    stageCard.innerHTML = stageHeaderHtml;

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

      const taskSkill = (task.topic || "").toLowerCase();
      let matchedResources = allResources.filter(r => {
        const rSkill = (r.skill || "").toLowerCase();
        const rRole = (r.role_id || "").toLowerCase();
        return rSkill.includes(taskSkill) || taskSkill.includes(rSkill) || rRole === currentRoadmap.role_id;
      });

      const activeTab = activeSkillTabs[task.key] || "video";

      let visibleResources = matchedResources.filter(r => {
        if (filterCategory !== "all") {
          if (r.category !== filterCategory) return false;
        } else {
          if (r.category !== activeTab) return false;
        }

        if (filterDifficulty !== "all") {
          const d = (r.difficulty || "").toLowerCase();
          if (filterDifficulty === "low" && !d.includes("beginner") && !d.includes("low")) return false;
          if (filterDifficulty === "medium" && !d.includes("intermediate") && !d.includes("medium")) return false;
          if (filterDifficulty === "high" && !d.includes("advanced") && !d.includes("high")) return false;
        }

        if (filterStatus !== "all") {
          if (r.status !== filterStatus) return false;
        }

        return true;
      });

      // Find skill explanation for this task's topic
      const expl = skillExplanationsMap[taskSkill] || null;

      taskDiv.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:10px;">
          <div style="flex:1; min-width:240px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-weight:700; font-size:0.95rem; color:#1e293b; ${task.status === 'completed' ? 'text-decoration:line-through; color:#166534;' : ''}">
                ${escapeHtml(task.title)}
              </span>
            </div>
            <p style="font-size:0.84rem; color:#64748b; margin:4px 0 0 0;">${escapeHtml(task.description)}</p>
            <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">
              ⏱ Est. Time: ${task.hours} hrs • Topic: ${escapeHtml(task.topic)}
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

        <!-- Collapsible "Why this skill matters" box -->
        ${expl ? `
          <details style="margin: 8px 0 12px 0; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 12px; font-size:0.82rem;">
            <summary style="font-weight:600; color:#2563eb; cursor:pointer; user-select:none;">
              💡 Why this skill matters for ${escapeHtml(currentRoadmap.role_title || 'this role')} (Click to expand)
            </summary>
            <div style="margin-top:8px; line-height:1.45; color:#334155; display:flex; flex-direction:column; gap:6px;">
              <div><strong>Why it matters:</strong> <span>${escapeHtml(expl.why_it_matters)}</span></div>
              <div><strong>How it is used:</strong> <span>${escapeHtml(expl.how_it_is_used_in_role)}</span></div>
              <div><strong>Your starting point:</strong> <span style="color:#d97706; font-weight:600;">${escapeHtml(expl.your_starting_point)}</span></div>
            </div>
          </details>
        ` : ''}

        <!-- Embedded Learning Hub Section (3 Tabs: Videos, Notes/Docs, Practice Questions) -->
        <div style="margin-top:10px; padding-top:10px; border-top:1px dashed #cbd5e1;">
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
                        ${escapeHtml(res.title)} ↗
                      </a>
                      <span class="badge badge-important" style="font-size:0.7rem; padding:2px 6px;">${escapeHtml(res.difficulty || 'All Levels')}</span>
                      <span style="font-size:0.75rem; color:#64748b;">via ${escapeHtml(res.source || 'Curated')}</span>
                      ${!res.verified ? '<span class="badge" style="background:#fef3c7; color:#92400e; font-size:0.7rem;">link not verified</span>' : ''}
                    </div>
                    ${res.description ? `<p style="font-size:0.78rem; color:#64748b; margin:3px 0 0 0;">${escapeHtml(res.description)}</p>` : ''}
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

// ---------------------------------------------------------------------
// WEEKLY STUDY PLAN LOGIC & RENDERING
// ---------------------------------------------------------------------

async function loadWeeklyPlan() {
  try {
    const res = await API.get("/api/roadmap/plan");
    currentPlan = (res && res.data) ? (res.data.plan || res.data) : null;
    if (activeRoadmapTab === "plan") {
      renderWeeklyPlanView();
    }
  } catch (err) {
    console.error("Could not load study plan", err);
  }
}

function renderWeeklyPlanView() {
  const container = document.getElementById("plan-content");
  container.innerHTML = "";

  // 1. Setup / Generator Panel
  const setupCard = document.createElement("div");
  setupCard.className = "card";
  setupCard.style.marginBottom = "20px";
  setupCard.style.borderTop = "4px solid #2563eb";

  const inputs = (currentPlan && currentPlan.inputs) || {};
  const currentHours = inputs.hours_per_week || 10;
  const currentWeeks = inputs.weeks || 8;
  const currentStyle = inputs.learning_style || "Videos first";
  const currentDate = inputs.target_date || "";

  setupCard.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
      <div>
        <h2 style="font-size:1.25rem; font-weight:700; color:#0f172a; margin:0;">
          📅 Create Your Personalized Weekly Study Plan
        </h2>
        <p style="font-size:0.86rem; color:#64748b; margin:4px 0 0 0;">
          Structure your missing and weak skills into realistic weekly milestones matching your study schedule.
        </p>
      </div>
      <div>
        <span style="font-size:0.75rem; color:#64748b; background:#f1f5f9; padding:4px 8px; border-radius:4px;">
          Your completed tasks are kept when you regenerate.
        </span>
      </div>
    </div>

    <form id="plan-setup-form" onsubmit="handleGeneratePlan(event)" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:14px; align-items:end;">
      <div>
        <label style="font-size:0.82rem; font-weight:600; color:#334155; display:block; margin-bottom:4px;">
          Hours Available Per Week
        </label>
        <select id="plan-hours" class="form-control" style="font-size:0.86rem;">
          <option value="5" ${currentHours === 5 ? 'selected' : ''}>5 hours / week</option>
          <option value="10" ${currentHours === 10 ? 'selected' : ''}>10 hours / week (Recommended)</option>
          <option value="15" ${currentHours === 15 ? 'selected' : ''}>15 hours / week</option>
          <option value="20" ${currentHours === 20 ? 'selected' : ''}>20 hours / week</option>
        </select>
      </div>

      <div>
        <label style="font-size:0.82rem; font-weight:600; color:#334155; display:block; margin-bottom:4px;">
          Target Duration
        </label>
        <select id="plan-weeks" class="form-control" style="font-size:0.86rem;">
          <option value="4" ${currentWeeks === 4 ? 'selected' : ''}>4 Weeks (Crash course)</option>
          <option value="6" ${currentWeeks === 6 ? 'selected' : ''}>6 Weeks (Fast paced)</option>
          <option value="8" ${currentWeeks === 8 ? 'selected' : ''}>8 Weeks (Standard)</option>
          <option value="12" ${currentWeeks === 12 ? 'selected' : ''}>12 Weeks (In-depth)</option>
        </select>
      </div>

      <div>
        <label style="font-size:0.82rem; font-weight:600; color:#334155; display:block; margin-bottom:4px;">
          Learning Style
        </label>
        <select id="plan-style" class="form-control" style="font-size:0.86rem;">
          <option value="Videos first" ${currentStyle === 'Videos first' ? 'selected' : ''}>Videos first (Visual)</option>
          <option value="Notes first" ${currentStyle === 'Notes first' ? 'selected' : ''}>Notes & Docs first (Reading)</option>
          <option value="Practice first" ${currentStyle === 'Practice first' ? 'selected' : ''}>Practice first (Hands-on)</option>
        </select>
      </div>

      <div>
        <label style="font-size:0.82rem; font-weight:600; color:#334155; display:block; margin-bottom:4px;">
          Ready By Date (Optional)
        </label>
        <input type="date" id="plan-target-date" class="form-control" value="${escapeHtml(currentDate)}" style="font-size:0.86rem;" />
      </div>

      <div style="display:flex; gap:8px;">
        <button type="submit" id="btn-generate-plan" class="btn btn-primary" style="flex:1; padding:8px 12px; font-weight:600; font-size:0.88rem;">
          ${currentPlan ? '🔄 Regenerate Plan' : '✨ Generate AI Study Plan'}
        </button>
      </div>
    </form>
  `;
  container.appendChild(setupCard);

  // If no plan generated yet, show empty state prompt
  if (!currentPlan) {
    const emptyCard = document.createElement("div");
    emptyCard.className = "card";
    emptyCard.style.textAlign = "center";
    emptyCard.style.padding = "40px 20px";
    emptyCard.innerHTML = `
      <div style="font-size:2.5rem; margin-bottom:12px;">🗓️</div>
      <h3 style="color:#0f172a; margin-bottom:6px;">No Active Weekly Plan</h3>
      <p style="color:#64748b; font-size:0.9rem; max-width:480px; margin:0 auto 16px auto;">
        Select your study hours and duration above, then click <strong>Generate AI Study Plan</strong> to break your missing skills down into bite-sized weekly sessions.
      </p>
    `;
    container.appendChild(emptyCard);
    return;
  }

  // 2. Banner if skills changed
  if (currentPlan.skills_changed) {
    const banner = document.createElement("div");
    banner.className = "alert alert-warning";
    banner.style.marginBottom = "16px";
    banner.style.display = "flex";
    banner.style.justifyContent = "space-between";
    banner.style.alignItems = "center";
    banner.innerHTML = `
      <div>
        <strong>⚠️ Your skills or role have changed since this plan was generated!</strong>
        <div style="font-size:0.82rem; margin-top:2px;">Regenerate your plan to incorporate newly updated skills. Your completed sessions will carry over automatically.</div>
      </div>
      <button class="btn btn-primary" style="padding:6px 12px; font-size:0.82rem;" onclick="triggerGeneratePlan()">
        Regenerate Now
      </button>
    `;
    container.appendChild(banner);
  }

  // 3. Plan Overview & Badge Header
  const overviewCard = document.createElement("div");
  overviewCard.className = "card";
  overviewCard.style.marginBottom = "20px";
  overviewCard.style.background = "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)";

  const modeBadge = currentPlan.mode === "ai"
    ? `<span class="badge" style="background:#dbeafe; color:#1e40af; font-size:0.75rem;">AI Mode</span>`
    : `<span class="badge" style="background:#f1f5f9; color:#475569; font-size:0.75rem;">Demo mode (rule-based)</span>`;

  const totalProgress = currentPlan.total_progress_pct || 0;
  const currentWeekNum = currentPlan.current_week_num || 1;

  overviewCard.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
          ${modeBadge}
          <span style="font-size:0.8rem; color:#64748b;">Target Role: <strong>${escapeHtml(currentPlan.role_title || currentProfile.target_role || '')}</strong></span>
          <span style="font-size:0.8rem; color:#64748b;">• Duration: <strong>${(currentPlan.weeks || []).length} Weeks</strong></span>
        </div>
        <p id="plan-overview-text" style="font-size:0.92rem; color:#334155; line-height:1.5; margin:0;"></p>
      </div>

      <div style="min-width:180px; text-align:right;">
        <div style="font-size:1.6rem; font-weight:800; color:#2563eb;">${totalProgress}% Done</div>
        <div class="progress-bar-container" style="width:180px; height:6px; margin-bottom:4px;">
          <div class="progress-bar-fill" style="width:${totalProgress}%;"></div>
        </div>
        <span style="font-size:0.78rem; color:#64748b;">Currently on Week ${currentWeekNum}</span>
      </div>
    </div>

    <!-- Mandatory Disclaimer -->
    <div style="margin-top:10px; padding-top:8px; border-top:1px dashed #e2e8f0; font-size:0.74rem; color:#94a3b8;">
      AI study plans are suggested learning schedules based on your target role and available hours. They do not change your skill levels or guarantee internship selection.
    </div>
  `;
  container.appendChild(overviewCard);

  // Safely assign overview text to prevent XSS
  const overviewTextEl = overviewCard.querySelector("#plan-overview-text");
  if (overviewTextEl) {
    overviewTextEl.textContent = currentPlan.overview || "Your structured weekly study plan.";
  }

  // 4. Render Weeks & Sessions
  const weeks = currentPlan.weeks || [];
  weeks.forEach(w => {
    const isCurrent = (w.week === currentWeekNum);
    const weekCard = document.createElement("div");
    weekCard.className = "card";
    weekCard.style.marginBottom = "18px";
    weekCard.style.borderLeft = isCurrent ? "5px solid #2563eb" : "4px solid #cbd5e1";
    if (isCurrent) {
      weekCard.style.boxShadow = "0 4px 12px rgba(37, 99, 235, 0.08)";
    }

    const weekPct = w.progress_pct || 0;
    const weekMins = w.total_minutes || 0;

    let weekHeader = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:28px; height:28px; border-radius:50%; background:${isCurrent ? '#2563eb' : '#64748b'}; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem;">
            W${w.week}
          </span>
          <div>
            <h3 style="font-size:1.05rem; font-weight:700; color:#0f172a; margin:0; display:flex; align-items:center; gap:8px;">
              <span>Week ${w.week}: ${escapeHtml(w.theme)}</span>
              ${isCurrent ? '<span class="badge badge-important" style="font-size:0.68rem; padding:2px 6px;">Current Week</span>' : ''}
            </h3>
            <span style="font-size:0.78rem; color:#64748b;">
              Goal: ${escapeHtml(w.goal)} • ~${weekMins} mins total
            </span>
          </div>
        </div>

        <div style="text-align:right;">
          <span style="font-size:0.82rem; font-weight:700; color:#2563eb;">${weekPct}%</span>
          <div class="progress-bar-container" style="width:110px; height:5px;">
            <div class="progress-bar-fill" style="width:${weekPct}%;"></div>
          </div>
        </div>
      </div>
    `;

    weekCard.innerHTML = weekHeader;

    // Sessions List
    const sessionsContainer = document.createElement("div");
    sessionsContainer.style.display = "flex";
    sessionsContainer.style.flexDirection = "column";
    sessionsContainer.style.gap = "10px";
    sessionsContainer.style.marginTop = "10px";

    (w.sessions || []).forEach(sess => {
      const sessDiv = document.createElement("div");
      sessDiv.style.padding = "10px 14px";
      sessDiv.style.borderRadius = "6px";
      sessDiv.style.border = "1px solid #e2e8f0";
      sessDiv.style.background = sess.status === "completed" ? "#f0fdf4" : "#ffffff";
      sessDiv.style.display = "flex";
      sessDiv.style.justifyContent = "space-between";
      sessDiv.style.alignItems = "center";
      sessDiv.style.flexWrap = "wrap";
      sessDiv.style.gap = "10px";

      // Task type pill styling
      let typeBg = "#f1f5f9";
      let typeColor = "#475569";
      if (sess.task_type === "learn") { typeBg = "#e0e7ff"; typeColor = "#3730a3"; }
      if (sess.task_type === "practice") { typeBg = "#fef3c7"; typeColor = "#92400e"; }
      if (sess.task_type === "project") { typeBg = "#dcfce7"; typeColor = "#166534"; }
      if (sess.task_type === "interview") { typeBg = "#fce7f3"; typeColor = "#9d174d"; }

      // Resource Links
      let resLinksHtml = "";
      if (sess.resources && sess.resources.length > 0) {
        resLinksHtml = `
          <div style="margin-top:4px; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
            <span style="font-size:0.72rem; color:#64748b;">Resources:</span>
            ${sess.resources.map(r => `
              <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" style="font-size:0.75rem; color:#2563eb; text-decoration:none; background:#f8fafc; border:1px solid #e2e8f0; padding:2px 6px; border-radius:4px; display:inline-flex; align-items:center; gap:3px;">
                🔗 ${escapeHtml(r.title)}
              </a>
            `).join("")}
          </div>
        `;
      }

      sessDiv.innerHTML = `
        <div style="flex:1; min-width:220px;">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span style="font-size:0.7rem; font-weight:700; text-transform:uppercase; padding:2px 6px; border-radius:4px; background:${typeBg}; color:${typeColor};">
              ${escapeHtml(sess.task_type || 'learn')}
            </span>
            <span style="font-size:0.88rem; font-weight:600; color:#1e293b; ${sess.status === 'completed' ? 'text-decoration:line-through; color:#166534;' : ''}">
              ${escapeHtml(sess.title)}
            </span>
            <span style="font-size:0.75rem; color:#94a3b8;">⏱ ${sess.minutes}m</span>
          </div>
          ${resLinksHtml}
        </div>

        <div>
          <div class="segmented-status-group">
            <button type="button" class="status-btn ${sess.status === 'pending' ? 'active-pending' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changePlanSessionStatus('${sess.session_key}', 'pending')">
              Pending
            </button>
            <button type="button" class="status-btn ${sess.status === 'in_progress' ? 'active-in_progress' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changePlanSessionStatus('${sess.session_key}', 'in_progress')">
              In Progress
            </button>
            <button type="button" class="status-btn ${sess.status === 'completed' ? 'active-completed' : ''}" style="padding:3px 8px; font-size:0.72rem;" onclick="changePlanSessionStatus('${sess.session_key}', 'completed')">
              ✓ Done
            </button>
          </div>
        </div>
      `;

      sessionsContainer.appendChild(sessDiv);
    });

    weekCard.appendChild(sessionsContainer);

    // Week Checkpoint and Tip
    if (w.checkpoint || w.tip) {
      const footerNotes = document.createElement("div");
      footerNotes.style.marginTop = "12px";
      footerNotes.style.paddingTop = "8px";
      footerNotes.style.borderTop = "1px dashed #e2e8f0";
      footerNotes.style.fontSize = "0.78rem";
      footerNotes.style.color = "#475569";
      footerNotes.style.display = "flex";
      footerNotes.style.flexDirection = "column";
      footerNotes.style.gap = "4px";

      if (w.checkpoint) {
        footerNotes.innerHTML += `<div>🎯 <strong>Weekly Checkpoint:</strong> <span>${escapeHtml(w.checkpoint)}</span></div>`;
      }
      if (w.tip) {
        footerNotes.innerHTML += `<div>💡 <strong>Study Tip:</strong> <span>${escapeHtml(w.tip)}</span></div>`;
      }
      weekCard.appendChild(footerNotes);
    }

    container.appendChild(weekCard);
  });

  // 5. Revision Tips Box
  if (currentPlan.revision_tips && currentPlan.revision_tips.length > 0) {
    const revCard = document.createElement("div");
    revCard.className = "card";
    revCard.style.marginTop = "20px";
    revCard.style.background = "#f0fdf4";
    revCard.style.border = "1px solid #bbf7d0";
    revCard.innerHTML = `
      <h4 style="color:#166534; font-size:0.95rem; font-weight:700; margin:0 0 8px 0;">
        🌿 General Revision & Retention Tips
      </h4>
      <ul style="margin:0; padding-left:20px; font-size:0.85rem; color:#14532d; display:flex; flex-direction:column; gap:4px;">
        ${currentPlan.revision_tips.map(t => `<li>${escapeHtml(t)}</li>`).join("")}
      </ul>
    `;
    container.appendChild(revCard);
  }
}

// ---------------------------------------------------------------------
// Plan Action Handlers
// ---------------------------------------------------------------------

function triggerGeneratePlan() {
  const form = document.getElementById("plan-setup-form");
  if (form) {
    handleGeneratePlan({ preventDefault: () => {} });
  }
}

async function handleGeneratePlan(e) {
  if (e && typeof e.preventDefault === "function") {
    e.preventDefault();
  }
  const hours = parseInt(document.getElementById("plan-hours").value, 10);
  const weeks = parseInt(document.getElementById("plan-weeks").value, 10);
  const style = document.getElementById("plan-style").value;
  const targetDate = document.getElementById("plan-target-date").value;

  const btn = document.getElementById("btn-generate-plan");
  const origText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = "⏳ Generating...";

  try {
    const res = await API.post("/api/roadmap/plan", {
      hours_per_week: hours,
      weeks: weeks,
      learning_style: style,
      target_date: targetDate
    });

    UI.toast("Weekly study plan generated successfully!", "success");
    currentPlan = (res && res.data) ? (res.data.plan || res.data) : null;
    renderWeeklyPlanView();
  } catch (err) {
    UI.toast("Failed to generate plan: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = origText;
  }
}

async function changePlanSessionStatus(sessionKey, newStatus) {
  try {
    await API.put(`/api/roadmap/plan/sessions/${sessionKey}`, {
      status: newStatus
    });

    // Refresh plan
    await loadWeeklyPlan();
    UI.toast(`Session updated to ${newStatus}!`, "success");
  } catch (err) {
    UI.toast("Failed to update session: " + err.message, "error");
  }
}

// Helper: Escape HTML to avoid XSS
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  initRoadmap();

  // Filter change handlers for roadmap hub
  const diffEl = document.getElementById("filter-difficulty");
  if (diffEl) {
    diffEl.addEventListener("change", (e) => {
      filterDifficulty = e.target.value;
      renderRoadmapView();
    });
  }

  const catEl = document.getElementById("filter-category");
  if (catEl) {
    catEl.addEventListener("change", (e) => {
      filterCategory = e.target.value;
      renderRoadmapView();
    });
  }

  const statEl = document.getElementById("filter-status");
  if (statEl) {
    statEl.addEventListener("change", (e) => {
      filterStatus = e.target.value;
      renderRoadmapView();
    });
  }
});
