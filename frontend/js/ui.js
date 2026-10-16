// UI helpers: notifications, safe text escaping, loading skeletons, and modal management

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
  }
};
