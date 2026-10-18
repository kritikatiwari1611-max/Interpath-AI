// Step 5: Internship Readiness Score client logic

let currentProfile = null;

async function loadReadinessScore(lang = "en") {
  const container = document.getElementById("readiness-content");
  UI.showLoading(container, "Calculating deterministic readiness score...");

  try {
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};

    if (!currentProfile.selected_role_id) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return;
    }

    UI.renderStepBar(5, currentProfile);

    const res = await API.get(`/api/readiness?lang=${lang}`);
    const data = res.data;
    renderReadiness(data);
  } catch (err) {
    UI.toast("Failed to load readiness: " + err.message, "error");
  }
}

function renderReadiness(data) {
  const container = document.getElementById("readiness-content");
  container.innerHTML = "";

  const score = data.overall || 0;
  const isReady = score >= 65;
  const scores = data.category_scores || {};
  const weights = data.weights || {};
  const checklist = data.completion_checklist || [];

  // Top Overall Score Card
  const scoreCard = document.createElement("div");
  scoreCard.className = "card";
  scoreCard.style.background = "linear-gradient(135deg, #ffffff 0%, #eff6ff 100%)";
  scoreCard.style.marginBottom = "20px";

  scoreCard.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 24px;">
      <div>
        <span class="badge badge-tech" style="margin-bottom: 6px;">Target: ${data.role_title}</span>
        <h2 style="font-size: 1.4rem; font-weight: 700; color: #0f172a; margin: 0 0 6px 0;">Internship Readiness Score</h2>
        <p style="font-size: 0.88rem; color: #64748b; max-width: 520px; margin: 0;">
          Deterministic calculation based on weighted skills, portfolio projects, resume compliance, interview readiness, and certifications.
        </p>
      </div>

      <div style="text-align: center; min-width: 200px;">
        <div style="font-size: 3.2rem; font-weight: 800; color: #2563eb; line-height: 1;">${score}%</div>
        <span style="font-size: 0.88rem; font-weight: 700; color: #0f172a;">${getReadinessLabel(score)}</span>
        <div class="progress-bar-container" style="width: 180px; margin: 8px auto 4px;">
          <div class="progress-bar-fill" style="width: ${score}%;"></div>
        </div>
        <span style="font-size: 0.75rem; color: #64748b;">Threshold to Apply: 65%</span>
      </div>
    </div>

    <!-- Threshold Banner directly under overall score -->
    <div style="margin-top: 20px; padding: 14px 18px; border-radius: 8px; ${isReady ? 'background:#f0fdf4; border:1px solid #86efac; color:#166534;' : 'background:#fffbeb; border:1px solid #fde68a; color:#92400e;'}">
      <div style="font-size: 0.95rem; font-weight: 700; margin-bottom: 2px;">
        ${isReady ? '🎉 Ready to apply!' : '⏳ Not ready to apply yet.'}
      </div>
      <p style="font-size: 0.88rem; margin: 0;">
        ${isReady 
          ? 'Ready to apply! Continue to add your links and browse internships.'
          : 'Not ready to apply yet. We recommend reaching at least 65% by finishing priority roadmap skills and at least one project.'}
      </p>
    </div>
  `;
  container.appendChild(scoreCard);

  // 9-Item Completion Checklist Card
  const checklistCard = document.createElement("div");
  checklistCard.className = "card";
  checklistCard.style.marginBottom = "24px";

  const completedCount = checklist.filter(c => c.done).length;

  checklistCard.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:8px;">
      <div>
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin:0;">
          9-Point Internship Readiness Checklist
        </h3>
        <p style="font-size: 0.85rem; color: #64748b; margin: 4px 0 0 0;">
          Tick each milestone to maximize your recruiter competitiveness.
        </p>
      </div>
      <span class="badge ${completedCount >= 7 ? 'badge-bonus' : 'badge-important'}">
        ${completedCount} of ${checklist.length} Completed
      </span>
    </div>

    <div style="display:flex; flex-direction:column; gap:8px;">
      ${checklist.map((item, idx) => `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding:10px 14px; background:${item.done ? '#f0fdf4' : '#f8fafc'}; border:1px solid ${item.done ? '#bbf7d0' : '#e2e8f0'}; border-radius:6px;">
          <div style="display:flex; align-items:center; gap:12px;">
            <span style="width:24px; height:24px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem; background:${item.done ? '#16a34a' : '#e2e8f0'}; color:${item.done ? '#ffffff' : '#94a3b8'};">
              ${item.done ? '✓' : '○'}
            </span>
            <span style="font-size:0.9rem; font-weight:600; color:${item.done ? '#166534' : '#334155'};">
              ${item.item}
            </span>
          </div>

          <a href="${item.link}" class="btn btn-secondary" style="font-size:0.78rem; padding:4px 10px;">
            ${item.step ? `Go to ${item.step} →` : 'Open →'}
          </a>
        </div>
      `).join("")}
    </div>

    <!-- Direct Action Buttons below Checklist -->
    <div style="margin-top:20px; padding-top:16px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
      <a href="/pages/interview.html" class="btn btn-secondary" style="font-size:0.88rem;">
        🎯 Practice Mock Interview
      </a>

      <button class="btn btn-primary" style="padding:10px 22px; font-weight:600;" onclick="window.location.href='/pages/application-profile.html'">
        Add Resume and Links →
      </button>
    </div>
  `;
  container.appendChild(checklistCard);

  // Category Breakdown Card
  const breakdownCard = document.createElement("div");
  breakdownCard.className = "card";
  breakdownCard.style.marginBottom = "24px";
  breakdownCard.innerHTML = `
    <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 16px;">Detailed Weighted Pillars</h3>
    
    <div style="display: flex; flex-direction: column; gap: 16px;">
      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
          <span>1. Core & Required Skills (${weights.skills || 35}% Weight)</span>
          <strong>${scores.skills || 0}%</strong>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${scores.skills || 0}%;"></div></div>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
          <span>2. Portfolio Projects (${weights.projects || 25}% Weight)</span>
          <strong>${scores.projects || 0}%</strong>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${scores.projects || 0}%;"></div></div>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
          <span>3. Resume Quality Checklist (${weights.resume || 15}% Weight)</span>
          <strong>${scores.resume || 0}%</strong>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${scores.resume || 0}%;"></div></div>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
          <span>4. Interview Preparation (${weights.interview || 20}% Weight)</span>
          <strong>${scores.interview || 0}%</strong>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${scores.interview || 0}%;"></div></div>
      </div>

      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
          <span>5. Certifications (${weights.certifications || 5}% Weight)</span>
          <strong>${scores.certifications || 0}%</strong>
        </div>
        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${scores.certifications || 0}%;"></div></div>
      </div>
    </div>
  `;
  container.appendChild(breakdownCard);

  // AI Coaching Tips
  if (data.ai_feedback) {
    const aiCard = document.createElement("div");
    aiCard.className = "card";
    aiCard.style.borderLeft = "4px solid #3b82f6";
    aiCard.style.background = "#f8fafc";
    aiCard.style.marginBottom = "24px";
    aiCard.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin:0;">AI Coach Feedback</h4>
        <span class="badge badge-tech">${data.ai_feedback.badge}</span>
      </div>
      <p style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-bottom: 8px;">
        ${data.ai_feedback.summary}
      </p>
      <div style="font-size: 0.85rem; color: #1d4ed8; background: #eff6ff; padding: 10px 14px; border-radius: 6px;">
        <strong>💡 Action Tip:</strong> ${data.ai_feedback.improvement_tip}
      </div>
    `;
    container.appendChild(aiCard);
  }

  // Navigation Footer
  const footerDiv = document.createElement("div");
  footerDiv.className = "step-nav-footer";
  footerDiv.innerHTML = `
    <div>
      <a href="/pages/projects.html" class="btn btn-secondary">← Back: Projects</a>
    </div>
    <div>
      <button class="btn btn-primary" onclick="window.location.href='/pages/application-profile.html'">
        Continue to Application Profile →
      </button>
    </div>
  `;
  container.appendChild(footerDiv);
}

function getReadinessLabel(score) {
  if (score >= 80) return "Ready to Apply 🚀";
  if (score >= 65) return "Competitive Candidate 👍";
  if (score >= 40) return "Developing Foundation ⏳";
  return "Initial Stage 🌱";
}

document.addEventListener("DOMContentLoaded", () => {
  loadReadinessScore();
  const langSelect = document.getElementById("readiness-lang-select");
  if (langSelect) {
    langSelect.addEventListener("change", (e) => loadReadinessScore(e.target.value));
  }
});
