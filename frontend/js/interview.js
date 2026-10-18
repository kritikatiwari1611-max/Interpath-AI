// Interview preparation and AI Mock Interview client logic
// Strictly uses textContent to prevent XSS vulnerabilities from AI or user inputs

let currentQuestions = [];
let mockState = {
  active: false,
  sessionId: null,
  mode: "demo",
  badge: "Demo mode (rule-based)",
  questions: [],
  currentIndex: 0,
  answers: [],
  roleId: "python-developer",
  weakTopics: [],
  isRetrying: false,
  previousAnswerScore: null
};

// -------------------------------------------------------------
// 1. INITIALIZATION & SETUP
// -------------------------------------------------------------

async function initInterviewPage() {
  loadQuestionBank();
  loadInterviewStats();
  await loadStudentRole();

  // Bind event listeners
  document.getElementById("bank-role-filter").addEventListener("change", loadQuestionBank);
  document.getElementById("bank-cat-filter").addEventListener("change", loadQuestionBank);

  document.getElementById("start-mock-btn").addEventListener("click", startMockInterview);
  document.getElementById("mock-submit-btn").addEventListener("click", submitMockAnswer);
  document.getElementById("mock-skip-btn").addEventListener("click", skipMockQuestion);
  document.getElementById("mock-next-btn").addEventListener("click", nextMockQuestion);
  document.getElementById("mock-retry-btn").addEventListener("click", resetMockView);
  document.getElementById("mock-practice-weak-btn").addEventListener("click", practiceWeakTopics);

  // Accordion & comparison toggles
  document.getElementById("eval-better-ans-toggle").addEventListener("click", toggleModelAnswerAccordion);
  document.getElementById("eval-compare-toggle").addEventListener("click", toggleComparisonView);
  document.getElementById("eval-try-again-btn").addEventListener("click", prepareRetryAnswer);
}

async function loadStudentRole() {
  try {
    const res = await API.get("/api/roles/selected");
    if (res && res.data && res.data.role_id) {
      const roleSelect = document.getElementById("mock-role");
      const bankSelect = document.getElementById("bank-role-filter");
      if (roleSelect) roleSelect.value = res.data.role_id;
      if (bankSelect) bankSelect.value = res.data.role_id;
    }
  } catch (err) {
    // If no role selected yet, keep default role
    console.log("No preselected role:", err.message);
  }
}

// -------------------------------------------------------------
// 2. QUESTION BANK BROWSER
// -------------------------------------------------------------

async function loadQuestionBank() {
  const container = document.getElementById("qbank-container");
  UI.showLoading(container, "Loading question bank...");

  const role = document.getElementById("bank-role-filter").value;
  const category = document.getElementById("bank-cat-filter").value;

  try {
    const res = await API.get(`/api/interview/questions?role=${role}&category=${category}`);
    currentQuestions = res.data || [];
    renderQuestionBank();
  } catch (err) {
    UI.toast("Failed to load questions: " + err.message, "error");
  }
}

