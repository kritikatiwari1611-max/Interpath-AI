// Interview preparation and interactive Mock Interview client logic

let currentQuestions = [];
let mockState = {
  active: false,
  questions: [],
  currentIndex: 0,
  answers: [],
  roleId: "python-developer",
  score: 0,
  weakTopics: []
};

// 1. QUESTION BANK TAB
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

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="display: flex; gap: 8px;">
          <span class="badge badge-tech">${q.category}</span>
          <span class="badge badge-bonus">${q.difficulty}</span>
          <span class="badge badge-important">${q.topic}</span>
        </div>
        <span style="font-size: 0.75rem; color: #94a3b8;">Format: ${q.type.toUpperCase()}</span>
      </div>

      <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 10px;">${idx + 1}. ${q.question}</h3>

      ${q.type === 'mcq' ? `
        <div style="margin-bottom: 12px; font-size: 0.88rem; display: flex; flex-direction: column; gap: 4px;">
          ${q.options.map(opt => `<div style="padding: 4px 8px; background: #f8fafc; border-radius: 4px;">• ${opt}</div>`).join("")}
        </div>
      ` : ''}

      <div style="margin-top: 10px;">
        <button class="btn btn-secondary" style="padding: 5px 12px; font-size: 0.78rem;" onclick="toggleAnswer('ans-${q.id}')">
          Show / Hide Solution
        </button>
        <div id="ans-${q.id}" style="display: none; margin-top: 10px; padding: 12px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0; font-size: 0.85rem;">
          <p style="font-weight: 600; color: #166534; margin-bottom: 4px;">Sample Answer / Explanation:</p>
          <p style="color: #15803d; line-height: 1.5;">${q.sampleAnswer || q.explanation}</p>
          ${q.keywords && q.keywords.length > 0 ? `
            <div style="margin-top: 8px; font-size: 0.75rem; color: #166534;">
              <strong>Key Evaluation Concepts:</strong> ${q.keywords.join(", ")}
            </div>
          ` : ''}
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function toggleAnswer(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === "none" ? "block" : "none";
}

// 2. MOCK INTERVIEW SIMULATION
async function startMockInterview() {
  const role = document.getElementById("mock-role").value;
  const category = document.getElementById("mock-category").value;
  const difficulty = document.getElementById("mock-difficulty").value;
  const numQuestions = document.getElementById("mock-num").value;

  try {
    const res = await API.post("/api/interview/mock/start", {
      role,
      category,
      difficulty,
      num_questions: numQuestions
    });

    const questions = res.data.questions || [];
    if (questions.length === 0) {
      UI.toast("No questions available for selected criteria.", "warning");
      return;
    }

    mockState = {
      active: true,
      questions,
      currentIndex: 0,
      answers: [],
      roleId: role,
      score: 0,
      weakTopics: []
    };

    document.getElementById("mock-setup-card").style.display = "none";
    document.getElementById("mock-active-card").style.display = "block";
    document.getElementById("mock-results-card").style.display = "none";

    renderMockQuestion();
  } catch (err) {
    UI.toast("Failed to start mock: " + err.message, "error");
  }
}

