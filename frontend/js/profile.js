// Profile management logic: load profile, render skills, projects, certifications, and handle updates

let currentProfile = null;
let currentSkills = [];
let currentProjects = [];
let currentCerts = [];

async function loadProfile() {
  const container = document.getElementById("profile-content");
  UI.showLoading(container, "Loading your profile...");

  try {
    const res = await API.get("/api/profile");
    currentProfile = res.data.profile;
    currentSkills = res.data.skills || [];
    currentProjects = res.data.projects || [];
    currentCerts = res.data.certifications || [];

    renderProfileForm();
    renderSkillsList();
    renderProjectsList();
    renderCertsList();
  } catch (err) {
    UI.toast("Failed to load profile: " + err.message, "error");
  }
}

function renderProfileForm() {
  const p = currentProfile;
  document.getElementById("course").value = p.course || "";
  document.getElementById("specialization").value = p.specialization || "";
  document.getElementById("semester").value = p.semester || "";
  document.getElementById("college").value = p.college || "";
  document.getElementById("career_goal").value = p.career_goal || "";
  document.getElementById("interests").value = p.interests || "";
  document.getElementById("github_link").value = p.github_link || "";
  document.getElementById("resume_status").value = p.resume_status || "none";

  // Resume checklist checkboxes
  const cl = p.resume_checklist || {};
  document.getElementById("chk_resume_exists").checked = !!cl.resume_exists;
  document.getElementById("chk_education_listed").checked = !!cl.education_listed;
  document.getElementById("chk_matching_skills_listed").checked = !!cl.matching_skills_listed;
  document.getElementById("chk_relevant_project_included").checked = !!cl.relevant_project_included;
  document.getElementById("chk_experience_volunteering").checked = !!cl.experience_volunteering;
  document.getElementById("chk_contact_portfolio_links").checked = !!cl.contact_portfolio_links;
}

function renderSkillsList() {
  const listEl = document.getElementById("skills-list");
  listEl.innerHTML = "";

  if (currentSkills.length === 0) {
    UI.showEmpty(listEl, "No skills added yet. Add your current skills below.");
    return;
  }

  currentSkills.forEach((s, idx) => {
    const item = document.createElement("div");
    item.style.display = "flex";
    item.style.justifyContent = "space-between";
    item.style.alignItems = "center";
    item.style.padding = "8px 12px";
    item.style.backgroundColor = "#f8fafc";
    item.style.border = "1px solid #e2e8f0";
    item.style.borderRadius = "8px";
    item.style.marginBottom = "8px";

    const left = document.createElement("div");
    left.innerHTML = `<strong>${s.skill_name}</strong> <span class="badge badge-tech" style="margin-left: 8px;">${s.level}</span>`;

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn-secondary";
    delBtn.style.padding = "3px 8px";
    delBtn.style.fontSize = "0.75rem";
    delBtn.textContent = "Remove";
    delBtn.onclick = () => removeSkill(idx);

    item.appendChild(left);
    item.appendChild(delBtn);
    listEl.appendChild(item);
  });
}

function renderProjectsList() {
  const listEl = document.getElementById("projects-list");
  listEl.innerHTML = "";

  if (currentProjects.length === 0) {
    UI.showEmpty(listEl, "No projects recorded yet. Add your college or personal projects.");
    return;
  }

  currentProjects.forEach((p) => {
    const card = document.createElement("div");
    card.style.padding = "12px 14px";
    card.style.border = "1px solid #e2e8f0";
    card.style.borderRadius = "8px";
    card.style.marginBottom = "10px";
    card.style.backgroundColor = "#ffffff";

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4 style="font-size: 0.95rem; margin-bottom: 4px;">${p.title}</h4>
        <span class="badge ${p.status === 'completed' ? 'badge-bonus' : 'badge-important'}">${p.status}</span>
      </div>
      <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 6px;">${p.description || ''}</p>
      <div style="font-size: 0.78rem; color: #2563eb;"><strong>Stack / Tools:</strong> ${p.tech || 'N/A'}</div>
    `;
    listEl.appendChild(card);
  });
}

function renderCertsList() {
  const listEl = document.getElementById("certs-list");
  listEl.innerHTML = "";

  if (currentCerts.length === 0) {
    UI.showEmpty(listEl, "No certifications listed.");
    return;
  }

  currentCerts.forEach((c) => {
    const item = document.createElement("div");
    item.style.padding = "8px 12px";
    item.style.backgroundColor = "#f8fafc";
    item.style.border = "1px solid #e2e8f0";
    item.style.borderRadius = "8px";
    item.style.marginBottom = "6px";
    item.innerHTML = `<strong>${c.title}</strong> <span style="font-size:0.8rem; color:#64748b;">(${c.issuer || 'Online Course'})</span>`;
    listEl.appendChild(item);
  });
}

function removeSkill(index) {
  currentSkills.splice(index, 1);
  renderSkillsList();
}

function addSkillFromInput() {
  const nameInput = document.getElementById("new-skill-name");
  const levelSelect = document.getElementById("new-skill-level");
  const name = nameInput.value.trim();
  const level = levelSelect.value;

  if (!name) {
    UI.toast("Please enter a skill name", "warning");
    return;
  }

  currentSkills.push({ skill_name: name, level });
  nameInput.value = "";
  renderSkillsList();
}

async function saveFullProfile() {
  const saveBtn = document.getElementById("save-profile-btn");
  saveBtn.disabled = true;
  saveBtn.textContent = "Saving...";

  const profilePayload = {
    course: document.getElementById("course").value.trim(),
    specialization: document.getElementById("specialization").value.trim(),
    semester: document.getElementById("semester").value.trim(),
    college: document.getElementById("college").value.trim(),
    career_goal: document.getElementById("career_goal").value.trim(),
    interests: document.getElementById("interests").value.trim(),
    github_link: document.getElementById("github_link").value.trim(),
    resume_status: document.getElementById("resume_status").value,
    selected_role_id: currentProfile ? currentProfile.selected_role_id : "",
    resume_checklist: {
      resume_exists: document.getElementById("chk_resume_exists").checked,
      education_listed: document.getElementById("chk_education_listed").checked,
      matching_skills_listed: document.getElementById("chk_matching_skills_listed").checked,
      relevant_project_included: document.getElementById("chk_relevant_project_included").checked,
      experience_volunteering: document.getElementById("chk_experience_volunteering").checked,
      contact_portfolio_links: document.getElementById("chk_contact_portfolio_links").checked
    }
  };

  try {
    // 1. Save profile details
    await API.put("/api/profile", profilePayload);
    // 2. Save skills list
    await API.put("/api/skills", {
      skills: currentSkills.map(s => ({ name: s.skill_name, level: s.level }))
    });

    UI.toast("Profile saved successfully!", "success");
  } catch (err) {
    UI.toast("Save error: " + err.message, "error");
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save Profile Changes";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  document.getElementById("add-skill-btn").addEventListener("click", addSkillFromInput);
  document.getElementById("save-profile-btn").addEventListener("click", saveFullProfile);
});