function renderQuestionBank() {
  const container = document.getElementById("qbank-container");
  container.innerHTML = "";

  if (currentQuestions.length === 0) {
    UI.showEmpty(container, "No questions matched your filter.");
    return;
  }

  currentQuestions.forEach((q, idx) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "14px";

    // Top metadata badges
    const topBar = document.createElement("div");
    topBar.style.display = "flex";
    topBar.style.justifyContent = "space-between";
    topBar.style.alignItems = "center";
    topBar.style.marginBottom = "8px";

    const badgeGroup = document.createElement("div");
    badgeGroup.style.display = "flex";
    badgeGroup.style.gap = "8px";

    const bCat = document.createElement("span");
    bCat.className = "badge badge-tech";
    bCat.textContent = q.category || "General";

    const bDiff = document.createElement("span");
    bDiff.className = "badge badge-bonus";
    bDiff.textContent = q.difficulty || "Basic";

    const bTopic = document.createElement("span");
    bTopic.className = "badge badge-important";
    bTopic.textContent = q.topic || "Core";

    badgeGroup.appendChild(bCat);
    badgeGroup.appendChild(bDiff);
    badgeGroup.appendChild(bTopic);

    const bType = document.createElement("span");
    bType.style.fontSize = "0.75rem";
    bType.style.color = "#94a3b8";
    bType.textContent = `Format: ${(q.type || "written").toUpperCase()}`;

    topBar.appendChild(badgeGroup);
    topBar.appendChild(bType);
    card.appendChild(topBar);

    // Question title
    const qTitle = document.createElement("h3");
    qTitle.style.fontSize = "1rem";
    qTitle.style.fontWeight = "600";
    qTitle.style.marginBottom = "10px";
    qTitle.textContent = `${idx + 1}. ${q.question}`;
    card.appendChild(qTitle);

    // Options if MCQ
    if (q.type === "mcq" && Array.isArray(q.options)) {
      const optsBox = document.createElement("div");
      optsBox.style.marginBottom = "12px";
      optsBox.style.display = "flex";
      optsBox.style.flexDirection = "column";
      optsBox.style.gap = "4px";

      q.options.forEach(opt => {
        const row = document.createElement("div");
        row.style.padding = "4px 8px";
        row.style.background = "#f8fafc";
        row.style.borderRadius = "4px";
        row.style.fontSize = "0.85rem";
        row.textContent = `• ${opt}`;
        optsBox.appendChild(row);
      });
      card.appendChild(optsBox);
    }

    // Solution toggle section
    const solWrapper = document.createElement("div");
    solWrapper.style.marginTop = "10px";

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "btn btn-secondary";
    toggleBtn.style.padding = "5px 12px";
    toggleBtn.style.fontSize = "0.78rem";
    toggleBtn.textContent = "Show / Hide Solution";

    const solContent = document.createElement("div");
    solContent.style.display = "none";
    solContent.style.marginTop = "10px";
    solContent.style.padding = "12px";
    solContent.style.background = "#f0fdf4";
    solContent.style.borderRadius = "8px";
    solContent.style.border = "1px solid #bbf7d0";
    solContent.style.fontSize = "0.85rem";

    const solTitle = document.createElement("p");
    solTitle.style.fontWeight = "600";
    solTitle.style.color = "#166534";
    solTitle.style.marginBottom = "4px";
    solTitle.textContent = "Sample Answer / Explanation:";

    const solText = document.createElement("p");
    solText.style.color = "#15803d";
    solText.style.lineHeight = "1.5";
    solText.textContent = q.sampleAnswer || q.explanation || "No solution provided.";

    solContent.appendChild(solTitle);
    solContent.appendChild(solText);

    if (q.keywords && q.keywords.length > 0) {
      const kwBox = document.createElement("div");
      kwBox.style.marginTop = "8px";
      kwBox.style.fontSize = "0.75rem";
      kwBox.style.color = "#166534";
      kwBox.textContent = `Key Concepts: ${q.keywords.join(", ")}`;
      solContent.appendChild(kwBox);
    }

    toggleBtn.addEventListener("click", () => {
      solContent.style.display = solContent.style.display === "none" ? "block" : "none";
    });

    solWrapper.appendChild(toggleBtn);
    solWrapper.appendChild(solContent);
    card.appendChild(solWrapper);

    container.appendChild(card);
  });
}

// -------------------------------------------------------------
// 3. MOCK INTERVIEW ARENA FLOW
// -------------------------------------------------------------

async function startMockInterview() {
  const role = document.getElementById("mock-role").value;
  const category = document.getElementById("mock-category").value;
  const difficulty = document.getElementById("mock-difficulty").value;
  const numQuestions = document.getElementById("mock-num").value;
  const focusMissing = document.getElementById("mock-focus-missing").checked;

  try {
    const res = await API.post("/api/interview/mock/start", {
      role,
      category,
      difficulty,
      num_questions: numQuestions,
      focus_missing_skills: focusMissing
    });

    const data = res.data;
    const questions = data.questions || [];
    if (questions.length === 0) {
      UI.toast("No questions available for the selected criteria.", "warning");
      return;
    }

    mockState = {
      active: true,
      sessionId: data.session_id,
      mode: data.mode,
      badge: data.badge,
      questions: questions,
      currentIndex: 0,
      answers: [],
      roleId: role,
      weakTopics: [],
      isRetrying: false,
      previousAnswerScore: null
    };

    // Update UI headers
    const topBadge = document.getElementById("top-mode-badge");
    if (topBadge) topBadge.textContent = data.badge;

    const mockModeBadge = document.getElementById("mock-mode-badge");
    if (mockModeBadge) mockModeBadge.textContent = data.badge;

    document.getElementById("mock-setup-card").style.display = "none";
    document.getElementById("mock-active-card").style.display = "block";
    document.getElementById("mock-results-card").style.display = "none";

    renderMockQuestion();
  } catch (err) {
    UI.toast("Failed to initialize mock: " + err.message, "error");
  }
}

