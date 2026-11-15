let allArticles = [];
let currentCategory = "all";

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
    grid.innerHTML = '<div class="loading-state">실시간 베트남 뉴스를 다시 수집하고 번역 중입니다...</div>';
  }

  try {
    const endpoint = forceRefresh ? "/api/news?refresh=1" : "/api/news";
    const res = await fetch(endpoint);
    const data = await res.json();

    allArticles = data.articles || [];
    document.getElementById("count-all").textContent = allArticles.length;
    document.getElementById("updatedAt").textContent = "마지막 업데이트: " + (data.updated_at || "-");

    // Update MCP status badge
    const mcpBadge = document.getElementById("mcpBadge");
    const mcpText = document.getElementById("mcpText");
    if (data.mcp_status && data.mcp_status.connected) {
      mcpBadge.className = "mcp-badge connected";
      mcpText.textContent = `Gemini MCP 연결됨 (${data.mcp_status.server_name} v${data.mcp_status.server_version} · 도구 ${data.mcp_status.tools_count}개)`;
    } else {
      mcpBadge.className = "mcp-badge";
      mcpText.textContent = "Gemini MCP 대기 중";
    }

    // Update Briefing
    const briefing = data.briefing || {};
    document.getElementById("briefingSummary").textContent =
      briefing.summary || "오늘의 베트남 주요 뉴스 브리핑입니다.";

    const highlightsEl = document.getElementById("briefingHighlights");
    highlightsEl.innerHTML = "";
    (briefing.highlights || []).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      highlightsEl.appendChild(li);
    });

    renderArticles();
  } catch (err) {
    console.error("Failed to load news:", err);
    grid.innerHTML = '<div class="loading-state">뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</div>';
  } finally {
    btn.disabled = false;
  }
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
    const hay = `${art.title_ko} ${art.title_vi} ${art.summary_ko} ${art.source}`.toLowerCase();
    return hay.includes(query);
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="loading-state">해당 조건에 맞는 뉴스가 없습니다.</div>';
    return;
  }

  grid.innerHTML = filtered
    .map((art) => {
      const imgTag = art.image
        ? `<img class="card-thumb" src="${escapeHtml(art.image)}" alt="news thumbnail" loading="lazy" onerror="this.style.display='none'" />`
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
            <p class="title-vi">${escapeHtml(art.title_vi)}</p>
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
