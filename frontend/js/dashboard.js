// Dashboard aggregator logic: pulls together profile, readiness, roadmap, and recent activity

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  UI.showLoading(container, "Loading your customized career dashboard...");

  try {
    // Parallel fetch profile, readiness, roadmap, progress, and internships
    const [profileRes, readinessRes, roadmapRes, progressRes, internshipsRes] = await Promise.all([
      API.get("/api/profile"),
      API.get("/api/readiness"),
      API.get("/api/roadmap"),
      API.get("/api/progress"),
      API.get("/api/internships")
    ]);

    const profileData = profileRes.data.profile;
    const readinessData = readinessRes.data;
    const roadmapData = roadmapRes.data;
    const progressData = progressRes.data;
    const topInternships = (internshipsRes.data.internships || []).slice(0, 3);

    renderDashboard(profileData, readinessData, roadmapData, progressData, topInternships);
  } catch (err) {
    UI.toast("Failed to load dashboard: " + err.message, "error");
  }
}

function renderDashboard(profile, readiness, roadmap, progress, topInternships) {
  const container = document.getElementById("dashboard-content");

  container.innerHTML = `
    <!-- Hero Welcome Banner -->
    <div class="card" style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); color: #ffffff; padding: 28px;">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
          <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
            ${profile.course || 'Degree Program'} • ${profile.semester || 'Current Semester'}
          </span>
          <h2 style="font-size: 1.6rem; font-weight: 700; margin-top: 8px;">Welcome back to InternPath AI!</h2>
          <p style="font-size: 0.95rem; opacity: 0.9; margin-top: 4px;">
            Target Track: <strong>${readiness.role_title || 'No Role Selected'}</strong>
          </p>
        </div>

        <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(8px); padding: 16px 24px; border-radius: 12px; text-align: center;">
          <div style="font-size: 2.2rem; font-weight: 800; line-height: 1;">${readiness.overall}%</div>
          <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85;">Readiness Score</span>
        </div>
      </div>
    </div>

    <!-- Quick Action / Summary Grid -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 24px;">
      
      <!-- Skill Gap Quick Summary -->
      <div class="card">
        <h3 class="card-title">Skills Status</h3>
        <p class="card-subtitle">Skills to elevate for ${readiness.role_title || 'your role'}</p>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
          <span style="font-size: 1.5rem; font-weight: 700; color: #2563eb;">${readiness.category_scores ? readiness.category_scores.skills : 0}%</span>
          <span class="badge badge-bonus">${progress.skills_improved} Improved</span>
        </div>
        <a href="/pages/skill-gap.html" class="btn btn-outline" style="width: 100%; font-size: 0.82rem; padding: 6px;">View Skill Gap Analysis →</a>
      </div>

      <!-- Roadmap Quick Summary -->
      <div class="card">
        <h3 class="card-title">Roadmap Tasks</h3>
        <p class="card-subtitle">Stage-by-stage learning trajectory</p>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
          <span style="font-size: 1.5rem; font-weight: 700; color: #10b981;">${roadmap.progress_pct || 0}%</span>
          <span style="font-size: 0.82rem; color: #64748b;">${roadmap.completed_tasks || 0} / ${roadmap.total_tasks || 0} Completed</span>
        </div>
        <div class="progress-bar-container" style="margin-bottom: 12px;">
          <div class="progress-bar-fill" style="width: ${roadmap.progress_pct || 0}%;"></div>
        </div>
        <a href="/pages/roadmap.html" class="btn btn-outline" style="width: 100%; font-size: 0.82rem; padding: 6px;">Open My Roadmap →</a>
      </div>

      <!-- Interview Preparation Quick Summary -->
      <div class="card">
        <h3 class="card-title">Interview Readiness</h3>
        <p class="card-subtitle">Simulated mock interview drills</p>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
          <span style="font-size: 1.5rem; font-weight: 700; color: #f59e0b;">${progress.practice_accuracy || 0}%</span>
          <span style="font-size: 0.82rem; color: #64748b;">${progress.mock_interviews_done || 0} Mocks Finished</span>
        </div>
        <a href="/pages/interview.html" class="btn btn-outline" style="width: 100%; font-size: 0.82rem; padding: 6px;">Practice Mock Interviews →</a>
      </div>

    </div>

    <!-- Matched Internships Carousel / List Preview -->
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div>
          <h3 class="card-title" style="margin-bottom: 2px;">Top Matched Internships (Demo Data)</h3>
          <p class="card-subtitle" style="margin-bottom: 0;">Opportunities aligned with your current profile and target role.</p>
        </div>
        <a href="/pages/internships.html" class="btn btn-secondary" style="font-size: 0.82rem; padding: 6px 12px;">View All Internships</a>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
        ${topInternships.map(item => `
          <div style="padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span class="badge badge-tech">${item.organization}</span>
                <span style="font-weight: 700; color: #10b981; font-size: 0.95rem;">${item.match_pct}% Match</span>
              </div>
              <h4 style="font-size: 1rem; font-weight: 600; margin-bottom: 4px;">${item.title}</h4>
              <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 8px;">${item.location} • ${item.duration}</p>
            </div>
            <a href="/pages/internships.html" style="font-size: 0.8rem; color: #2563eb; font-weight: 600; text-decoration: none;">View Requirements →</a>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});