function renderMockQuestion() {
  const q = mockState.questions[mockState.currentIndex];
  const total = mockState.questions.length;
  const current = mockState.currentIndex + 1;

  mockState.isRetrying = false;
  mockState.previousAnswerScore = null;

  document.getElementById("mock-progress-badge").textContent = `Question ${current} of ${total}`;
  document.getElementById("mock-question-title").textContent = q.question;
  document.getElementById("mock-question-meta").textContent = `${q.category || "General"} • ${q.topic || "Core"} • ${q.difficulty || "Basic"}`;
  document.getElementById("mock-mode-badge").textContent = mockState.badge;

  const answerContainer = document.getElementById("mock-answer-area");
  answerContainer.innerHTML = "";

  const charCounterWrap = document.getElementById("mock-char-counter-wrap");
  const charCounter = document.getElementById("mock-char-counter");

  if (q.type === "mcq") {
    charCounterWrap.style.display = "none";
    const optsBox = document.createElement("div");
    optsBox.style.display = "flex";
    optsBox.style.flexDirection = "column";
    optsBox.style.gap = "8px";

    (q.options || []).forEach(opt => {
      const lbl = document.createElement("label");
      lbl.style.padding = "10px 14px";
      lbl.style.background = "#f8fafc";
      lbl.style.border = "1px solid #e2e8f0";
      lbl.style.borderRadius = "8px";
      lbl.style.cursor = "pointer";
      lbl.style.display = "flex";
      lbl.style.alignItems = "center";
      lbl.style.gap = "10px";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "mock-mcq-opt";
      radio.value = opt;

      const span = document.createElement("span");
      span.textContent = opt;

      lbl.appendChild(radio);
      lbl.appendChild(span);
      optsBox.appendChild(lbl);
    });

    answerContainer.appendChild(optsBox);
  } else {
    charCounterWrap.style.display = "flex";
    charCounter.textContent = "0 / 1500 characters";

    const textarea = document.createElement("textarea");
    textarea.id = "mock-written-input";
    textarea.className = "form-control";
    textarea.rows = 5;
    textarea.maxLength = 1500;
    textarea.placeholder = "Type your structured explanation here (Include practical concepts and a code/process example)...";

    textarea.addEventListener("input", () => {
      charCounter.textContent = `${textarea.value.length} / 1500 characters`;
    });

    answerContainer.appendChild(textarea);
  }

  // Reset visibility states
  document.getElementById("mock-loading-indicator").style.display = "none";
  document.getElementById("mock-evaluation-card").style.display = "none";
  document.getElementById("mock-action-btns").style.display = "flex";
  
  const submitBtn = document.getElementById("mock-submit-btn");
  submitBtn.disabled = false;
  submitBtn.textContent = "Submit Answer";
  
  document.getElementById("mock-skip-btn").disabled = false;
}

// -------------------------------------------------------------
// 4. SUBMIT & EVALUATE ANSWER
// -------------------------------------------------------------

async function submitMockAnswer() {
  const q = mockState.questions[mockState.currentIndex];
  let answerVal = "";

  if (q.type === "mcq") {
    const selected = document.querySelector('input[name="mock-mcq-opt"]:checked');
    if (!selected) {
      UI.toast("Please select an option before submitting.", "warning");
      return;
    }
    answerVal = selected.value;
  } else {
    const textEl = document.getElementById("mock-written-input");
    answerVal = textEl ? textEl.value.trim() : "";
    if (!answerVal) {
      UI.toast("Please type your answer before submitting, or click Skip.", "warning");
      return;
    }
  }

  // Display loading indicator
  const loadingInd = document.getElementById("mock-loading-indicator");
  loadingInd.style.display = "flex";
  document.getElementById("mock-action-btns").style.display = "none";

  try {
    const res = await API.post("/api/interview/mock/answer", {
      session_id: mockState.sessionId,
      question_id: q.id,
      answer: answerVal,
      is_retry: mockState.isRetrying
    });

    const feedback = res.data;
    loadingInd.style.display = "none";

    renderEvaluationCard(feedback, answerVal);
  } catch (err) {
    loadingInd.style.display = "none";
    document.getElementById("mock-action-btns").style.display = "flex";
    UI.toast("Evaluation failed: " + err.message, "error");
  }
}

