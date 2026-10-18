// Step 2: Skill Gap Analyzer & Skill Selection Logic

let currentProfile = null;
let roleGapData = null;
let skillSelectionState = {}; // map skillName -> { knows: boolean, level: 'Low'|'Medium'|'High' }
let extraSkills = []; // list of { name: string, level: string }

async function initSkillGap() {
  const container = document.getElementById("skillgap-content");
  UI.showLoading(container, "Loading target role requirements and your skills...");

  try {
    // 1. Fetch user profile
    const profileRes = await API.get("/api/profile");
    currentProfile = profileRes.data.profile || {};

    // Check prerequisite: must have chosen a role
    if (!currentProfile.selected_role_id) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return;
    }

    UI.renderStepBar(2, currentProfile);

    // 2. Fetch skill gap data
    const gapRes = await API.get("/api/skill-gap");
    roleGapData = gapRes.data;

    if (!roleGapData.role_selected) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return;
    }

    // Initialize selection state based on user's current saved skills
    const existingSkillsMap = {};
    (currentProfile.skills || []).forEach(s => {
      existingSkillsMap[s.skill_name.toLowerCase()] = s.level;
    });

    // Populate required role skills
    (roleGapData.skills || []).forEach(s => {
      const existingLevel = existingSkillsMap[s.name.toLowerCase()];
      if (existingLevel) {
        let normalizedLevel = "Medium";
        const lvlLower = existingLevel.toLowerCase();
        if (lvlLower === "low" || lvlLower === "beginner") normalizedLevel = "Low";
        else if (lvlLower === "high" || lvlLower === "advanced") normalizedLevel = "High";
        
        skillSelectionState[s.name] = { knows: true, level: normalizedLevel };
      } else {
        skillSelectionState[s.name] = { knows: false, level: "Low" };
      }
    });

    // Also populate extra skills not in role list
    const roleSkillNames = new Set((roleGapData.skills || []).map(s => s.name.toLowerCase()));
    extraSkills = [];
    (currentProfile.skills || []).forEach(s => {
      if (!roleSkillNames.has(s.skill_name.toLowerCase())) {
        let norm = "Medium";
        const lvl = (s.level || "").toLowerCase();
        if (lvl === "low" || lvl === "beginner") norm = "Low";
        else if (lvl === "high" || lvl === "advanced") norm = "High";
        extraSkills.push({ name: s.skill_name, level: norm });
      }
    });

    renderSkillSelectionAndResults();
  } catch (err) {
    UI.toast("Failed to load skill gap: " + err.message, "error");
  }
}

