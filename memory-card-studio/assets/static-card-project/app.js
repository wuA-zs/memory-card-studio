const GROUP_SIZE = 5;

const CHEERS = [
  "这一组完成得很稳，继续保持节奏。",
  "很好，记忆正在被重新加固。",
  "这组已经收下，下一组会更轻松。",
  "复习进度很漂亮，短时专注很有价值。"
];

const INTERVALS = [1, 2, 4, 7, 15, 30, 60];

const state = {
  libraries: [],
  activeLibraryId: "",
  reviewState: { version: 1, cards: {} },
  allDueCards: [],
  reviewGroups: [],
  currentGroupIndex: 0,
  reviewCards: [],
  currentReviewIndex: 0,
  answerVisible: false,
  selectedChoice: null,
  groupResults: []
};

const els = {
  librarySelect: document.querySelector("#librarySelect"),
  message: document.querySelector("#message"),
  tabs: document.querySelectorAll(".tab"),
  panels: {
    review: document.querySelector("#reviewPanel"),
    all: document.querySelector("#allPanel")
  },
  groupProgress: document.querySelector("#groupProgress"),
  groupLabel: document.querySelector("#groupLabel"),
  groupDots: document.querySelector("#groupDots"),
  reviewCard: document.querySelector("#reviewCard"),
  reviewCounter: document.querySelector("#reviewCounter"),
  showAnswer: document.querySelector("#showAnswer"),
  prevCard: document.querySelector("#prevCard"),
  nextCard: document.querySelector("#nextCard"),
  reviewButtons: document.querySelectorAll("[data-grade]"),
  celebrationOverlay: document.querySelector("#celebrationOverlay"),
  celebrationTitle: document.querySelector("#celebrationTitle"),
  celebrationStats: document.querySelector("#celebrationStats"),
  continueGroup: document.querySelector("#continueGroup"),
  searchInput: document.querySelector("#searchInput"),
  typeFilter: document.querySelector("#typeFilter"),
  allCards: document.querySelector("#allCards"),
  allCounter: document.querySelector("#allCounter")
};

// 小功能：把文本转义后再写入页面，避免卡片内容里的特殊字符破坏 HTML。
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// 小功能：显示页面提示，用于解释本地文件读取限制或空数据状态。
function showMessage(text) {
  els.message.textContent = text;
  els.message.hidden = !text;
}

// 小功能：从本地脚本快照读取数据，避免 file:// 下 fetch 读取 JSON 被浏览器拦截。
function loadScriptSnapshot() {
  const snapshot = window.MEMORY_CARD_STUDIO_DATA;
  if (!snapshot?.libraries?.length) {
    return false;
  }
  state.libraries = snapshot.libraries;
  state.activeLibraryId = snapshot.libraries[0].id;
  state.reviewState = snapshot.reviewState || { version: 1, cards: {} };
  return true;
}

