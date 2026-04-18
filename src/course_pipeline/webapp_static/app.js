const state = {
  courses: [],
  selectedCourseId: null,
  selectedCourse: null,
  loadingChat: false,
  requestedCourseId: new URLSearchParams(window.location.search).get("course_id"),
  requestedTabId: new URLSearchParams(window.location.search).get("tab"),
};

const elements = {
  loadingState: document.getElementById("loading-state"),
  emptyState: document.getElementById("empty-state"),
  courseView: document.getElementById("course-view"),
  courseSearch: document.getElementById("course-search"),
  courseOptions: document.getElementById("course-options"),
  runBadges: document.getElementById("run-badges"),
  courseTitle: document.getElementById("course-title"),
  courseMetaLine: document.getElementById("course-meta-line"),
  courseStats: document.getElementById("course-stats"),
  subjectChips: document.getElementById("subject-chips"),
  metadataGrid: document.getElementById("metadata-grid"),
  summaryBody: document.getElementById("summary-body"),
  overviewBody: document.getElementById("overview-body"),
  chaptersList: document.getElementById("chapters-list"),
  learningOutcomesList: document.getElementById("learning-outcomes-list"),
  questionCacheList: document.getElementById("question-cache-list"),
  qaPairsList: document.getElementById("qa-pairs-list"),
  rawYaml: document.getElementById("raw-yaml"),
  chatCourseLine: document.getElementById("chat-course-line"),
  chatThread: document.getElementById("chat-thread"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  sendButton: document.getElementById("send-button"),
  tabButtons: Array.from(document.querySelectorAll(".tab-button")),
  tabPanels: Array.from(document.querySelectorAll(".tab-panel")),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderRunBadges(runContext) {
  const badges = [];
  if (runContext.learning_run_id) {
    badges.push(`<span class="badge">learning ${escapeHtml(runContext.learning_run_id)}</span>`);
  }
  if (runContext.question_cache_run_id) {
    badges.push(`<span class="badge">cache ${escapeHtml(runContext.question_cache_run_id)}</span>`);
  }
  elements.runBadges.innerHTML = badges.join("");
}

function selectedCourseOption() {
  if (!state.courses.length) {
    return null;
  }
  if (state.requestedCourseId) {
    const requested = state.courses.find((course) => course.course_id === state.requestedCourseId);
    if (requested) {
      return requested;
    }
  }
  return state.courses[0];
}

function renderCourseOptions() {
  elements.courseOptions.innerHTML = state.courses
    .map((course) => `<option value="${escapeHtml(course.label)}"></option>`)
    .join("");
  if (!state.selectedCourseId) {
    const initial = selectedCourseOption();
    if (initial) {
      state.selectedCourseId = initial.course_id;
      elements.courseSearch.value = initial.label;
    }
  }
}

function courseBySearchValue(value) {
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  return state.courses.find((course) =>
    course.label.toLowerCase() === normalized
    || course.course_id === normalized
    || course.title.toLowerCase() === normalized
  ) || null;
}

function renderMetadata(course) {
  const rows = [
    ["Provider", course.provider],
    ["Course ID", course.course_id],
    ["Level", course.level],
    ["Duration (hours)", course.duration_hours],
    ["Pricing", course.pricing],
    ["Language", course.language],
    ["Source URL", course.source_url ? `<a href="${escapeHtml(course.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(course.source_url)}</a>` : ""],
    ["Final URL", course.final_url ? `<a href="${escapeHtml(course.final_url)}" target="_blank" rel="noreferrer">${escapeHtml(course.final_url)}</a>` : ""],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");

  elements.metadataGrid.innerHTML = rows
    .map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`)
    .join("");
}

function renderChapters(chapters) {
  if (!chapters.length) {
    elements.chaptersList.innerHTML = `<div class="derived-card muted">No chapters recovered.</div>`;
    return;
  }
  elements.chaptersList.innerHTML = chapters
    .map((chapter) => `
      <article class="chapter-card">
        <div class="chapter-kicker">
          <span>Chapter ${escapeHtml(chapter.chapter_index)}</span>
          <span>${escapeHtml(chapter.source)} <span class="confidence">confidence ${escapeHtml(chapter.confidence)}</span></span>
        </div>
        <h3>${escapeHtml(chapter.title)}</h3>
        <p class="muted">${escapeHtml(chapter.summary || "No chapter summary available.")}</p>
      </article>
    `)
    .join("");
}

function renderLearningOutcomes(payload) {
  const outcomes = payload?.learning_outcomes || [];
  if (!outcomes.length) {
    elements.learningOutcomesList.innerHTML = `<div class="derived-card muted">No learning outcomes loaded for this course.</div>`;
    return;
  }
  elements.learningOutcomesList.innerHTML = outcomes
    .map((item) => {
      const citations = (item.citations || [])
        .map((citation) => `<span class="chip">${escapeHtml(citation.field)}</span>`)
        .join("");
      return `
        <article class="derived-card">
          <p class="message-role">${escapeHtml(item.process_level)} / ${escapeHtml(item.knowledge_type)}</p>
          <div class="message-body">${escapeHtml(item.claim)}</div>
          <div class="message-meta">
            <span class="chip">DOK ${escapeHtml(item.dok_level)}</span>
            <span class="chip">SOLO ${escapeHtml(item.solo_level)}</span>
            <span class="chip">confidence ${escapeHtml(item.confidence)}</span>
            ${citations}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderQuestionCache(payload) {
  const groups = payload?.question_groups || [];
  if (!groups.length) {
    elements.questionCacheList.innerHTML = `<div class="derived-card muted">No question-cache groups loaded for this course.</div>`;
    return;
  }
  elements.questionCacheList.innerHTML = groups
    .map((group) => {
      const variations = (group.variations || []).slice(0, 3).map((item) => item.text);
      const answers = (group.answers || []).slice(0, 1).map((item) => item.answer_markdown);
      return `
        <article class="derived-card">
          <p class="message-role">${escapeHtml(group.intent_slug)}</p>
          <div class="message-body">${escapeHtml(group.canonical_question)}</div>
          <div class="message-meta">
            <span class="chip">${escapeHtml(group.pedagogical_move)}</span>
            <span class="chip">${escapeHtml(group.validator_status)}</span>
            <span class="chip">confidence ${escapeHtml(group.confidence)}</span>
          </div>
          <p class="muted small-copy">Example variations</p>
          <div class="prose-block">${escapeHtml(variations.join("\n") || "No accepted variations exposed.")}</div>
          <p class="muted small-copy">Canonical answer</p>
          <div class="prose-block">${escapeHtml(answers[0] || "No canonical answer available.")}</div>
        </article>
      `;
    })
    .join("");
}

function renderQaPairs(payload) {
  const groups = (payload?.question_groups || []).filter((group) =>
    (group.answers || []).some((answer) => answer.answer_fit_status === "pass" && answer.grounding_status === "pass")
  );
  if (!groups.length) {
    elements.qaPairsList.innerHTML = `<div class="derived-card muted">No runtime-eligible precomputed Q/A pairs are available for this course.</div>`;
    return;
  }
  elements.qaPairsList.innerHTML = groups
    .map((group) => {
      const acceptedVariations = (group.variations || []).filter((variation) => variation.accepted_for_runtime);
      const answer = (group.answers || []).find(
        (item) => item.answer_fit_status === "pass" && item.grounding_status === "pass"
      );
      return `
        <article class="derived-card qa-card">
          <div class="message-meta">
            <span class="badge status-badge hit">runtime pair</span>
            <span class="chip">claim ${escapeHtml(group.claim_id)}</span>
            <span class="chip">group ${escapeHtml(group.question_group_id)}</span>
          </div>
          <div class="qa-block">
            <p class="qa-label">Canonical Question</p>
            <div class="message-body">${escapeHtml(group.canonical_question)}</div>
          </div>
          <div class="qa-block">
            <p class="qa-label">Precomputed Answer</p>
            <div class="message-body">${escapeHtml(answer?.answer_markdown || "No answer available.")}</div>
          </div>
          <div class="qa-block">
            <p class="qa-label">Accepted Variations</p>
            <div class="prose-block">${escapeHtml(
              acceptedVariations.map((item) => item.text).join("\n") || "No accepted variations."
            )}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderCourseDetail(payload) {
  const course = payload.course;
  state.selectedCourse = payload;
  elements.loadingState.classList.add("hidden");
  elements.emptyState.classList.add("hidden");
  elements.courseView.classList.remove("hidden");

  elements.courseTitle.textContent = course.title;
  elements.courseMetaLine.textContent = [course.provider, `course ${course.course_id}`, course.level].filter(Boolean).join(" • ");
  elements.chatCourseLine.textContent = `Current course: ${course.title} (${course.course_id})`;

  const stats = payload.stats || {};
  elements.courseStats.innerHTML = [
    ["chapters", stats.chapter_count],
    ["outcomes", stats.learning_outcome_count],
    ["cache groups", stats.question_group_count],
  ]
    .map(([label, value]) => `<span class="stat-pill">${escapeHtml(label)} ${escapeHtml(value ?? 0)}</span>`)
    .join("");

  elements.subjectChips.innerHTML = (course.subjects || [])
    .map((subject) => `<span class="chip">${escapeHtml(subject)}</span>`)
    .join("");

  renderMetadata(course);
  elements.summaryBody.textContent = course.summary || "No summary available.";
  elements.overviewBody.textContent = course.overview || "No overview available.";
  renderChapters(course.chapters || []);
  renderLearningOutcomes(payload.learning_outcomes);
  renderQuestionCache(payload.question_cache);
  renderQaPairs(payload.question_cache);
  elements.rawYaml.textContent = payload.raw_yaml || "Raw YAML unavailable.";
  if (state.requestedTabId) {
    activateTab(state.requestedTabId);
  }
}

function appendMessage(role, body, meta = []) {
  const card = document.createElement("article");
  card.className = `message-card ${role}`;
  const metaHtml = meta.length ? `<div class="message-meta">${meta.join("")}</div>` : "";
  card.innerHTML = `
    <p class="message-role">${role === "user" ? "You" : "Assistant"}</p>
    <div class="message-body">${escapeHtml(body)}</div>
    ${metaHtml}
  `;
  elements.chatThread.appendChild(card);
  elements.chatThread.scrollTop = elements.chatThread.scrollHeight;
}

function resetChat() {
  elements.chatThread.innerHTML = "";
  if (state.selectedCourseId) {
    appendMessage(
      "assistant",
      "Ask a course-scoped question. I will report cache hit or cache miss before returning the answer."
    );
  }
}

async function loadCourses() {
  const response = await fetch("/api/courses");
  const payload = await response.json();
  state.courses = payload.courses || [];
  renderRunBadges(payload.run_context || {});
  renderCourseOptions();
  if (state.selectedCourseId) {
    await loadCourseDetail(state.selectedCourseId);
  } else {
    elements.loadingState.textContent = "No courses available.";
  }
}

async function loadCourseDetail(courseId) {
  state.selectedCourseId = courseId;
  const course = state.courses.find((item) => item.course_id === courseId);
  if (course) {
    elements.courseSearch.value = course.label;
  }
  const response = await fetch(`/api/courses/${encodeURIComponent(courseId)}`);
  const payload = await response.json();
  renderCourseDetail(payload);
  resetChat();
}

function resolveCourseSearch() {
  const exact = courseBySearchValue(elements.courseSearch.value);
  if (exact) {
    loadCourseDetail(exact.course_id);
    return;
  }
  const query = elements.courseSearch.value.trim().toLowerCase();
  if (!query) {
    return;
  }
  const partial = state.courses.find((course) => course.label.toLowerCase().includes(query));
  if (partial) {
    loadCourseDetail(partial.course_id);
  }
}

function activateTab(targetId) {
  if (!elements.tabPanels.some((panel) => panel.id === targetId)) {
    return;
  }
  elements.tabButtons.forEach((button) => {
    const isActive = button.dataset.tabTarget === targetId;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  elements.tabPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === targetId);
  });
}

async function submitChat(event) {
  event.preventDefault();
  if (state.loadingChat || !state.selectedCourseId) {
    return;
  }
  const question = elements.chatInput.value.trim();
  if (!question) {
    return;
  }

  state.loadingChat = true;
  elements.sendButton.disabled = true;
  appendMessage("user", question);
  elements.chatInput.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: state.selectedCourseId,
        question,
      }),
    });
    const payload = await response.json();
    const statusClass = payload.status === "cache_hit" ? "hit" : "miss";
    const statusLabel = payload.status === "cache_hit" ? "cache hit" : "cache miss";
    const meta = [
      `<span class="badge status-badge ${statusClass}">${statusLabel}</span>`,
      payload.match_method ? `<span class="chip">method ${escapeHtml(payload.match_method)}</span>` : "",
      payload.match_score !== undefined ? `<span class="chip">score ${escapeHtml(payload.match_score)}</span>` : "",
      payload.claim_id ? `<span class="chip">claim ${escapeHtml(payload.claim_id)}</span>` : "",
      payload.question_group_id ? `<span class="chip">group ${escapeHtml(payload.question_group_id)}</span>` : "",
      payload.fallback_reason ? `<span class="chip">reason ${escapeHtml(payload.fallback_reason)}</span>` : "",
    ].filter(Boolean);
    appendMessage("assistant", payload.answer_markdown || "No answer returned.", meta);
  } catch (error) {
    appendMessage("assistant", `Request failed: ${error}`);
  } finally {
    state.loadingChat = false;
    elements.sendButton.disabled = false;
  }
}

elements.courseSearch.addEventListener("change", resolveCourseSearch);
elements.courseSearch.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    resolveCourseSearch();
  }
});
elements.chatForm.addEventListener("submit", submitChat);
elements.tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tabTarget));
});

loadCourses().catch((error) => {
  elements.loadingState.textContent = `Failed to load app: ${error}`;
});