function skipMockQuestion() {
  const confirmSkip = confirm("Are you sure you want to skip this question? It will be recorded as 0 points.");
  if (!confirmSkip) return;

  const q = mockState.questions[mockState.currentIndex];
  API.post("/api/interview/mock/answer", {
    session_id: mockState.sessionId,
    question_id: q.id,
    answer: "[Skipped by candidate]",
    is_retry: false
  }).finally(() => {
    nextMockQuestion();
  });
}

function renderEvaluationCard(fb, studentAnswer) {
  const card = document.getElementById("mock-evaluation-card");
  card.style.display = "block";

  // Score number and verdict
  const scoreNum = document.getElementById("eval-score-num");
  scoreNum.textContent = fb.score;

  const verdict = document.getElementById("eval-verdict-badge");
  if (fb.score >= 75) {
    verdict.textContent = "Strong Concept";
    verdict.className = "badge badge-success";
  } else if (fb.score >= 50) {
    verdict.textContent = "Room for Growth";
    verdict.className = "badge badge-warning";
  } else {
    verdict.textContent = "Needs Revision";
    verdict.className = "badge badge-danger";
  }

  document.getElementById("eval-badge-label").textContent = fb.badge || "Evaluation";
  document.getElementById("eval-confidence-text").textContent = fb.confidence_note || "";

  // 4 Rubric bars
  const sc = fb.scores || { relevance: 0, completeness: 0, clarity: 0, example_or_evidence: 0 };
  updateRubricBar("relevance", sc.relevance || 0);
  updateRubricBar("completeness", sc.completeness || 0);
  updateRubricBar("clarity", sc.clarity || 0);
  updateRubricBar("example", sc.example_or_evidence || 0);

  // 3 Colored lists (Safely injected via textContent)
  populateList("eval-good-list", fb.what_was_good, "No specific highlights identified.");
  populateList("eval-missing-list", fb.what_was_missing, "No major concepts missing.");
  populateList("eval-tips-list", fb.improvement_tips, "Review standard interview answers.");

  // Model answer accordion content
  const modelTextEl = document.getElementById("eval-better-ans-text");
  modelTextEl.textContent = fb.better_answer || "Review official documentation.";
  document.getElementById("eval-better-ans-content").style.display = "none";
  document.getElementById("eval-better-ans-icon").textContent = "▼";

  // Side-by-Side comparison contents
  document.getElementById("compare-user-text").textContent = studentAnswer;
  document.getElementById("compare-model-text").textContent = fb.better_answer || "";
  document.getElementById("eval-compare-view").style.display = "none";

  // Follow-up question if provided by AI
  const followupBox = document.getElementById("eval-followup-box");
  if (fb.follow_up_question && fb.follow_up_question.trim()) {
    followupBox.style.display = "block";
    document.getElementById("eval-followup-text").textContent = fb.follow_up_question;
  } else {
    followupBox.style.display = "none";
  }

  // Store for potential retry comparison
  mockState.lastEvaluatedFeedback = fb;
  mockState.lastStudentAnswer = studentAnswer;
  if (!mockState.isRetrying) {
    mockState.previousAnswerScore = fb.score;
  } else if (mockState.previousAnswerScore !== null) {
    const diff = fb.score - mockState.previousAnswerScore;
    const diffSign = diff >= 0 ? `+${diff}` : `${diff}`;
    UI.toast(`Score updated from ${mockState.previousAnswerScore} to ${fb.score} (${diffSign})!`, diff >= 0 ? "success" : "info");
  }
}

function updateRubricBar(key, val) {
  const label = document.getElementById(`bar-val-${key}`);
  const fill = document.getElementById(`bar-fill-${key}`);
  if (label) label.textContent = `${Number(val).toFixed(1)} / 5`;
  if (fill) {
    const pct = Math.min(100, Math.max(0, (val / 5.0) * 100));
    fill.style.width = `${pct}%`;
  }
}

