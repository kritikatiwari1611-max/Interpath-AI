// Navigation topbar three-dot menu and sidebar toggle logic

document.addEventListener("DOMContentLoaded", () => {
  const threeDotBtn = document.getElementById("three-dot-btn");
  const dropdownMenu = document.getElementById("three-dot-dropdown");
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");

  // Toggle Three-dot (⋮) menu
  if (threeDotBtn && dropdownMenu) {
    threeDotBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isExpanded = threeDotBtn.getAttribute("aria-expanded") === "true";
      threeDotBtn.setAttribute("aria-expanded", !isExpanded);
      dropdownMenu.classList.toggle("show");
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
      if (!dropdownMenu.contains(e.target) && e.target !== threeDotBtn) {
        dropdownMenu.classList.remove("show");
        threeDotBtn.setAttribute("aria-expanded", "false");
      }
    });

    // Keyboard navigation (Escape, arrow keys)
    dropdownMenu.addEventListener("keydown", (e) => {
      const items = Array.from(dropdownMenu.querySelectorAll(".dropdown-item"));
      const currentIndex = items.indexOf(document.activeElement);

      if (e.key === "Escape") {
        dropdownMenu.classList.remove("show");
        threeDotBtn.focus();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % items.length;
        items[nextIndex].focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prevIndex = (currentIndex - 1 + items.length) % items.length;
        items[prevIndex].focus();
      }
    });
  }

  // Mobile sidebar drawer toggle
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }
});
