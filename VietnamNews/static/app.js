let allArticles = [];
let currentCategory = "all";
let currentConfig = {
  ai_model: "gemini-4-argon",
  news_sources: []
};

document.addEventListener("DOMContentLoaded", () => {
  setupCategoryTabs();
  loadNews(false);
});

function setupCategoryTabs() {
  const tabs = document.querySelectorAll("#categoryTabs .tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentCategory = tab.getAttribute("data-cat");
      renderArticles();
    });
  });
}

async function loadNews(forceRefresh = false) {
  const btn = document.getElementById("refreshBtn");
  const grid = document.getElementById("newsGrid");
  btn.disabled = true;

  if (forceRefresh) {
    grid.innerHTML = '<div class="loading-state">실시간 베트남 뉴스를 다시 수집하고 전체 내용을 한글로 번역하는 중입니다...</div>';
  }

  try {
    const endpoint = forceRefresh ? "/api/news?refresh=1" : "/api/news";
    const res = await fetch(endpoint);
    const data = await res.json();

    applyDashboardData(data);
  } catch (err) {
    console.error("Failed to load news:", err);
    grid.innerHTML = '<div class="loading-state">뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</div>';
  } finally {
    btn.disabled = false;
  }
}

function applyDashboardData(data) {
  allArticles = data.articles || [];
  if (data.config) {
    currentConfig = data.config;
  }
  document.getElementById("count-all").textContent = allArticles.length;
  document.getElementById("updatedAt").textContent = "마지막 업데이트: " + (data.updated_at || "-");

  const activeModel = (data.config && data.config.ai_model) || (data.mcp_status && data.mcp_status.active_model) || "gemini-4-argon";
  const modelLabel = document.getElementById("activeModelLabel");
  if (modelLabel) {
    modelLabel.textContent = "AI 모델: " + activeModel;
  }

  // Update MCP status badge
  const mcpBadge = document.getElementById("mcpBadge");
  const mcpText = document.getElementById("mcpText");
  if (data.mcp_status && data.mcp_status.connected) {
    mcpBadge.className = "mcp-badge connected";
    mcpText.textContent = `Gemini MCP 연결됨 (${activeModel} · 도구 ${data.mcp_status.tools_count}개)`;
  } else {
    mcpBadge.className = "mcp-badge";
    mcpText.textContent = `Gemini MCP (${activeModel})`;
  }

  // Update Briefing
  const briefing = data.briefing || {};
  document.getElementById("briefingSummary").textContent =
    briefing.summary || "오늘의 베트남 주요 뉴스 한글 브리핑입니다.";

  const highlightsEl = document.getElementById("briefingHighlights");
  highlightsEl.innerHTML = "";
  (briefing.highlights || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    highlightsEl.appendChild(li);
  });

  renderArticles();
}