function populateList(elementId, items, emptyFallback) {
  const ul = document.getElementById(elementId);
  ul.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = emptyFallback;
    ul.appendChild(li);
    return;
  }
  items.forEach(text => {
    const li = document.createElement("li");
    li.textContent = text;
    ul.appendChild(li);
  });
}

function toggleModelAnswerAccordion() {
  const content = document.getElementById("eval-better-ans-content");
  const icon = document.getElementById("eval-better-ans-icon");
  if (content.style.display === "none") {
    content.style.display = "block";
    icon.textContent = "▲";
  } else {
    content.style.display = "none";
    icon.textContent = "▼";
  }
}

function toggleComparisonView() {
  const view = document.getElementById("eval-compare-view");
  view.style.display = view.style.display === "none" ? "grid" : "none";
}

function prepareRetryAnswer() {
  const q = mockState.questions[mockState.currentIndex];
  if (q.type === "mcq") {
    UI.toast("Multiple-choice questions cannot be retried.", "info");
    return;
  }

  mockState.isRetrying = true;
  document.getElementById("mock-evaluation-card").style.display = "none";
  document.getElementById("mock-action-btns").style.display = "flex";

  const submitBtn = document.getElementById("mock-submit-btn");
  submitBtn.textContent = "Submit Improved Answer";

  const textEl = document.getElementById("mock-written-input");
  if (textEl && mockState.lastStudentAnswer) {
    textEl.value = mockState.lastStudentAnswer;
    textEl.focus();
  }
}

// -------------------------------------------------------------
// 5. FINISH & RESULTS VIEW
// -------------------------------------------------------------

function nextMockQuestion() {
  mockState.currentIndex += 1;
  if (mockState.currentIndex < mockState.questions.length) {
    renderMockQuestion();
  } else {
    finishMockInterview();
  }
}

