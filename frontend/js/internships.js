// Internship matching client logic

let allInternships = [];

async function loadMatchedInternships() {
  const container = document.getElementById("internships-container");
  UI.showLoading(container, "Analyzing skill overlap and finding matched opportunities...");

  try {
    const res = await API.get("/api/internships");
    const data = res.data;
    allInternships = data.internships || [];
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
    card.style.marginBottom = "18px";
    card.style.borderLeft = item.match_pct >= 70 ? "4px solid #10b981" : "4px solid #3b82f6";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div style="flex: 1; min-width: 280px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px;">
            <span class="badge badge-tech">${item.organization}</span>
            <span class="badge badge-bonus">${item.location}</span>
            <span class="badge" style="background:#f1f5f9; color:#475569;">${item.duration}</span>
            <span class="badge" style="background:#fef3c7; color:#92400e;">${item.demo_label}</span>
          </div>

          <h3 style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${item.title}</h3>
          <p style="font-size: 0.88rem; color: #64748b; line-height: 1.5; margin-bottom: 12px;">${item.description}</p>
          
          <div style="font-size: 0.8rem; color: #475569; margin-bottom: 8px;">
            <strong>Eligibility:</strong> ${item.eligibility}
          </div>

          <!-- Why you match reasons -->
          ${item.reasons && item.reasons.length > 0 ? `
            <div style="background: #f8fafc; padding: 10px 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 12px; font-size: 0.82rem;">
              <strong style="color: #0f172a;">Why You Match:</strong>
              <ul style="padding-left: 18px; margin-top: 4px; color: #334155;">
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

        <!-- Match Score Ring -->
        <div style="text-align: center; min-width: 140px; padding: 16px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
          <div style="font-size: 2.2rem; font-weight: 800; color: ${item.match_pct >= 70 ? '#10b981' : '#2563eb'}; line-height: 1;">
            ${item.match_pct}%
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; color: #64748b; display: block; margin-top: 4px;">Calculated Match</span>
          <button class="btn btn-secondary" style="margin-top: 12px; width: 100%; font-size: 0.78rem; padding: 6px 8px;" onclick="viewNotice()">
            Demo Listing
          </button>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function viewNotice() {
  UI.toast("Demo opportunity only: No real application is submitted.", "info");
}

document.addEventListener("DOMContentLoaded", () => {
  loadMatchedInternships();
});