function renderSkillSelectionAndResults() {
  const container = document.getElementById("skillgap-content");
  container.innerHTML = "";

  // 1. Header Banner
  const headerCard = document.createElement("div");
  headerCard.className = "card";
  headerCard.style.background = "linear-gradient(135deg, #ffffff 0%, #eff6ff 100%)";
  headerCard.style.marginBottom = "24px";
  headerCard.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <div>
        <span class="badge badge-tech" style="margin-bottom: 6px;">Target Role</span>
        <h2 style="font-size: 1.4rem; font-weight: 700; color: #0f172a; margin: 0;">${roleGapData.role_title}</h2>
        <p style="font-size: 0.88rem; color: #64748b; margin: 4px 0 0 0;">
          Mark which skills you know and choose your proficiency level. Skills you don't know yet will be automatically included in your Step 3 learning roadmap!
        </p>
      </div>
      <div style="text-align: right; min-width: 160px;">
        <div style="font-size: 2rem; font-weight: 800; color: #2563eb;">${roleGapData.overall_match_pct || 0}%</div>
        <div class="progress-bar-container" style="width: 160px; margin-bottom: 4px;">
          <div class="progress-bar-fill" style="width: ${roleGapData.overall_match_pct || 0}%;"></div>
        </div>
        <span style="font-size: 0.78rem; color: #64748b;">Current Role Match</span>
      </div>
    </div>
  `;
  container.appendChild(headerCard);

  // 2. Interactive Skills Checklist Card
  const checklistCard = document.createElement("div");
  checklistCard.className = "card";
  checklistCard.style.marginBottom = "24px";

  let itemsHtml = (roleGapData.skills || []).map(s => {
    const state = skillSelectionState[s.name] || { knows: false, level: "Low" };
    let impBadge = "badge-important";
    if (s.importance === "core") impBadge = "badge-core";
    else if (s.importance === "bonus") impBadge = "badge-bonus";

    return `
      <div class="skill-row-item" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; padding:14px; border-bottom:1px solid #f1f5f9;" data-skill="${s.name}">
        <div style="min-width: 220px;">
          <div style="font-weight: 600; font-size: 0.95rem; color: #1e293b;">${s.name}</div>
          <span class="badge ${impBadge}" style="font-size: 0.75rem;">${s.importance}</span>
        </div>

        <!-- Choice: Know vs Don't Know -->
        <div style="display:flex; align-items:center; gap: 8px;">
          <div class="segmented-status-group">
            <button type="button" class="status-btn ${!state.knows ? 'active-pending' : ''}" onclick="setSkillKnown('${s.name}', false)">
              I don't know this yet
            </button>
            <button type="button" class="status-btn ${state.knows ? 'active-completed' : ''}" onclick="setSkillKnown('${s.name}', true)">
              ✓ I know this
            </button>
          </div>
        </div>

        <!-- Level selector: LOW / MEDIUM / HIGH -->
        <div style="min-width: 180px; display:flex; align-items:center; justify-content:flex-end;">
          ${state.knows ? `
            <div style="display:inline-flex; align-items:center; gap:4px;">
              <span style="font-size:0.75rem; color:#64748b; margin-right:4px;">Level:</span>
              <button type="button" class="btn ${state.level === 'Low' ? 'btn-primary' : 'btn-secondary'}" style="padding:4px 8px; font-size:0.75rem;" onclick="setSkillLevel('${s.name}', 'Low')">LOW (0.4)</button>
              <button type="button" class="btn ${state.level === 'Medium' ? 'btn-primary' : 'btn-secondary'}" style="padding:4px 8px; font-size:0.75rem;" onclick="setSkillLevel('${s.name}', 'Medium')">MEDIUM (0.7)</button>
              <button type="button" class="btn ${state.level === 'High' ? 'btn-primary' : 'btn-secondary'}" style="padding:4px 8px; font-size:0.75rem;" onclick="setSkillLevel('${s.name}', 'High')">HIGH (1.0)</button>
            </div>
          ` : `
            <span style="font-size:0.8rem; color:#94a3b8; font-style:italic;">Added to Roadmap</span>
          `}
        </div>
      </div>
    `;
  }).join("");

  checklistCard.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 16px;">
      <div>
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin: 0;">Required Skills Checklist</h3>
        <p style="font-size: 0.85rem; color: #64748b; margin: 4px 0 0 0;">Check your current knowledge against ${roleGapData.role_title} requirements</p>
      </div>
    </div>

    <div>${itemsHtml}</div>

    <!-- Extra Skills Section -->
    <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
      <h4 style="font-size: 0.95rem; font-weight: 600; color: #334155; margin-bottom: 10px;">Additional Skills (Optional)</h4>
      <div id="extra-skills-list" style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom: 12px;">
        ${extraSkills.map((es, idx) => `
          <span class="badge badge-important" style="padding:6px 10px; font-size:0.82rem; display:inline-flex; align-items:center; gap:6px;">
            ${es.name} (${es.level})
            <button type="button" onclick="removeExtraSkill(${idx})" style="background:none; border:none; color:#ef4444; font-weight:bold; cursor:pointer;">×</button>
          </span>
        `).join("")}
      </div>

      <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
        <input type="text" id="extra-skill-name" class="form-control" placeholder="Add extra skill (e.g. Git, Docker, Excel)..." style="width: 240px; font-size:0.85rem;">
        <select id="extra-skill-level" class="form-control" style="width: 140px; font-size:0.85rem;">
          <option value="Low">LOW (Beginner)</option>
          <option value="Medium" selected>MEDIUM (Interm.)</option>
          <option value="High">HIGH (Advanced)</option>
        </select>
        <button type="button" onclick="addExtraSkill()" class="btn btn-secondary" style="font-size:0.85rem; padding:8px 14px;">+ Add Skill</button>
      </div>
    </div>

    <!-- Save and Analyze Action Button -->
    <div style="margin-top: 24px; padding-top: 16px; border-top: 2px solid #e2e8f0; text-align: right;">
      <button id="save-analyze-btn" class="btn btn-primary" style="padding: 10px 24px; font-size: 0.95rem; font-weight: 600;" onclick="saveAndAnalyze()">
        Save and Analyze Skills
      </button>
    </div>
  `;
  container.appendChild(checklistCard);

  // 3. Analysis Results Section
  const resultsCard = document.createElement("div");
  resultsCard.className = "card";
  resultsCard.style.marginBottom = "24px";

  resultsCard.innerHTML = `
    <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 16px;">
      Skill Gap Analysis Result
    </h3>

    <!-- 4-Column Breakdown -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px;">
      
      <!-- Learned (Medium/High) -->
      <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-weight:700; color:#166534; font-size:0.95rem;">Skills Learned</span>
          <span class="badge badge-bonus">${roleGapData.learned.length}</span>
        </div>
        <p style="font-size:0.8rem; color:#166534; margin-bottom:10px;">Medium / High proficiency recorded</p>
        <div>
          ${roleGapData.learned.length > 0 ? roleGapData.learned.map(s => `
            <div style="padding:4px 8px; background:#ffffff; border-radius:4px; margin-bottom:4px; font-size:0.82rem; font-weight:600; color:#166534;">
              ✓ ${s}
            </div>
          `).join("") : '<span style="font-size:0.82rem; color:#64748b;">None yet.</span>'}
        </div>
      </div>

      <!-- Needs Improvement (Low) -->
      <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-weight:700; color:#92400e; font-size:0.95rem;">Needs Improvement</span>
          <span class="badge badge-important">${roleGapData.needs_improvement.length}</span>
        </div>
        <p style="font-size:0.8rem; color:#92400e; margin-bottom:10px;">Low proficiency (0.4 multiplier)</p>
        <div>
          ${roleGapData.needs_improvement.length > 0 ? roleGapData.needs_improvement.map(s => `
            <div style="padding:4px 8px; background:#ffffff; border-radius:4px; margin-bottom:4px; font-size:0.82rem; font-weight:600; color:#92400e;">
              ▲ ${s}
            </div>
          `).join("") : '<span style="font-size:0.82rem; color:#64748b;">None.</span>'}
        </div>
      </div>

      <!-- Missing (Don't Know) -->
      <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-weight:700; color:#991b1b; font-size:0.95rem;">Missing (To Learn)</span>
          <span class="badge badge-core">${roleGapData.missing.length}</span>
        </div>
        <p style="font-size:0.8rem; color:#991b1b; margin-bottom:10px;">Will populate your Step 3 roadmap</p>
        <div>
          ${roleGapData.missing.length > 0 ? roleGapData.missing.map(s => `
            <div style="padding:4px 8px; background:#ffffff; border-radius:4px; margin-bottom:4px; font-size:0.82rem; font-weight:600; color:#991b1b;">
              ✕ ${s}
            </div>
          `).join("") : '<span style="font-size:0.82rem; color:#10b981; font-weight:600;">Zero missing skills!</span>'}
        </div>
      </div>

      <!-- Priority Areas & Actions -->
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
        <div style="font-weight:700; color:#334155; font-size:0.95rem; margin-bottom:8px;">Priority Actions</div>
        <p style="font-size:0.8rem; color:#64748b; margin-bottom:10px;">Core skills recommended first</p>
        <ul style="padding-left:18px; margin:0; font-size:0.82rem; color:#475569;">
          ${(roleGapData.suggested_actions || []).length > 0 ? roleGapData.suggested_actions.map(act => `
            <li style="margin-bottom:6px;">${act}</li>
          `).join("") : '<li>No priority actions needed.</li>'}
        </ul>
      </div>

    </div>

    <!-- Below the Result: Generate My Roadmap Callout -->
    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
      <div>
        <h4 style="font-size: 1.05rem; font-weight: 700; color: #1e3a8a; margin: 0 0 4px 0;">Ready for Step 3?</h4>
        <p style="font-size: 0.88rem; color: #2563eb; margin: 0;">
          Generate your personalized stage-by-stage learning roadmap covering all missing and low skills.
        </p>
      </div>
      <button class="btn btn-primary" style="padding: 10px 22px; font-weight: 600;" onclick="window.location.href='/pages/roadmap.html'">
        Generate My Roadmap →
      </button>
    </div>
  `;
  container.appendChild(resultsCard);

  // 4. Step Navigation Footer
  const footerDiv = document.createElement("div");
  footerDiv.className = "step-nav-footer";
  footerDiv.innerHTML = `
    <div>
      <a href="/pages/roles.html" class="btn btn-secondary">← Back: 1. Choose Role</a>
    </div>
    <div>
      <button class="btn btn-primary" onclick="window.location.href='/pages/roadmap.html'">
        Continue to Step 3: Roadmap →
      </button>
    </div>
  `;
  container.appendChild(footerDiv);
}