async function finishMockInterview() {
  const loadingInd = document.getElementById("mock-loading-indicator");
  loadingInd.style.display = "flex";
  document.getElementById("mock-loading-text").textContent = "Calculating final performance analysis...";

  try {
    const res = await API.post("/api/interview/mock/finish", {
      session_id: mockState.sessionId
    });

    loadingInd.style.display = "none";
    const data = res.data;

    document.getElementById("mock-active-card").style.display = "none";
    const resCard = document.getElementById("mock-results-card");
    resCard.style.display = "block";

    // Overall score & accuracy
    document.getElementById("res-score").textContent = `${data.score}%`;
    document.getElementById("res-accuracy").textContent = `Accuracy: ${data.accuracy}% • ${data.badge || "Mock Interview"}`;

    // Criteria breakdown averages
    const avg = data.criterion_averages || {};
    document.getElementById("res-avg-relevance").textContent = `${avg.relevance || 0} / 5`;
    document.getElementById("res-avg-completeness").textContent = `${avg.completeness || 0} / 5`;
    document.getElementById("res-avg-clarity").textContent = `${avg.clarity || 0} / 5`;
    document.getElementById("res-avg-example").textContent = `${avg.example_or_evidence || 0} / 5`;

    // Strong topics list
    const strongList = document.getElementById("res-strong-topics");
    strongList.innerHTML = "";
    if (data.strong_topics && data.strong_topics.length > 0) {
      data.strong_topics.forEach(t => {
        const li = document.createElement("li");
        li.textContent = t;
        strongList.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "Keep practicing to build topic strengths.";
      strongList.appendChild(li);
    }

    // Weak topics list
    const weakList = document.getElementById("res-weak-topics");
    weakList.innerHTML = "";
    mockState.weakTopics = data.weak_topics || [];
    const practiceWeakBtn = document.getElementById("mock-practice-weak-btn");

    if (mockState.weakTopics.length > 0) {
      mockState.weakTopics.forEach(t => {
        const li = document.createElement("li");
        li.textContent = t;
        weakList.appendChild(li);
      });
      practiceWeakBtn.style.display = "inline-flex";
    } else {
      const li = document.createElement("li");
      li.textContent = "Great mastery! No severe topic gaps detected.";
      weakList.appendChild(li);
      practiceWeakBtn.style.display = "none";
    }

    // Detailed per-question review list
    renderPerQuestionReview(data.review || []);

    loadInterviewStats();
  } catch (err) {
    loadingInd.style.display = "none";
    UI.toast("Failed to finalize results: " + err.message, "error");
  }
}

function renderPerQuestionReview(reviewItems) {
  const container = document.getElementById("res-review-container");
  container.innerHTML = "";

  if (reviewItems.length === 0) {
    container.innerHTML = "<p style='color:#64748b;'>No question details available.</p>";
    return;
  }

  reviewItems.forEach((item, idx) => {
    const card = document.createElement("div");
    card.style.background = "#ffffff";
    card.style.border = "1px solid #e2e8f0";
    card.style.borderRadius = "8px";
    card.style.padding = "14px";
    card.style.marginBottom = "10px";

    const topRow = document.createElement("div");
    topRow.style.display = "flex";
    topRow.style.justifyContent = "space-between";
    topRow.style.marginBottom = "6px";

    const topicBadge = document.createElement("span");
    topicBadge.className = "badge badge-tech";
    topicBadge.textContent = item.topic || "Topic";

    const scoreBadge = document.createElement("span");
    scoreBadge.style.fontWeight = "700";
    scoreBadge.style.color = item.score >= 70 ? "#166534" : (item.score >= 50 ? "#92400e" : "#991b1b");
    scoreBadge.textContent = `Score: ${item.score}/100`;

    topRow.appendChild(topicBadge);
    topRow.appendChild(scoreBadge);
    card.appendChild(topRow);

    const qText = document.createElement("div");
    qText.style.fontWeight = "600";
    qText.style.fontSize = "0.9rem";
    qText.style.marginBottom = "8px";
    qText.textContent = `Q${idx + 1}: ${item.question}`;
    card.appendChild(qText);

    const ansText = document.createElement("div");
    ansText.style.fontSize = "0.82rem";
    ansText.style.color = "#475569";
    ansText.style.marginBottom = "8px";
    ansText.textContent = `Your Answer: "${item.student_answer}"`;
    card.appendChild(ansText);

    if (item.better_answer) {
      const betterBox = document.createElement("div");
      betterBox.style.fontSize = "0.8rem";
      betterBox.style.color = "#15803d";
      betterBox.style.background = "#f0fdf4";
      betterBox.style.padding = "8px";
      betterBox.style.borderRadius = "6px";
      betterBox.textContent = `Model Answer: ${item.better_answer}`;
      card.appendChild(betterBox);
    }

    container.appendChild(card);
  });
}

async function practiceWeakTopics() {
  if (mockState.weakTopics.length === 0) return;

  try {
    const res = await API.post("/api/interview/mock/start", {
      role: mockState.roleId,
      category: "all",
      difficulty: "all",
      num_questions: 3,
      weak_topics_only: true,
      weak_topics: mockState.weakTopics
    });

    const data = res.data;
    const questions = data.questions || [];
    if (questions.length === 0) {
      UI.toast("No specific questions found for weak topics.", "info");
      return;
    }

    mockState = {
      active: true,
      sessionId: data.session_id,
      mode: data.mode,
      badge: data.badge,
      questions: questions,
      currentIndex: 0,
      answers: [],
      roleId: mockState.roleId,
      weakTopics: [],
      isRetrying: false,
      previousAnswerScore: null
    };

    document.getElementById("mock-setup-card").style.display = "none";
    document.getElementById("mock-active-card").style.display = "block";
    document.getElementById("mock-results-card").style.display = "none";

    renderMockQuestion();
  } catch (err) {
    UI.toast("Failed to start weak topics drill: " + err.message, "error");
  }
}

function resetMockView() {
  document.getElementById("mock-setup-card").style.display = "block";
  document.getElementById("mock-active-card").style.display = "none";
  document.getElementById("mock-results-card").style.display = "none";
}

// -------------------------------------------------------------
// 6. OVERALL STATS
// -------------------------------------------------------------

async function loadInterviewStats() {
  try {
    const res = await API.get("/api/interview/stats");
    const st = res.data;

    document.getElementById("stat-total-attempts").textContent = st.total_attempts;
    document.getElementById("stat-accuracy").textContent = `${st.accuracy}%`;
    document.getElementById("stat-mocks-done").textContent = st.mock_interviews_done;
  } catch (err) {
    console.error("Stats load err:", err);
  }
}

document.addEventListener("DOMContentLoaded", initInterviewPage);
