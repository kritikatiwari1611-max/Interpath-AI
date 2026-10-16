// Skill-gap analysis visualization logic

async function loadSkillGap() {
  const container = document.getElementById("skillgap-content");
  UI.showLoading(container, "Calculating skill gaps against target role...");

  try {
    const res = await API.get("/api/skill-gap");
    const data = res.data;

    if (!data.role_selected) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 24px;">
          <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Internship Role Selected</h3>
          <p style="color: #64748b; margin-bottom: 20px;">Please pick a target internship role to analyze your skill match.</p>
          <a href="/pages/roles.html" class="btn btn-primary">Browse Internship Roles</a>
        </div>
      `;
      return;
    }

    renderSkillGap(data);
  } catch (err) {
    UI.toast("Failed to load skill gap: " + err.message, "error");
  }
}

function renderSkillGap(data) {
  const container = document.getElementById("skillgap-content");
  container.innerHTML = `
    <!-- Top Summary Card -->
    <div class="card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);">
      <div>
        <span class="badge badge-tech" style="margin-bottom: 6px;">Target Role</span>
        <h2 style="font-size: 1.4rem; font-weight: 700;">${data.role_title}</h2>
        <p style="font-size: 0.88rem; color: #64748b;">Deterministic Skill Match against industry prerequisites</p>
      </div>

      <div style="text-align: right; min-width: 180px;">
        <div style="font-size: 2.2rem; font-weight: 800; color: #2563eb;">${data.overall_match_pct}%</div>
        <div class="progress-bar-container" style="width: 180px;">
          <div class="progress-bar-fill" style="width: ${data.overall_match_pct}%;"></div>
        </div>
        <span style="font-size: 0.78rem; color: #64748b;">Weighted Match Index</span>
      </div>
    </div>

    <!-- Priority Action Callout -->
    ${data.suggested_actions && data.suggested_actions.length > 0 ? `
      <div class="card" style="border-left: 4px solid #f59e0b; background-color: #fffbeb;">
        <h4 style="font-size: 0.95rem; font-weight: 600; color: #92400e; margin-bottom: 6px;">Recommended Priority Focus</h4>
        <ul style="padding-left: 20px; font-size: 0.88rem; color: #78350f;">
          ${data.suggested_actions.map(act => `<li style="margin-bottom: 4px;">${act}</li>`).join("")}
        </ul>
      </div>
    ` : ''}

    <!-- 4-Column Skill Breakdown -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 24px;">
      
      <!-- Learned / Strong -->
      <div class="card" style="border-top: 3px solid #10b981;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="font-size: 1rem; font-weight: 600;">Good / Strong</h3>
          <span class="badge badge-bonus">${data.learned.length}</span>
        </div>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 12px;">Proficiency verified at Intermediate or Advanced level.</p>
        <div>
          ${data.learned.length > 0 ? data.learned.map(s => `
            <div style="padding: 6px 10px; background: #f0fdf4; border-radius: 6px; margin-bottom: 6px; font-size: 0.85rem; font-weight: 500; color: #166534;">
              ✓ ${s}
            </div>
          `).join("") : '<p style="font-size: 0.85rem; color: #94a3b8;">None yet.</p>'}
        </div>
      </div>

      <!-- Needs Improvement -->
      <div class="card" style="border-top: 3px solid #f59e0b;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="font-size: 1rem; font-weight: 600;">Needs Improvement</h3>
          <span class="badge badge-important">${data.needs_improvement.length}</span>
        </div>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 12px;">Beginner level recorded (0.4 multiplier). Elevate with practice.</p>
        <div>
          ${data.needs_improvement.length > 0 ? data.needs_improvement.map(s => `
            <div style="padding: 6px 10px; background: #fffbeb; border-radius: 6px; margin-bottom: 6px; font-size: 0.85rem; font-weight: 500; color: #92400e;">
              ▲ ${s}
            </div>
          `).join("") : '<p style="font-size: 0.85rem; color: #94a3b8;">None.</p>'}
        </div>
      </div>

      <!-- Missing Skills -->
      <div class="card" style="border-top: 3px solid #ef4444;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="font-size: 1rem; font-weight: 600;">Missing Prerequisite</h3>
          <span class="badge badge-core">${data.missing.length}</span>
        </div>
        <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 12px;">Required skills not currently found in your profile.</p>
        <div>
          ${data.missing.length > 0 ? data.missing.map(s => `
            <div style="padding: 6px 10px; background: #fef2f2; border-radius: 6px; margin-bottom: 6px; font-size: 0.85rem; font-weight: 500; color: #991b1b;">
              ✕ ${s}
            </div>
          `).join("") : '<p style="font-size: 0.85rem; color: #10b981; font-weight: 500;">Zero missing skills! Great job.</p>'}
        </div>
      </div>

    </div>

    <!-- Complete Role Requirements Table -->
    <div class="card">
      <h3 class="card-title">All Requirements for ${data.role_title}</h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 12px;">
        <thead>
          <tr style="border-bottom: 2px solid #e2e8f0; text-align: left; color: #64748b;">
            <th style="padding: 8px 12px;">Skill Requirement</th>
            <th style="padding: 8px 12px;">Importance</th>
            <th style="padding: 8px 12px;">Your Stated Level</th>
            <th style="padding: 8px 12px;">Evaluation</th>
          </tr>
        </thead>
        <tbody>
          ${data.skills.map(s => {
            let impBadge = "badge-important";
            if (s.importance === "core") impBadge = "badge-core";
            else if (s.importance === "bonus") impBadge = "badge-bonus";

            let evalColor = "#10b981";
            if (s.status === "Missing") evalColor = "#ef4444";
            else if (s.status === "Needs improvement") evalColor = "#f59e0b";

            return `
              <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 12px; font-weight: 600;">${s.name}</td>
                <td style="padding: 10px 12px;"><span class="badge ${impBadge}">${s.importance}</span></td>
                <td style="padding: 10px 12px;">${s.user_level}</td>
                <td style="padding: 10px 12px; font-weight: 600; color: ${evalColor};">${s.status}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  loadSkillGap();
});
