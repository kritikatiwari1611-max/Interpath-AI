// Progress page client logic: aggregate activity cards and progress bars

async function loadProgressOverview() {
  const container = document.getElementById("progress-content");
  UI.showLoading(container, "Calculating progress metrics across activity...");

  try {
    const res = await API.get("/api/progress");
    const data = res.data;
    renderProgress(data);
  } catch (err) {
    UI.toast("Failed to load progress: " + err.message, "error");
  }
}

function renderProgress(data) {
  const container = document.getElementById("progress-content");

  container.innerHTML = `
    <!-- Top Overall Progress Card -->
    <div class="card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);">
      <div>
        <span class="badge badge-tech" style="margin-bottom: 6px;">Holistic Progress</span>
        <h2 style="font-size: 1.4rem; font-weight: 700;">Preparation Completion Track</h2>
        <p style="font-size: 0.88rem; color: #64748b;">Computed deterministically from your recorded roadmap, practice tests, and projects.</p>
      </div>

      <div style="text-align: right; min-width: 200px;">
        <div style="font-size: 2.6rem; font-weight: 800; color: #2563eb;">${data.overall_progress}%</div>
        <div class="progress-bar-container" style="width: 200px;">
          <div class="progress-bar-fill" style="width: ${data.overall_progress}%;"></div>
        </div>
        <span style="font-size: 0.78rem; color: #64748b;">Overall Milestone Completion</span>
      </div>
    </div>

    <!-- 5 Pillar Metrics Grid -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-bottom: 24px;">
      
      <div class="card" style="margin-bottom: 0;">
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Skills Improved</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #10b981;">${data.skills_improved}</div>
        <span style="font-size: 0.75rem; color: #94a3b8;">Out of ${data.total_skills} recorded skills</span>
      </div>

      <div class="card" style="margin-bottom: 0;">
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Roadmap Tasks</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #2563eb;">${data.roadmap_pct}%</div>
        <span style="font-size: 0.75rem; color: #94a3b8;">${data.completed_tasks} / ${data.total_tasks} Tasks Finished</span>
      </div>

      <div class="card" style="margin-bottom: 0;">
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Hub Resources Done</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #8b5cf6;">${data.resources_completed}</div>
        <span style="font-size: 0.75rem; color: #94a3b8;">Tutorials & Exercises completed</span>
      </div>

      <div class="card" style="margin-bottom: 0;">
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Practice Attempts</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #f59e0b;">${data.practice_attempted}</div>
        <span style="font-size: 0.75rem; color: #94a3b8;">${data.practice_accuracy}% Accuracy</span>
      </div>

      <div class="card" style="margin-bottom: 0;">
        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Completed Projects</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #06b6d4;">${data.projects_completed}</div>
        <span style="font-size: 0.75rem; color: #94a3b8;">Portfolio Projects verified</span>
      </div>

    </div>

    <!-- Recent Mock Interview History -->
    <div class="card">
      <h3 class="card-title">Recent Mock Interview Sessions</h3>
      ${data.recent_mocks && data.recent_mocks.length > 0 ? `
        <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 12px;">
          <thead>
            <tr style="border-bottom: 2px solid #e2e8f0; text-align: left; color: #64748b;">
              <th style="padding: 8px 12px;">Date</th>
              <th style="padding: 8px 12px;">Score</th>
              <th style="padding: 8px 12px;">Accuracy</th>
              <th style="padding: 8px 12px;">Status</th>
            </tr>
          </thead>
          <tbody>
            ${data.recent_mocks.map(m => `
              <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 12px;">${m.created_at || 'Recent'}</td>
                <td style="padding: 10px 12px; font-weight: 700; color: #2563eb;">${m.score}%</td>
                <td style="padding: 10px 12px;">${m.accuracy}%</td>
                <td style="padding: 10px 12px;"><span class="badge badge-bonus">Completed</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      ` : '<p style="font-size: 0.88rem; color: #64748b; margin-top: 8px;">No mock interviews recorded yet. Complete one under Interview Prep.</p>'}
    </div>

    <!-- Flow Navigation Footer -->
    <div class="step-nav-footer" style="margin-top: 24px;">
      <div>
        <a href="/pages/interview.html" class="btn btn-secondary">← Back: Interview Prep</a>
      </div>
      <div>
        <button class="btn btn-primary" onclick="window.location.href='/pages/dashboard.html'">
          Back to Dashboard →
        </button>
      </div>
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  loadProgressOverview();
});