// 小功能：读取 JSON 文件，并在静态服务器场景下提供兼容加载能力。
async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法读取 ${path}`);
  }
  return response.json();
}

// 小功能：加载卡片数据，优先用本地脚本快照，失败时再尝试静态服务器 JSON。
async function loadData() {
  if (loadScriptSnapshot()) {
    showMessage("");
    return;
  }

  try {
    const library = await fetchJson("data/libraries/default.json");
    state.libraries = [library];
    state.activeLibraryId = library.id;
    state.reviewState = await fetchJson("data/review-state.json");
    showMessage("");
  } catch (error) {
    showMessage("没有找到 data/app-data.js，且浏览器阻止了本地 JSON 读取。请让 Codex 重新生成或修复这个卡片项目。");
    state.libraries = [embeddedFallbackLibrary()];
    state.activeLibraryId = state.libraries[0].id;
  }
}

// 小功能：在 file:// 读取 JSON 失败时提供内置示例，避免页面空白。
function embeddedFallbackLibrary() {
  return {
    id: "default",
    name: "示例卡片库",
    sourceFiles: [],
    cards: [
      {
        id: "sample-qa",
        type: "qa",
        front: "这个前端项目的主要用途是什么？",
        back: "它用于查看本地记忆卡片库，并按今日复习顺序刷卡。",
        source: "内置示例",
        tags: ["示例"],
        createdAt: new Date().toISOString()
      }
    ]
  };
}

// 小功能：获取当前选中的卡片库。
function activeLibrary() {
  return state.libraries.find((library) => library.id === state.activeLibraryId) || state.libraries[0];
}

// 小功能：判断卡片今天是否到期，缺少状态的新卡也视为可复习。
function isDueToday(card) {
  const review = state.reviewState.cards?.[card.id];
  if (!review || !review.nextReviewAt) {
    return true;
  }
  return new Date(review.nextReviewAt) <= new Date();
}

// 小功能：根据复习状态计算遗忘曲线优先级，分数越高越应该先复习。
function forgettingCurvePriority(card) {
  const review = state.reviewState.cards?.[card.id];
  if (!review) {
    return 1000;
  }

  const now = new Date();
  const due = review.nextReviewAt ? new Date(review.nextReviewAt) : now;
  const overdueDays = Math.max(0, Math.floor((now - due) / 86400000));
  const intervalDays = Math.max(1, Number(review.intervalDays || 1));
  const reviewCount = Math.max(0, Number(review.reviewCount || 0));
  const overdueFactor = overdueDays * 12;
  const intervalFactor = 80 / intervalDays;
  const reviewCountFactor = Math.max(0, 30 - reviewCount * 4);
  const statusBonus = review.status === "forgotten" ? 60 : 0;

  return overdueFactor + intervalFactor + reviewCountFactor + statusBonus;
}

// 小功能：把数组按固定大小切成多个复习小组。
function chunkCards(cards, size) {
  const groups = [];
  for (let index = 0; index < cards.length; index += size) {
    groups.push(cards.slice(index, index + size));
  }
  return groups;
}

// 小功能：按遗忘曲线优先级生成今日复习队列，并拆成固定大小的小组。
function buildReviewQueue() {
  const cards = activeLibrary()?.cards || [];
  const dueCards = cards.filter(isDueToday);
  state.allDueCards = (dueCards.length ? dueCards : cards.slice(0, 10))
    .sort((left, right) => forgettingCurvePriority(right) - forgettingCurvePriority(left));
  state.reviewGroups = chunkCards(state.allDueCards, GROUP_SIZE);
  state.currentGroupIndex = 0;
  loadGroup(0);
}

// 小功能：加载指定复习小组，并重置本组内的答题状态。
function loadGroup(groupIndex) {
  state.currentGroupIndex = Math.min(Math.max(groupIndex, 0), Math.max(0, state.reviewGroups.length - 1));
  state.reviewCards = state.reviewGroups[state.currentGroupIndex] || [];
  state.currentReviewIndex = 0;
  state.answerVisible = false;
  state.selectedChoice = null;
  state.groupResults = [];
  renderGroupProgress();
}

// 小功能：把题型转换成中文标签。
function typeLabel(type) {
  if (type === "cloze") return "填空题";
  if (type === "choice") return "选择题";
  return "问答题";
}

// 小功能：把复习反馈转换成中文标签。
function gradeLabel(grade) {
  if (grade === "forgot") return "忘记";
  if (grade === "fuzzy") return "模糊";
  return "记得";
}

// 小功能：渲染当前小组进度，显示组号和每张卡片的完成状态。
function renderGroupProgress() {
  const totalGroups = state.reviewGroups.length;
  els.groupProgress.hidden = totalGroups === 0;
  els.groupLabel.textContent = totalGroups
    ? `第 ${state.currentGroupIndex + 1} 组 / 共 ${totalGroups} 组`
    : "暂无复习组";
  els.groupDots.innerHTML = state.reviewCards.map((card, index) => {
    const status = index < state.groupResults.length
      ? "done"
      : index === state.currentReviewIndex
        ? "current"
        : "pending";
    return `<span class="group-dot is-${status}" title="${escapeHtml(card.front || card.choice?.question || "")}"></span>`;
  }).join("");
}

// 小功能：渲染当前复习卡片，根据题型展示不同交互。
function renderReviewCard() {
  const card = state.reviewCards[state.currentReviewIndex];
  els.reviewCounter.textContent = state.reviewCards.length
    ? `${state.currentReviewIndex + 1} / ${state.reviewCards.length}`
    : "0 / 0";
  renderGroupProgress();

  if (!card) {
    els.reviewCard.innerHTML = state.allDueCards.length
      ? `<div class="empty">今日复习已完成。</div>`
      : `<div class="empty">今天没有可复习的卡片。可以让 Codex 继续从文件生成新卡片。</div>`;
    return;
  }

  const answerHtml = state.answerVisible
    ? `<div class="answer">${escapeHtml(card.back || card.choice?.explanation || "")}</div>`
    : "";

  if (card.type === "choice") {
    const options = card.choice?.options || [];
    const optionHtml = options.map((option, index) => {
      const isSelected = state.selectedChoice === index;
      const isCorrect = state.answerVisible && index === card.choice?.answerIndex;
      const isWrong = state.answerVisible && isSelected && !isCorrect;
      const className = ["choice-option", isCorrect ? "is-correct" : "", isWrong ? "is-wrong" : ""].join(" ");
      return `<button class="${className}" type="button" data-choice-index="${index}">${escapeHtml(option)}</button>`;
    }).join("");

    els.reviewCard.innerHTML = `
      <span class="card-type">${typeLabel(card.type)}</span>
      <div class="prompt">${escapeHtml(card.choice?.question || card.front)}</div>
      <div class="choice-list">${optionHtml}</div>
      ${answerHtml}
      <p class="source">${escapeHtml(card.source || "")}</p>
      <p class="tags">${escapeHtml((card.tags || []).join(" / "))}</p>
    `;
    bindChoiceButtons();
    return;
  }

  els.reviewCard.innerHTML = `
    <span class="card-type">${typeLabel(card.type)}</span>
    <div class="prompt">${escapeHtml(card.front)}</div>
    ${answerHtml}
    <p class="source">${escapeHtml(card.source || "")}</p>
    <p class="tags">${escapeHtml((card.tags || []).join(" / "))}</p>
  `;
}

// 小功能：给选择题选项绑定点击事件，并在选择后显示解析。
function bindChoiceButtons() {
  document.querySelectorAll("[data-choice-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedChoice = Number(button.dataset.choiceIndex);
      state.answerVisible = true;
      renderReviewCard();
    });
  });
}

// 小功能：渲染全部卡片列表，并支持关键词和题型筛选。
function renderAllCards() {
  const library = activeLibrary();
  const keyword = els.searchInput.value.trim().toLowerCase();
  const type = els.typeFilter.value;
  const cards = (library?.cards || []).filter((card) => {
    const haystack = [
      card.front,
      card.back,
      card.source,
      ...(card.tags || []),
      ...(card.choice?.options || [])
    ].join(" ").toLowerCase();
    const matchesKeyword = !keyword || haystack.includes(keyword);
    const matchesType = type === "all" || card.type === type;
    return matchesKeyword && matchesType;
  });

  els.allCounter.textContent = `${cards.length} 张`;
  els.allCards.innerHTML = cards.length
    ? cards.map(renderCardDetails).join("")
    : `<div class="empty">没有匹配的卡片。</div>`;
}

// 小功能：把单张卡片渲染成可展开详情。
function renderCardDetails(card) {
  const choice = card.choice
    ? `<p><strong>选项：</strong>${escapeHtml(card.choice.options.join(" / "))}</p>`
    : "";
  return `
    <details>
      <summary>${escapeHtml(card.front || card.choice?.question)}</summary>
      <p><span class="card-type">${typeLabel(card.type)}</span></p>
      <p>${escapeHtml(card.back || "")}</p>
      ${choice}
      <p class="source">${escapeHtml(card.source || "")}</p>
      <p class="tags">${escapeHtml((card.tags || []).join(" / "))}</p>
    </details>
  `;
}

// 小功能：按复习反馈计算下一次复习状态，保持与 skill 的间隔规则一致。
function nextReviewState(previous, grade) {
  const now = new Date();
  const currentInterval = Math.max(1, Number(previous?.intervalDays || 1));
  const currentIndex = Math.max(0, INTERVALS.findIndex((days) => days >= currentInterval));
  const rememberedIndex = Math.min(INTERVALS.length - 1, currentIndex + 1);
  const fuzzyIndex = Math.max(0, currentIndex - 1);
  const intervalDays = grade === "remembered"
    ? INTERVALS[rememberedIndex]
    : grade === "fuzzy"
      ? INTERVALS[fuzzyIndex]
      : 1;
  const nextReviewAt = new Date(now);
  nextReviewAt.setDate(now.getDate() + (grade === "forgot" ? 0 : intervalDays));

  return {
    ease: previous?.ease ?? 2.5,
    intervalDays,
    reviewCount: Number(previous?.reviewCount || 0) + 1,
    lastReviewedAt: now.toISOString(),
    nextReviewAt: nextReviewAt.toISOString(),
    status: grade === "forgot" ? "forgotten" : grade === "fuzzy" ? "learning" : "review"
  };
}

// 小功能：把浏览器侧复习反馈保存到 localStorage，便于用户本地临时记录。
function saveLocalReview(card, grade) {
  const key = "memory-card-studio-review";
  const raw = localStorage.getItem(key);
  const history = raw ? JSON.parse(raw) : {};
  history[card.id] = {
    grade,
    label: gradeLabel(grade),
    reviewedAt: new Date().toISOString()
  };
  localStorage.setItem(key, JSON.stringify(history));
}

// 小功能：处理单张卡片的复习反馈，并在小组完成时显示完成弹窗。
function handleGrade(grade) {
  const card = state.reviewCards[state.currentReviewIndex];
  if (!card) return;

  const previous = state.reviewState.cards?.[card.id];
  state.reviewState.cards = state.reviewState.cards || {};
  state.reviewState.cards[card.id] = nextReviewState(previous, grade);
  state.groupResults.push(grade);
  saveLocalReview(card, grade);

  if (state.currentReviewIndex < state.reviewCards.length - 1) {
    state.currentReviewIndex += 1;
    state.answerVisible = false;
    state.selectedChoice = null;
    renderReviewCard();
    return;
  }

  showCelebration();
}

// 小功能：统计当前小组复习结果，用于完成弹窗展示。
function groupStats() {
  return state.groupResults.reduce((stats, grade) => {
    stats[grade] += 1;
    return stats;
  }, { remembered: 0, fuzzy: 0, forgot: 0 });
}

// 小功能：显示小组完成弹窗，并决定按钮文案是继续下一组还是完成。
function showCelebration() {
  const stats = groupStats();
  const message = CHEERS[Math.floor(Math.random() * CHEERS.length)];
  const isLastGroup = state.currentGroupIndex >= state.reviewGroups.length - 1;
  els.celebrationTitle.textContent = message;
  els.celebrationStats.innerHTML = `
    <span>记得 ${stats.remembered}</span>
    <span>模糊 ${stats.fuzzy}</span>
    <span>忘记 ${stats.forgot}</span>
  `;
  els.continueGroup.textContent = isLastGroup ? "完成复习" : "下一组";
  els.celebrationOverlay.hidden = false;
}

// 小功能：关闭完成弹窗，并进入下一组或显示最终完成状态。
function continueAfterCelebration() {
  els.celebrationOverlay.hidden = true;
  if (state.currentGroupIndex < state.reviewGroups.length - 1) {
    loadGroup(state.currentGroupIndex + 1);
    renderReviewCard();
    return;
  }
  state.reviewCards = [];
  state.currentReviewIndex = 0;
  renderGroupProgress();
  renderReviewCard();
}

// 小功能：切换卡片库后刷新复习队列和全部卡片列表。
function setActiveLibrary(libraryId) {
  state.activeLibraryId = libraryId;
  buildReviewQueue();
  renderReviewCard();
  renderAllCards();
}

// 小功能：绑定顶部卡片库选择器。
function renderLibrarySelect() {
  els.librarySelect.innerHTML = state.libraries
    .map((library) => `<option value="${escapeHtml(library.id)}">${escapeHtml(library.name)}</option>`)
    .join("");
  els.librarySelect.value = state.activeLibraryId;
}

// 小功能：绑定所有页面事件。
function bindEvents() {
  els.librarySelect.addEventListener("change", (event) => setActiveLibrary(event.target.value));

  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      els.tabs.forEach((item) => item.classList.remove("is-active"));
      Object.values(els.panels).forEach((panel) => panel.classList.remove("is-active"));
      tab.classList.add("is-active");
      els.panels[tab.dataset.tab].classList.add("is-active");
    });
  });

  els.showAnswer.addEventListener("click", () => {
    state.answerVisible = !state.answerVisible;
    renderReviewCard();
  });

  els.prevCard.addEventListener("click", () => {
    if (!state.reviewCards.length) return;
    state.currentReviewIndex = Math.max(0, state.currentReviewIndex - 1);
    state.answerVisible = false;
    state.selectedChoice = null;
    renderReviewCard();
  });

  els.nextCard.addEventListener("click", () => {
    if (!state.reviewCards.length) return;
    state.currentReviewIndex = Math.min(state.reviewCards.length - 1, state.currentReviewIndex + 1);
    state.answerVisible = false;
    state.selectedChoice = null;
    renderReviewCard();
  });

  els.reviewButtons.forEach((button) => {
    button.addEventListener("click", () => handleGrade(button.dataset.grade));
  });

  els.continueGroup.addEventListener("click", continueAfterCelebration);
  els.searchInput.addEventListener("input", renderAllCards);
  els.typeFilter.addEventListener("change", renderAllCards);
}

// 小功能：启动应用，完成数据加载、事件绑定和首次渲染。
async function init() {
  await loadData();
  renderLibrarySelect();
  buildReviewQueue();
  bindEvents();
  renderReviewCard();
  renderAllCards();
}

init();