function setSkillKnown(skillName, knows) {
  if (!skillSelectionState[skillName]) {
    skillSelectionState[skillName] = { knows: false, level: "Low" };
  }
  skillSelectionState[skillName].knows = knows;
  renderSkillSelectionAndResults();
}

function setSkillLevel(skillName, level) {
  if (!skillSelectionState[skillName]) {
    skillSelectionState[skillName] = { knows: true, level: "Low" };
  }
  skillSelectionState[skillName].level = level;
  renderSkillSelectionAndResults();
}

function addExtraSkill() {
  const nameInput = document.getElementById("extra-skill-name");
  const levelSelect = document.getElementById("extra-skill-level");
  const name = (nameInput.value || "").trim();
  const level = levelSelect.value || "Medium";

  if (!name) {
    UI.toast("Please enter a skill name.", "warning");
    return;
  }

  extraSkills.push({ name, level });
  nameInput.value = "";
  renderSkillSelectionAndResults();
}

function removeExtraSkill(index) {
  extraSkills.splice(index, 1);
  renderSkillSelectionAndResults();
}

async function saveAndAnalyze() {
  const saveBtn = document.getElementById("save-analyze-btn");
  if (saveBtn) saveBtn.disabled = true;

  try {
    // Collect all skills marked as known
    const finalSkillsList = [];

    // 1. Role skills where knows == true
    for (const [sName, state] of Object.entries(skillSelectionState)) {
      if (state.knows) {
        finalSkillsList.push({
          name: sName,
          level: state.level // "Low", "Medium", "High"
        });
      }
    }

    // 2. Extra skills
    extraSkills.forEach(es => {
      finalSkillsList.push({
        name: es.name,
        level: es.level
      });
    });

    // Save to backend via PUT /api/skill-gap/skills
    await API.put("/api/skill-gap/skills", { skills: finalSkillsList });
    UI.toast("Skills saved! Recalculating skill match...", "success");

    // Refresh profile and skill gap data
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};
    UI.renderStepBar(2, currentProfile);

    const gapRes = await API.get("/api/skill-gap");
    roleGapData = gapRes.data;

    renderSkillSelectionAndResults();
  } catch (err) {
    UI.toast("Failed to save skills: " + err.message, "error");
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initSkillGap();
});
