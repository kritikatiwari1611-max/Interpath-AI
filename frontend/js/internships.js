// Internship matching client logic with "Prepare to apply" verification panel

let allInternships = [];
let appReadiness = {
  resume_uploaded: false,
  linkedin_added: false,
  github_added: false,
  all_ready: false
};
let pendingApplyUrl = null;

async function loadMatchedInternships() {
  const container = document.getElementById("internships-container");
  UI.showLoading(container, "Analyzing skill overlap and finding matched opportunities...");

  try {
    const res = await API.get("/api/internships");
    const data = res.data;
    allInternships = data.internships || [];
    if (data.application_readiness) {
      appReadiness = data.application_readiness;
    }
    renderInternships(allInternships, data.disclaimer);
  } catch (err) {
    UI.toast("Failed to load internships: " + err.message, "error");
  }
}

function renderInternships(list, disclaimer) {
  const container = document.getElementById("internships-container");
  container.innerHTML = "";

  if (list.length === 0) {
    UI.showEmpty(container, "No internship opportunities currently available.");
    return;
  }

  list.forEach(item => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "20px";
    card.style.borderLeft = item.match_pct >= 70 ? "4px solid #10b981" : "4px solid #3b82f6";

    // Application URL
    const applyUrl = item.application_url || "https://internshala.com";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div style="flex: 1; min-width: 280px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px; flex-wrap: wrap;">
            <span class="badge badge-tech">${item.organization}</span>
            <span class="badge badge-bonus">${item.location}</span>
            <span class="badge" style="background:#f1f5f9; color:#475569;">${item.duration}</span>
            <span class="badge" style="background:#fef3c7; color:#92400e;">${item.demo_label || 'Demo Listing'}</span>
          </div>

          <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${item.title}</h3>
          <p style="font-size: 0.88rem; color: #64748b; line-height: 1.5; margin-bottom: 12px;">${item.description}</p>
          
          <div style="font-size: 0.82rem; color: #475569; margin-bottom: 10px;">
            <strong>Eligibility:</strong> ${item.eligibility}
          </div>

          <!-- Why you match reasons -->
          ${item.reasons && item.reasons.length > 0 ? `
            <div style="background: #f8fafc; padding: 10px 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 12px; font-size: 0.82rem;">
              <strong style="color: #0f172a;">Why You Match:</strong>
              <ul style="padding-left: 18px; margin: 4px 0 0 0; color: #334155;">
                ${item.reasons.map(r => `<li>${r}</li>`).join("")}
              </ul>
            </div>
          ` : ''}

          <!-- Skills breakdown -->
          <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
            <span style="font-size: 0.75rem; font-weight: 600; color: #94a3b8;">Matched Skills:</span>
            ${item.matched_skills.map(s => `<span class="badge badge-bonus">✓ ${s}</span>`).join("")}
            ${item.missing_skills.length > 0 ? `<span style="font-size: 0.75rem; font-weight: 600; color: #94a3b8; margin-left: 8px;">Missing:</span>` : ''}
            ${item.missing_skills.map(s => `<span class="badge badge-core">✕ ${s}</span>`).join("")}
          </div>
        </div>

        <!-- Right Action Column: Match % & Prepare to Apply -->
        <div style="min-width: 200px; display: flex; flex-direction: column; gap: 12px;">
          <!-- Match Score -->
          <div style="text-align: center; padding: 14px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
            <div style="font-size: 2.2rem; font-weight: 800; color: ${item.match_pct >= 70 ? '#10b981' : '#2563eb'}; line-height: 1;">
              ${item.match_pct}%
            </div>
            <span style="font-size: 0.75rem; font-weight: 600; color: #64748b; display: block; margin-top: 4px;">Role Match</span>
          </div>

          <!-- Prepare to apply panel -->
          <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 0.78rem;">
            <div style="font-weight: 700; color: #1e293b; margin-bottom: 6px; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.5px;">
              Prepare to Apply:
            </div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <div>
                Resume: ${appReadiness.resume_uploaded 
                  ? '<span style="color:#16a34a; font-weight:700;">YES ✓</span>' 
                  : '<a href="/pages/application-profile.html" style="color:#ef4444; font-weight:600; text-decoration:none;">NO (Upload in Profile)</a>'}
              </div>
              <div>
                LinkedIn: ${appReadiness.linkedin_added 
                  ? '<span style="color:#16a34a; font-weight:700;">YES ✓</span>' 
                  : '<a href="/pages/application-profile.html" style="color:#f59e0b; font-weight:600; text-decoration:none;">NO (Add in Profile)</a>'}
              </div>
              <div>
                GitHub: ${appReadiness.github_added 
                  ? '<span style="color:#16a34a; font-weight:700;">YES ✓</span>' 
                  : '<a href="/pages/application-profile.html" style="color:#f59e0b; font-weight:600; text-decoration:none;">NO (Add in Profile)</a>'}
              </div>
            </div>
          </div>

          <!-- Apply Button -->
          <button class="btn btn-primary" style="width: 100%; padding: 10px 14px; font-weight: 600; font-size: 0.88rem;" onclick="handleApplyClick('${applyUrl}')">
            Apply Now ↗
          </button>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function handleApplyClick(url) {
  if (!appReadiness.all_ready) {
    // Show friendly warning modal
    pendingApplyUrl = url;
    const modal = document.getElementById("apply-warning-modal");
    if (modal) modal.style.display = "flex";
  } else {
    // Open external URL directly
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadMatchedInternships();

  const modal = document.getElementById("apply-warning-modal");
  const cancelBtn = document.getElementById("cancel-apply-btn");
  const proceedBtn = document.getElementById("proceed-apply-btn");

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      window.location.href = "/pages/application-profile.html";
    });
  }

  if (proceedBtn) {
    proceedBtn.addEventListener("click", () => {
      if (modal) modal.style.display = "none";
      if (pendingApplyUrl) {
        window.open(pendingApplyUrl, "_blank", "noopener,noreferrer");
        pendingApplyUrl = null;
      }
    });
  }
});
