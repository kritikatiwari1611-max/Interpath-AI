// Deterministic readiness score UI rendering logic

async function loadReadinessScore(lang = "en") {
  const container = document.getElementById("readiness-content");
  UI.showLoading(container, "Calculating deterministic readiness score...");

  try {
    const res = await API.get(`/api/readiness?lang=${lang}`);
    const data = res.data;
    renderReadiness(data);
  } catch (err) {
    UI.toast("Failed to load readiness: " + err.message, "error");
  }
}

function renderReadiness(data) {
  const container = document.getElementById("readiness-content");

  if (data.provisional) {
    container.innerHTML = `
      <div class="card" style="border-left: 4px solid #f59e0b; background-color: #fffbeb;">
        <div style="display: flex; gap: 12px; align-items: flex-start;">
          <div style="font-size: 1.8rem;">⚠️</div>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 700; color: #92400e; margin-bottom: 6px;">Provisional / Incomplete Readiness Profile</h3>
            <p style="font-size: 0.9rem; color: #78350f; margin-bottom: 12px;">
              ${data.reasons ? data.reasons.join(" ") : 'Your profile lacks sufficient data to generate a finalized score.'}
            </p>
            <div style="font-size: 0.85rem; font-weight: 600; color: #92400e; margin-bottom: 6px;">Action Items to Unlock Full Score:</div>
            <ul style="padding-left: 20px; font-size: 0.85rem; color: #78350f; margin-bottom: 16px;">
              ${(data.next_actions || []).map(act => `<li>${act}</li>`).join("")}
            </ul>
            <a href="/pages/profile.html" class="btn btn-primary" style="font-size: 0.85rem; padding: 8px 16px;">Complete My Profile</a>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const scores = data.category_scores || {};
  const weights = data.weights || {};

  container.innerHTML = `
    <!-- Top Overall Score Card -->
    <div class="card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 24px; background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);">
      <div>
        <span class="badge badge-tech" style="margin-bottom: 6px;">Target: ${data.role_title}</span>
        <h2 style="font-size: 1.4rem; font-weight: 700;">Internship Readiness Score</h2>
        <p style="font-size: 0.88rem; color: #64748b; max-width: 520px;">
          Deterministic composite based on weighted skills, project relevance, resume compliance, interview practice, and certifications.
        </p>
      </div>

      <div style="text-align: center; min-width: 200px;">
        <div style="font-size: 3rem; font-weight: 800; color: #2563eb; line-height: 1;">${data.overall}%</div>
        <span style="font-size: 0.85rem; font-weight: 600; color: #0f172a;">${getReadinessLabel(data.overall)}</span>
        <div class="progress-bar-container" style="width: 180px; margin: 8px auto 4px;">
          <div class="progress-bar-fill" style="width: ${data.overall}%;"></div>
        </div>
        <span style="font-size: 0.75rem; color: #64748b;">Deterministic Scale (0-100)</span>
      </div>
    </div>

    <!-- AI / Rule-based Feedback Callout -->
    ${data.ai_feedback ? `
      <div class="card" style="border-left: 4px solid #3b82f6; background-color: #f8fafc;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h4 style="font-size: 0.95rem; font-weight: 700; color: #0f172a;">Preparation Summary & Coaching</h4>
          <span class="badge badge-tech">${data.ai_feedback.badge}</span>
        </div>
        <p style="font-size: 0.9rem; color: #334155; line-height: 1.6; margin-bottom: 8px;">
          ${data.ai_feedback.summary}
        </p>
        <div style="font-size: 0.85rem; color: #1d4ed8; background: #eff6ff; padding: 10px 14px; border-radius: 6px;">
          <strong>💡 Action Tip:</strong> ${data.ai_feedback.improvement_tip}
        </div>
      </div>
    ` : ''}

    <!-- 5 Weighted Category Bars -->
    <div class="card">
      <h3 class="card-title">Detailed Category Breakdown</h3>
      <p class="card-subtitle">Each component represents a weighted pillar of employability.</p>

      <div style="display: flex; flex-direction: column; gap: 16px; margin-top: 16px;">
        
        <!-- Skills -->
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
            <span>1. Core & Required Skills (${weights.skills || 35}% Weight)</span>
            <strong>${scores.skills || 0}%</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${scores.skills || 0}%;"></div>
          </div>
          <span style="font-size: 0.78rem; color: #64748b;">Derived directly from role-specific skill gap analysis.</span>
        </div>

        <!-- Projects -->
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
            <span>2. Portfolio Projects (${weights.projects || 25}% Weight)</span>
            <strong>${scores.projects || 0}%</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${scores.projects || 0}%;"></div>
          </div>
          <span style="font-size: 0.78rem; color: #64748b;">${data.matched_projects_count || 0} relevant projects matched against keywords.</span>
        </div>

        <!-- Resume -->
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
            <span>3. Resume Checklist (${weights.resume || 15}% Weight)</span>
            <strong>${scores.resume || 0}%</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${scores.resume || 0}%;"></div>
          </div>
          <span style="font-size: 0.78rem; color: #64748b;">Structured 6-point checklist verification.</span>
        </div>

        <!-- Interview -->
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
            <span>4. Interview Preparation (${weights.interview || 20}% Weight)</span>
            <strong>${scores.interview || 0}%</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${scores.interview || 0}%;"></div>
          </div>
          <span style="font-size: 0.78rem; color: #64748b;">Derived from question attempts, accuracy, and completed mock interviews.</span>
        </div>

        <!-- Certifications -->
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 500;">
            <span>5. Certifications (${weights.certifications || 5}% Weight)</span>
            <strong>${scores.certifications || 0}%</strong>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${scores.certifications || 0}%;"></div>
          </div>
          <span style="font-size: 0.78rem; color: #64748b;">${data.valid_certifications_count || 0} credential(s) matched to role keywords.</span>
        </div>

      </div>
    </div>

    <!-- Priority Improvement Checklist & Next Steps -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
      <div class="card">
        <h4 style="font-size: 1rem; font-weight: 600; margin-bottom: 8px;">Recommended Next Steps:</h4>
        <ul style="padding-left: 20px; font-size: 0.88rem; color: #475569; line-height: 1.6;">
          ${(data.next_actions || []).map(a => `<li>${a}</li>`).join("")}
        </ul>
      </div>

      <div class="card" style="background: #f8fafc;">
        <h4 style="font-size: 0.95rem; font-weight: 600; margin-bottom: 8px;">How This Score Was Calculated</h4>
        <p style="font-size: 0.82rem; color: #64748b; line-height: 1.5;">
          Formula: Overall = (Skills * ${weights.skills} + Projects * ${weights.projects} + Resume * ${weights.resume} + Interview * ${weights.interview} + Certs * ${weights.certifications}) / 100.
          All calculations are 100% deterministic and auditable.
        </p>
        <div style="margin-top: 12px; font-size: 0.75rem; color: #94a3b8; font-style: italic;">
          "${data.disclaimer}"
        </div>
      </div>
    </div>
  `;
}

function getReadinessLabel(score) {
  if (score >= 80) return "Ready to Apply 🚀";
  if (score >= 60) return "Competitive Candidate 👍";
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
