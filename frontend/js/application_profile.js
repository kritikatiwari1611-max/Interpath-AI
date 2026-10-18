// Step 6: Application Profile client logic (Resume, LinkedIn, GitHub)

let currentProfile = null;

async function initApplicationProfile() {
  try {
    const res = await API.get("/api/profile");
    currentProfile = res.data.profile || {};

    if (!currentProfile.selected_role_id) {
      window.location.href = "/pages/roles.html?msg=role_required";
      return;
    }

    UI.renderStepBar(6, currentProfile);
    populateProfileData();
  } catch (err) {
    UI.toast("Failed to load profile: " + err.message, "error");
  }
}

function populateProfileData() {
  if (!currentProfile) return;

  // 1. Resume panel
  const resumeBadge = document.getElementById("resume-status-badge");
  const existingPanel = document.getElementById("existing-resume-panel");
  const resumeNameEl = document.getElementById("current-resume-name");
  const downloadBtn = document.getElementById("download-resume-btn");

  if (currentProfile.resume_filename) {
    if (resumeBadge) {
      resumeBadge.className = "badge badge-bonus";
      resumeBadge.textContent = "✓ Uploaded";
    }
    if (existingPanel) existingPanel.style.display = "block";
    if (resumeNameEl) {
      resumeNameEl.textContent = currentProfile.resume_original_name || currentProfile.resume_filename;
    }
    if (downloadBtn) {
      downloadBtn.href = `/api/uploads/${currentProfile.resume_filename}`;
    }
  } else {
    if (resumeBadge) {
      resumeBadge.className = "badge badge-important";
      resumeBadge.textContent = "Not Uploaded";
    }
    if (existingPanel) existingPanel.style.display = "none";
  }

  // 2. Links
  const linkedinInput = document.getElementById("link-linkedin");
  const githubInput = document.getElementById("link-github");
  const portfolioInput = document.getElementById("link-portfolio");

  if (linkedinInput) linkedinInput.value = currentProfile.linkedin_link || "";
  if (githubInput) githubInput.value = currentProfile.github_link || "";
  if (portfolioInput) portfolioInput.value = currentProfile.portfolio_link || "";
}

async function handleResumeUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById("resume-file-input");
  const uploadBtn = document.getElementById("upload-resume-btn");

  if (!fileInput || fileInput.files.length === 0) {
    UI.toast("Please choose a PDF or DOCX resume to upload.", "warning");
    return;
  }

  const file = fileInput.files[0];
  if (file.size > 2 * 1024 * 1024) {
    UI.toast("Resume file size exceeds 2 MB limit.", "error");
    return;
  }

  const ext = file.name.split(".").pop().toLowerCase();
  if (ext !== "pdf" && ext !== "docx") {
    UI.toast("Only PDF and DOCX files are permitted.", "error");
    return;
  }

  uploadBtn.disabled = true;
  uploadBtn.textContent = "Uploading...";

  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await API.postForm("/api/profile/resume-upload", formData);
    UI.toast("Resume uploaded successfully!", "success");
    fileInput.value = "";

    // Refresh profile state
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};
    UI.renderStepBar(6, currentProfile);
    populateProfileData();
  } catch (err) {
    UI.toast("Resume upload failed: " + err.message, "error");
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Upload Resume";
  }
}

async function deleteResume() {
  if (!confirm("Are you sure you want to remove your resume?")) return;

  try {
    await API.post("/api/profile/resume-delete", {});
    UI.toast("Resume removed.", "success");

    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};
    UI.renderStepBar(6, currentProfile);
    populateProfileData();
  } catch (err) {
    UI.toast("Failed to delete resume: " + err.message, "error");
  }
}

async function handleLinksSave(e) {
  e.preventDefault();
  const saveBtn = document.getElementById("save-links-btn");
  saveBtn.disabled = true;

  const linkedin_link = (document.getElementById("link-linkedin").value || "").trim();
  const github_link = (document.getElementById("link-github").value || "").trim();
  const portfolio_link = (document.getElementById("link-portfolio").value || "").trim();

  // Validate URLs
  if (linkedin_link && !linkedin_link.startsWith("https://www.linkedin.com/") && !linkedin_link.startsWith("https://linkedin.com/")) {
    UI.toast("LinkedIn URL must start with https://www.linkedin.com/ or https://linkedin.com/", "error");
    saveBtn.disabled = false;
    return;
  }

  if (github_link && !github_link.startsWith("https://github.com/")) {
    UI.toast("GitHub URL must start with https://github.com/", "error");
    saveBtn.disabled = false;
    return;
  }

  try {
    // Send update to profile
    await API.put("/api/profile", {
      course: currentProfile.course || "",
      specialization: currentProfile.specialization || "",
      semester: currentProfile.semester || "",
      college: currentProfile.college || "",
      career_goal: currentProfile.career_goal || "",
      interests: currentProfile.interests || "",
      resume_status: currentProfile.resume_status || "none",
      selected_role_id: currentProfile.selected_role_id || "",
      linkedin_link,
      github_link,
      portfolio_link
    });

    UI.toast("Application profile links saved successfully!", "success");

    // Refresh profile
    const profRes = await API.get("/api/profile");
    currentProfile = profRes.data.profile || {};
    UI.renderStepBar(6, currentProfile);
    populateProfileData();
  } catch (err) {
    UI.toast("Failed to save links: " + err.message, "error");
  } finally {
    saveBtn.disabled = false;
  }
}

function testUrl(inputElementId, defaultDomain) {
  const input = document.getElementById(inputElementId);
  const url = (input.value || "").trim();
  if (!url) {
    UI.toast("Please enter a URL first to test.", "warning");
    return;
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    UI.toast("URL must start with https://", "warning");
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

document.addEventListener("DOMContentLoaded", () => {
  initApplicationProfile();

  const uploadForm = document.getElementById("resume-upload-form");
  if (uploadForm) uploadForm.addEventListener("submit", handleResumeUpload);

  const linksForm = document.getElementById("links-form");
  if (linksForm) linksForm.addEventListener("submit", handleLinksSave);

  const testLinkedinBtn = document.getElementById("test-linkedin-btn");
  if (testLinkedinBtn) {
    testLinkedinBtn.addEventListener("click", () => testUrl("link-linkedin", "linkedin.com"));
  }

  const testGithubBtn = document.getElementById("test-github-btn");
  if (testGithubBtn) {
    testGithubBtn.addEventListener("click", () => testUrl("link-github", "github.com"));
  }
});
