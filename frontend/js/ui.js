// UI helpers: notifications, safe text escaping, loading skeletons, step bar, and flow navigation

const GUIDED_STEPS = [
  { step: 1, title: "Choose Role", url: "/pages/roles.html" },
  { step: 2, title: "Skill Gap", url: "/pages/skill-gap.html" },
  { step: 3, title: "Roadmap & Learning", url: "/pages/roadmap.html" },
  { step: 4, title: "Projects", url: "/pages/projects.html" },
  { step: 5, title: "Readiness Score", url: "/pages/readiness.html" },
  { step: 6, title: "Application Profile", url: "/pages/application-profile.html" }
];

const UI = {
  // Always render user and dynamic text safely with textContent (avoiding innerHTML vulnerabilities)
  safeText(el, text) {
    if (el) el.textContent = text != null ? text : "";
  },

  toast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.style.position = "fixed";
      container.style.bottom = "24px";
      container.style.right = "24px";
      container.style.zIndex = "9999";
      container.style.display = "flex";
      container.style.flexDirection = "column";
      container.style.gap = "8px";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.style.padding = "12px 18px";
    toast.style.borderRadius = "8px";
    toast.style.fontSize = "0.88rem";
    toast.style.fontWeight = "500";
    toast.style.color = "#ffffff";
    toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
    toast.style.transition = "all 0.3s ease";

    if (type === "success") toast.style.backgroundColor = "#10b981";
    else if (type === "error") toast.style.backgroundColor = "#ef4444";
    else if (type === "warning") toast.style.backgroundColor = "#f59e0b";
    else toast.style.backgroundColor = "#2563eb";

    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  showLoading(container, message = "Loading...") {
    if (!container) return;
    container.innerHTML = `
      <div style="padding: 32px; text-align: center; color: #64748b;">
        <div style="display: inline-block; width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
        <p style="margin-top: 12px; font-size: 0.9rem;">${message}</p>
      </div>
      <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
    `;
  },

  showEmpty(container, message = "No data found.") {
    if (!container) return;
    container.innerHTML = `
      <div style="padding: 40px 20px; text-align: center; color: #64748b;">
        <p style="font-size: 1rem; margin-bottom: 8px;">📋</p>
        <p style="font-size: 0.9rem;">${message}</p>
      </div>
    `;
  },

  // Check URL query parameters for polite redirect messages
  checkUrlMessages() {
    const params = new URLSearchParams(window.location.search);
    const msg = params.get("msg");
    if (msg === "role_required") {
      UI.toast("Please choose a target role first before proceeding.", "warning");
    } else if (msg === "skills_required") {
      UI.toast("Please analyze your skills first to generate your roadmap.", "warning");
    } else if (msg === "profile_updated") {
      UI.toast("Application profile updated successfully!", "success");
    }
  },

  // Check whether the student meets prerequisites for a given step; redirect politely if not
  checkPrerequisites(currentStepNum, profile) {
    if (!profile) return true;
    if (currentStepNum > 1 && !profile.selected_role_id) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return false;
    }
    if (currentStepNum > 2 && (!profile.skills || profile.skills.length === 0)) {
      window.location.href = "/pages/skill-gap.html?msg=skills_required";
      return false;
    }
    return true;
  },

  // Step bar removed per user request
  renderStepBar(currentStepNum, profile = null) {
    const wrapper = document.getElementById("step-bar-container");
    if (wrapper) wrapper.remove();
  },

  // Helper to render standard Back / Next footer buttons
  renderStepFooter(containerId, prevUrl, prevLabel, nextUrl, nextLabel) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.className = "step-nav-footer";
    container.innerHTML = `
      <div>
        ${prevUrl ? `<a href="${prevUrl}" class="btn btn-secondary">← Back: ${prevLabel}</a>` : ''}
      </div>
      <div>
        ${nextUrl ? `<a href="${nextUrl}" class="btn btn-primary" id="step-next-btn">${nextLabel} →</a>` : ''}
      </div>
    `;
  }
};

// Auto check for URL notifications on load
document.addEventListener("DOMContentLoaded", () => {
  UI.checkUrlMessages();
});