function renderMockQuestion() {
  const q = mockState.questions[mockState.currentIndex];
  const total = mockState.questions.length;
  const current = mockState.currentIndex + 1;

  document.getElementById("mock-progress-badge").textContent = `Question ${current} of ${total}`;
  document.getElementById("mock-question-title").textContent = q.question;
  document.getElementById("mock-question-meta").textContent = `Domain: ${q.category} • Topic: ${q.topic} • Difficulty: ${q.difficulty}`;

  const answerContainer = document.getElementById("mock-answer-area");
  answerContainer.innerHTML = "";

  if (q.type === "mcq") {
    answerContainer.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${q.options.map((opt, i) => `
          <label style="padding: 10px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
            <input type="radio" name="mock-mcq-opt" value="${opt}">
            <span>${opt}</span>
          </label>
        `).join("")}
      </div>
    `;
  } else {
    answerContainer.innerHTML = `
      <textarea id="mock-written-input" class="form-control" rows="5" placeholder="Type your structured explanation here (Include practical concepts and a code/process example)..."></textarea>
    `;
  }

  document.getElementById("mock-feedback-box").style.display = "none";
  document.getElementById("mock-submit-btn").style.display = "inline-flex";
  document.getElementById("mock-next-btn").style.display = "none";
}

async function submitMockAnswer() {
  const q = mockState.questions[mockState.currentIndex];
  let answerVal = "";

  if (q.type === "mcq") {
    const selected = document.querySelector('input[name="mock-mcq-opt"]:checked');
    if (!selected) {
      UI.toast("Please select an option.", "warning");
      return;
    }
    answerVal = selected.value;
  } else {
    const textEl = document.getElementById("mock-written-input");
    answerVal = textEl ? textEl.value.trim() : "";
    if (!answerVal) {
      UI.toast("Please type your response before submitting.", "warning");
      return;
    }
  }

  const submitBtn = document.getElementById("mock-submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Evaluating...";

  try {
    const res = await API.post("/api/interview/mock/answer", {
      question_id: q.id,
      answer: answerVal,
      role_id: mockState.roleId
    });

    const feedback = res.data;
    mockState.answers.push(feedback);

    if (!feedback.is_correct) {
      if (!mockState.weakTopics.includes(q.topic)) {
        mockState.weakTopics.push(q.topic);
      }
    }

    // Display inline feedback
    const fbBox = document.getElementById("mock-feedback-box");
    fbBox.style.display = "block";
    fbBox.style.backgroundColor = feedback.is_correct ? "#f0fdf4" : "#fffbeb";
    fbBox.style.border = feedback.is_correct ? "1px solid #bbf7d0" : "1px solid #fde68a";
    
    document.getElementById("mock-fb-title").textContent = feedback.is_correct ? "Evaluation: Accepted / Solid Concept" : "Evaluation: Room for Growth";
    document.getElementById("mock-fb-title").style.color = feedback.is_correct ? "#166534" : "#92400e";
    document.getElementById("mock-fb-text").textContent = feedback.feedback;
    document.getElementById("mock-fb-label").textContent = feedback.eval_label;

    submitBtn.style.display = "none";
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Answer";
    document.getElementById("mock-next-btn").style.display = "inline-flex";
  } catch (err) {
    UI.toast("Evaluation failed: " + err.message, "error");
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Answer";
  }
}

function nextMockQuestion() {
  mockState.currentIndex += 1;
  if (mockState.currentIndex < mockState.questions.length) {
    renderMockQuestion();
  } else {
    finishMockInterview();
  }
}

async function finishMockInterview() {
  const total = mockState.answers.length;
  const correct = mockState.answers.filter(a => a.is_correct).length;
  const accuracy = roundToDec((correct / total) * 100, 1);
  const score = Math.round(accuracy);

  try {
    await API.post("/api/interview/mock/finish", {
      role_id: mockState.roleId,
      score,
      accuracy,
      weak_topics: mockState.weakTopics
    });

    document.getElementById("mock-active-card").style.display = "none";
    const resCard = document.getElementById("mock-results-card");
    resCard.style.display = "block";

    document.getElementById("res-score").textContent = `${score}%`;
    document.getElementById("res-accuracy").textContent = `${correct} / ${total} Correct (${accuracy}%)`;
    
    const weakListEl = document.getElementById("res-weak-topics");
    weakListEl.innerHTML = "";
    if (mockState.weakTopics.length > 0) {
      mockState.weakTopics.forEach(top => {
        const li = document.createElement("li");
        li.textContent = top;
        weakListEl.appendChild(li);
      });
    } else {
      weakListEl.innerHTML = "<p style='color:#166534;'>Great performance! No significant weak topics detected.</p>";
    }

    loadInterviewStats();
  } catch (err) {
    UI.toast("Failed to record mock results: " + err.message, "error");
  }
}

function resetMockView() {
  document.getElementById("mock-setup-card").style.display = "block";
  document.getElementById("mock-active-card").style.display = "none";
  document.getElementById("mock-results-card").style.display = "none";
}

// 3. STATS TAB
async function loadInterviewStats() {
  try {
    const res = await API.get("/api/interview/stats");
    const st = res.data;

    document.getElementById("stat-total-attempts").textContent = st.total_attempts;
    document.getElementById("stat-accuracy").textContent = `${st.accuracy}%`;
    document.getElementById("stat-mocks-done").textContent = st.mock_interviews_done;

    const topicContainer = document.getElementById("stat-topic-summary");
    if (topicContainer) {
      topicContainer.innerHTML = "";
      for (const [top, vals] of Object.entries(st.topic_summary || {})) {
        const acc = vals.total > 0 ? Math.round((vals.correct / vals.total) * 100) : 0;
        const div = document.createElement("div");
        div.style.padding = "8px 12px";
        div.style.background = "#f8fafc";
        div.style.borderRadius = "6px";
        div.style.display = "flex";
        div.style.justifyContent = "space-between";
        div.innerHTML = `<span><strong>${top}</strong></span> <span>${acc}% (${vals.correct}/${vals.total})</span>`;
        topicContainer.appendChild(div);
      }
    }
  } catch (err) {
    console.error("Stats load err:", err);
  }
}

function roundToDec(val, dec) {
  return Number(Math.round(val + 'e' + dec) + 'e-' + dec);
}

document.addEventListener("DOMContentLoaded", () => {
  loadQuestionBank();
  loadInterviewStats();

  document.getElementById("bank-role-filter").addEventListener("change", loadQuestionBank);
  document.getElementById("bank-cat-filter").addEventListener("change", loadQuestionBank);

  document.getElementById("start-mock-btn").addEventListener("click", startMockInterview);
  document.getElementById("mock-submit-btn").addEventListener("click", submitMockAnswer);
  document.getElementById("mock-next-btn").addEventListener("click", nextMockQuestion);
  document.getElementById("mock-retry-btn").addEventListener("click", resetMockView);
});