function refreshNews() {
  loadNews(true);
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderArticles() {
  const grid = document.getElementById("newsGrid");
  const query = (document.getElementById("searchInput").value || "").trim().toLowerCase();

  const filtered = allArticles.filter((art) => {
    const matchCat = currentCategory === "all" || art.category === currentCategory;
    if (!matchCat) return false;
    if (!query) return true;
    const hay = `${art.title_ko} ${art.summary_ko} ${art.source} ${art.category_ko}`.toLowerCase();
    return hay.includes(query);
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="loading-state">해당 조건에 맞는 뉴스가 없습니다.</div>';
    return;
  }

  grid.innerHTML = filtered
    .map((art) => {
      const imgTag = art.image
        ? `<img class="card-thumb" src="${escapeHtml(art.image)}" alt="뉴스 썸네일" loading="lazy" onerror="this.style.display='none'" />`
        : "";
      return `
        <article class="news-card">
          ${imgTag}
          <div class="card-body">
            <div class="card-meta">
              <div class="badge-group">
                <span class="badge-source">${escapeHtml(art.source)}</span>
                <span class="badge-cat">${escapeHtml(art.category_ko)}</span>
              </div>
              <span class="pub-date">${escapeHtml(art.published_at)}</span>
            </div>
            <h3 class="title-ko">${escapeHtml(art.title_ko)}</h3>
            <p class="summary-ko">${escapeHtml(art.summary_ko)}</p>
            <div class="card-footer">
              <a class="read-link" href="${escapeHtml(art.link)}" target="_blank" rel="noopener noreferrer">
                원문 기사 보기 →
              </a>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

/* Settings Modal Functions */
async function openSettingsModal() {
  try {
    const res = await fetch("/api/config");
    const cfg = await res.json();
    currentConfig = cfg;
  } catch (e) {}

  const modelInput = document.getElementById("aiModelInput");
  const modelSelect = document.getElementById("aiModelSelect");
  const modelVal = currentConfig.ai_model || "gemini-4-argon";
  modelInput.value = modelVal;

  const knownOptions = Array.from(modelSelect.options).map((o) => o.value);
  if (knownOptions.includes(modelVal)) {
    modelSelect.value = modelVal;
  } else {
    modelSelect.value = "custom";
  }

  const listEl = document.getElementById("sourcesList");
  listEl.innerHTML = "";
  (currentConfig.news_sources || []).forEach((src) => {
    addSourceRow(src);
  });

  document.getElementById("settingsModal").classList.remove("hidden");
}

function closeSettingsModal() {
  document.getElementById("settingsModal").classList.add("hidden");
}

function handleOverlayClick(e) {
  if (e.target.id === "settingsModal") {
    closeSettingsModal();
  }
}

function syncModelInput() {
  const select = document.getElementById("aiModelSelect");
  const input = document.getElementById("aiModelInput");
  if (select.value !== "custom") {
    input.value = select.value;
  } else {
    input.focus();
  }
}

function addSourceRow(src = { source: "", category: "latest", url: "" }) {
  const listEl = document.getElementById("sourcesList");
  const row = document.createElement("div");
  row.className = "source-row";

  const categories = [
    { val: "latest", label: "속보·종합" },
    { val: "economy", label: "경제·비즈니스" },
    { val: "hanoi", label: "하노이·로컬" },
    { val: "society", label: "사회·로컬" },
    { val: "tech", label: "IT·과학" },
    { val: "culture", label: "문화·라이프" }
  ];

  const optionsHtml = categories
    .map((c) => `<option value="${c.val}" ${src.category === c.val ? "selected" : ""}>${c.label}</option>`)
    .join("");

  row.innerHTML = `
    <input type="text" class="src-name" placeholder="사이트 이름 (예: VnExpress)" value="${escapeHtml(src.source || "")}" />
    <select class="src-cat">${optionsHtml}</select>
    <input type="url" class="src-url" placeholder="https://vnexpress.net/rss/tin-moi-nhat.rss" value="${escapeHtml(src.url || "")}" />
    <button type="button" class="btn-remove-source" title="삭제" onclick="this.parentElement.remove()">✕</button>
  `;
  listEl.appendChild(row);
}

async function saveSettings() {
  const saveBtn = document.getElementById("saveSettingsBtn");
  const aiModel = (document.getElementById("aiModelInput").value || "gemini-4-argon").trim();
  const rows = document.querySelectorAll("#sourcesList .source-row");

  const newsSources = [];
  rows.forEach((r) => {
    const name = r.querySelector(".src-name").value.trim() || "뉴스 사이트";
    const cat = r.querySelector(".src-cat").value;
    const url = r.querySelector(".src-url").value.trim();
    if (url) {
      newsSources.push({ source: name, category: cat, url });
    }
  });

  if (newsSources.length === 0) {
    alert("최소 1개 이상의 뉴스 수집 사이트 주소를 입력해 주세요.");
    return;
  }

  saveBtn.disabled = true;
  saveBtn.textContent = "저장 및 뉴스 번역 중...";

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ai_model: aiModel,
        news_sources: newsSources,
        refresh_now: true
      })
    });
    const result = await res.json();
    if (result.ok && result.news) {
      applyDashboardData(result.news);
      closeSettingsModal();
    } else {
      alert("설정 저장 실패: " + (result.error || "알 수 없는 오류"));
    }
  } catch (err) {
    alert("설정 저장 중 오류가 발생했습니다.");
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "설정 저장 및 뉴스 다시 수집";
  }
}
