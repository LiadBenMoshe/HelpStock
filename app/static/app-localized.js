const form = document.getElementById("analyze-form");
const input = document.getElementById("symbol-input");
const dashboard = document.getElementById("dashboard");
const loading = document.getElementById("loading");
const statusBanner = document.getElementById("status-banner");
const languageDropdown = document.getElementById("language-dropdown");
const languageButton = document.getElementById("language-button");
const languageButtonText = document.getElementById("language-button-text");
const languageMenu = document.getElementById("language-menu");
const languageOptions = Array.from(document.querySelectorAll(".language-option"));

const translations = {
  en: {
    htmlLang: "en",
    dir: "ltr",
    title: "HelpStock Dashboard",
    eyebrow: "Stock Intelligence Dashboard",
    heroCopy: "A compact research dashboard for technical levels, valuation, sentiment, news, and market context.",
    stockSymbol: "Stock Symbol",
    analyze: "Analyze",
    examples: "Examples: AAPL, MSFT, NVDA, TSLA",
    language: "Language",
    loading: "Fetching live market data and building the analysis...",
    companyOverview: "Company Overview",
    mainProducts: "Main Products / Services",
    supportResistance: "Support / Resistance",
    support: "Support",
    resistance: "Resistance",
    insiderActivity: "Insider Activity",
    revenueGrowth: "Revenue Growth",
    peAnalysis: "P/E Analysis",
    googleTrends: "Google Trends",
    vixStatus: "VIX Status",
    analystTargets: "Analyst Targets",
    newsSummaries: "News Summaries",
    partnerships: "Partnerships / Contracts",
    productRelevance: "Product Relevance",
    neutral: "Neutral",
    positive: "Positive",
    negative: "Negative",
    generated: "Generated",
    noProducts: "No specific products/services extracted.",
    noSupport: "No support levels found.",
    noResistance: "No resistance levels found.",
    noInsider: "No recent insider transactions available.",
    noTargets: "No analyst targets available.",
    noNews: "No recent news articles available.",
    noPartnerships: "No clear partnerships or contracts were identified from recent coverage.",
    noDrivers: "No specific drivers identified.",
    enterSymbol: "Please enter a stock symbol.",
    loaded: (symbol) => `Analysis loaded for ${symbol}.`,
    loadError: "Unable to fetch analysis.",
    name: "Name",
    date: "Date",
    type: "Type",
    shares: "Shares",
    change: "Change",
    analystSource: "Target Type",
    target: "Target",
    published: "Published",
    min: "Min",
    average: "Average",
    median: "Median",
    max: "Max",
    openArticle: "Open article",
    source: "Source",
    confidence: "Confidence",
    unknownPublisher: "Unknown publisher",
    current: "Current",
    previousYear: "Previous year",
    keyword: "Keyword",
    score: "Score",
    direction: "Direction",
    vix: "VIX",
    scoreLabel: "Score",
    na: "N/A",
    footerRights: "All Rights Reserved to Liad Ben Moshe",
  },
  he: {
    htmlLang: "he",
    dir: "rtl",
    title: "לוח הבקרה HelpStock",
    eyebrow: "לוח ניתוח מניות",
    heroCopy: "לוח מחקר תמציתי לרמות טכניות, תמחור, סנטימנט, חדשות והקשר שוק.",
    stockSymbol: "סימול מניה",
    analyze: "נתח",
    examples: "דוגמאות: AAPL, MSFT, NVDA, TSLA",
    language: "שפה",
    loading: "טוען נתוני שוק חיים ובונה את הניתוח...",
    companyOverview: "סקירת חברה",
    mainProducts: "מוצרים / שירותים עיקריים",
    supportResistance: "תמיכה / התנגדות",
    support: "תמיכה",
    resistance: "התנגדות",
    insiderActivity: "פעילות בעלי עניין",
    revenueGrowth: "צמיחת הכנסות",
    peAnalysis: "ניתוח מכפיל רווח",
    googleTrends: "Google Trends",
    vixStatus: "מצב VIX",
    analystTargets: "יעדי אנליסטים",
    newsSummaries: "סיכומי חדשות",
    partnerships: "שותפויות / חוזים",
    productRelevance: "רלוונטיות המוצר",
    neutral: "ניטרלי",
    positive: "חיובי",
    negative: "שלילי",
    generated: "נוצר",
    noProducts: "לא זוהו מוצרים או שירותים ספציפיים.",
    noSupport: "לא נמצאו רמות תמיכה.",
    noResistance: "לא נמצאו רמות התנגדות.",
    noInsider: "אין עסקאות פנים זמינות מהתקופה האחרונה.",
    noTargets: "אין יעדי אנליסטים זמינים.",
    noNews: "אין כתבות חדשות זמינות.",
    noPartnerships: "לא זוהו שותפויות או חוזים ברורים מהסיקור האחרון.",
    noDrivers: "לא זוהו גורמים ספציפיים.",
    enterSymbol: "יש להזין סימול מניה.",
    loaded: (symbol) => `הניתוח עבור ${symbol} נטען.`,
    loadError: "לא ניתן להביא את הניתוח.",
    name: "שם",
    date: "תאריך",
    type: "סוג",
    shares: "מניות",
    change: "שינוי",
    analystSource: "אנליסט / מקור",
    target: "יעד",
    published: "פורסם",
    min: "מינימום",
    average: "ממוצע",
    median: "חציון",
    max: "מקסימום",
    openArticle: "פתח כתבה",
    source: "מקור",
    confidence: "רמת ביטחון",
    unknownPublisher: "מפרסם לא ידוע",
    current: "נוכחי",
    previousYear: "שנה קודמת",
    keyword: "מילת מפתח",
    score: "ציון",
    direction: "כיוון",
    vix: "VIX",
    scoreLabel: "ציון",
    na: "לא זמין",
  },
};

const uiState = {
  language: localStorage.getItem("helpstock-language") || "en",
  lastPayload: null,
  lastSymbol: null,
};

translations.he.footerRights = "כל הזכויות שמורות לליעד בן משה";

translations.he.analystSource = "סוג יעד";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const symbol = input.value.trim().toUpperCase();
  if (!symbol) {
    showStatus(t("enterSymbol"), "negative");
    return;
  }

  await runAnalysis(symbol);
});

if (languageButton) {
  languageButton.addEventListener("click", () => {
    const expanded = languageButton.getAttribute("aria-expanded") === "true";
    setLanguageMenuOpen(!expanded);
  });
}

languageOptions.forEach((option) => {
  option.addEventListener("click", async () => {
    const nextLanguage = option.dataset.lang;
    if (!nextLanguage || nextLanguage === uiState.language) {
      setLanguageMenuOpen(false);
      return;
    }

    uiState.language = nextLanguage;
    localStorage.setItem("helpstock-language", uiState.language);
    applyLanguage();
    setLanguageMenuOpen(false);

    if (uiState.lastSymbol) {
      await runAnalysis(uiState.lastSymbol, true);
      return;
    }
    if (uiState.lastPayload) {
      renderDashboard(uiState.lastPayload);
    }
  });
});

document.addEventListener("click", (event) => {
  if (!languageDropdown || languageDropdown.contains(event.target)) {
    return;
  }
  setLanguageMenuOpen(false);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setLanguageMenuOpen(false);
  }
});

async function runAnalysis(symbol, preserveStatus = false) {
  uiState.lastSymbol = symbol;

  setLoading(true);
  if (!preserveStatus) {
    showStatus("", "neutral", true);
  }

  try {
    const response = await fetch(
      `/analyze/${encodeURIComponent(symbol)}?lang=${encodeURIComponent(uiState.language)}`
    );
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || t("loadError"));
    }
    uiState.lastPayload = payload;
    renderDashboard(payload);
    showStatus(t("loaded", payload.symbol), "positive");
  } catch (error) {
    dashboard.classList.add("hidden");
    showStatus(error.message || t("loadError"), "negative");
  } finally {
    setLoading(false);
  }
}

function applyLanguage() {
  const lang = translations[uiState.language];
  document.documentElement.lang = lang.htmlLang;
  document.documentElement.dir = lang.dir;
  document.title = lang.title;
  if (languageButtonText) {
    languageButtonText.textContent = uiState.language === "he" ? "עברית" : "English";
  }
  languageOptions.forEach((option) => {
    option.classList.toggle("is-active", option.dataset.lang === uiState.language);
    option.setAttribute("aria-selected", option.dataset.lang === uiState.language ? "true" : "false");
  });

  setText(".hero .eyebrow", lang.eyebrow);
  setText(".hero-copy", lang.heroCopy);
  setText('label[for="symbol-input"]', lang.stockSymbol);
  setText(".hint", lang.examples);
  setText('button[type="submit"]', lang.analyze);
  setText(".language-label", lang.language);
  setText("#footer-rights", lang.footerRights);
  setText("#loading span", lang.loading);
  setText("#summary-card .eyebrow", lang.companyOverview);
  setText("#summary-card h3", lang.mainProducts);

  const headers = document.querySelectorAll(".card > .card-header > h3");
  const headerKeys = [
    "supportResistance",
    "insiderActivity",
    "revenueGrowth",
    "peAnalysis",
    "googleTrends",
    "vixStatus",
    "analystTargets",
    "newsSummaries",
    "partnerships",
    "productRelevance",
  ];
  headers.forEach((header, index) => {
    header.textContent = lang[headerKeys[index]];
  });

  const sectionLabels = document.querySelectorAll(".two-col h4");
  if (sectionLabels[0]) sectionLabels[0].textContent = lang.support;
  if (sectionLabels[1]) sectionLabels[1].textContent = lang.resistance;

  const tableRows = document.querySelectorAll("table thead tr");
  const insiderHeaders = tableRows[0]?.children || [];
  if (insiderHeaders.length >= 5) {
    insiderHeaders[0].textContent = lang.name;
    insiderHeaders[1].textContent = lang.date;
    insiderHeaders[2].textContent = lang.type;
    insiderHeaders[3].textContent = lang.shares;
    insiderHeaders[4].textContent = lang.change;
  }

  const targetHeaders = tableRows[1]?.children || [];
  if (targetHeaders.length >= 3) {
    targetHeaders[0].textContent = lang.analystSource;
    targetHeaders[1].textContent = lang.target;
    targetHeaders[2].textContent = lang.published;
  }
}

function renderDashboard(data) {
  dashboard.classList.remove("hidden");

  document.getElementById("company-name").textContent = `${data.company_overview.name} (${data.symbol})`;
  document.getElementById("generated-at").textContent = `${t("generated")}: ${formatDate(data.generated_at)}`;
  document.getElementById("company-meta").textContent =
    [data.company_overview.sector, data.company_overview.industry, data.company_overview.website]
      .filter(Boolean)
      .join(" • ");
  document.getElementById("company-description").textContent = data.company_overview.description;
  renderList(document.getElementById("company-products"), data.company_overview.products_services, t("noProducts"));

  document.getElementById("support-methodology").textContent = data.support_resistance.methodology;
  renderPriceLevels(document.getElementById("support-levels"), data.support_resistance.support_levels, t("noSupport"));
  renderPriceLevels(document.getElementById("resistance-levels"), data.support_resistance.resistance_levels, t("noResistance"));

  setBadge("insider-badge", data.insider_activity.sentiment);
  document.getElementById("insider-summary").textContent = data.insider_activity.summary;
  renderTableRows(
    document.getElementById("insider-table"),
    data.insider_activity.transactions,
    (item) => `
      <tr>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.transaction_date || "-")}</td>
        <td>${escapeHtml(item.transaction_type || "-")}</td>
        <td>${formatNumber(item.shares)}</td>
        <td>${formatNumber(item.change)}</td>
      </tr>
    `,
    5,
    t("noInsider")
  );

  setBadge("revenue-badge", data.revenue_analysis.signal);
  document.getElementById("revenue-figures").textContent =
    `${formatCurrency(data.revenue_analysis.latest_revenue)} vs ${formatCurrency(data.revenue_analysis.year_ago_revenue)} (${formatPercent(data.revenue_analysis.growth_percent)})`;
  document.getElementById("revenue-interpretation").textContent = data.revenue_analysis.interpretation;

  setBadge("pe-badge", data.pe_analysis.signal);
  document.getElementById("pe-figures").textContent =
    `${t("current")}: ${formatNumber(data.pe_analysis.current_pe)} | ${t("previousYear")}: ${formatNumber(data.pe_analysis.previous_year_pe)}`;
  document.getElementById("pe-interpretation").textContent = data.pe_analysis.interpretation;

  setBadge("trends-badge", data.google_trends.signal);
  document.getElementById("trends-score").textContent =
    `${t("keyword")}: ${data.google_trends.keyword} | ${t("score")}: ${data.google_trends.score ?? t("na")} | ${t("direction")}: ${data.google_trends.direction}`;
  document.getElementById("trends-interpretation").textContent = data.google_trends.interpretation;

  setBadge(
    "vix-badge",
    data.vix_status.signal,
    uiState.language === "he" ? data.vix_status.label_he : null
  );
  document.getElementById("vix-value").textContent = `${t("vix")}: ${formatNumber(data.vix_status.value)}`;
  document.getElementById("vix-interpretation").textContent = data.vix_status.interpretation;

  setBadge("relevance-badge", data.product_relevance.signal);
  document.getElementById("relevance-score").textContent = `${t("scoreLabel")}: ${data.product_relevance.score}/100`;
  document.getElementById("relevance-interpretation").textContent = data.product_relevance.interpretation;
  renderList(document.getElementById("relevance-drivers"), data.product_relevance.drivers, t("noDrivers"));

  renderStats(data.analyst_targets.stats);
  renderAnalystTargets(data.analyst_targets.targets);

  renderNews(data.news_summaries);
  renderPartnerships(data.partnerships_and_contracts);
}

function renderPriceLevels(element, items, emptyText) {
  renderList(
    element,
    (items || []).map((item) => `${item.label}: ${formatCurrency(item.price)}`),
    emptyText
  );
}

function renderList(element, items, emptyText) {
  const entries = (items || []).filter(Boolean);
  if (!entries.length) {
    element.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  element.innerHTML = entries.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("");
}

function renderTableRows(element, items, rowRenderer, colspan, emptyText) {
  const rows = items || [];
  if (!rows.length) {
    element.innerHTML = `<tr><td colspan="${colspan}">${escapeHtml(emptyText)}</td></tr>`;
    return;
  }
  element.innerHTML = rows.map(rowRenderer).join("");
}

function renderStats(stats) {
  const container = document.getElementById("target-stats");
  const chips = [
    [t("min"), formatCurrency(stats.minimum)],
    [t("average"), formatCurrency(stats.average)],
    [t("median"), formatCurrency(stats.median)],
    [t("max"), formatCurrency(stats.maximum)],
  ];
  container.innerHTML = chips
    .map(([label, value]) => `<div class="stat-chip"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderAnalystTargets(items) {
  const rows = items || [];
  const tableRows = document.querySelectorAll("table thead tr");
  const targetHeaders = tableRows[1]?.children || [];
  const hasPublishedDates = rows.some((item) => item.published_at);

  if (targetHeaders.length >= 3) {
    targetHeaders[0].textContent = t("analystSource");
    targetHeaders[1].textContent = t("target");
    targetHeaders[2].textContent = t("published");
    targetHeaders[2].style.display = hasPublishedDates ? "" : "none";
  }

  renderTableRows(
    document.getElementById("targets-table"),
    rows,
    (item) => `
      <tr>
        <td>${escapeHtml(item.analyst || item.source)}</td>
        <td>${formatCurrency(item.target_price)}</td>
        <td style="display:${hasPublishedDates ? "" : "none"}">${escapeHtml(item.published_at || "-")}</td>
      </tr>
    `,
    hasPublishedDates ? 3 : 2,
    t("noTargets")
  );
}

function renderNews(items) {
  const container = document.getElementById("news-list");
  if (!items || !items.length) {
    container.innerHTML = `<div class="news-item">${escapeHtml(t("noNews"))}</div>`;
    return;
  }

  container.innerHTML = items
    .map((item) => `
      <article class="news-item">
        <div class="card-header">
          <h4>${escapeHtml(item.title)}</h4>
          <span class="badge ${item.sentiment}">${translateSignal(item.sentiment)}</span>
        </div>
        <p>${escapeHtml(item.summary)}</p>
        <p class="muted">${escapeHtml(item.publisher || t("unknownPublisher"))} • ${escapeHtml(item.published_at || "-")}</p>
        ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">${t("openArticle")}</a>` : ""}
      </article>
    `)
    .join("");
}

function renderPartnerships(items) {
  const container = document.getElementById("partnerships-list");
  if (!items || !items.length) {
    container.innerHTML = `<div class="partnership-item">${escapeHtml(t("noPartnerships"))}</div>`;
    return;
  }

  container.innerHTML = items
    .map((item) => `
      <article class="partnership-item">
        <h4>${escapeHtml(item.title)}</h4>
        <p>${escapeHtml(item.summary)}</p>
        <p class="muted">${t("confidence")}: ${escapeHtml(item.confidence)}</p>
        ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">${t("source")}</a>` : ""}
      </article>
    `)
    .join("");
}

function setBadge(id, signal, customText) {
  const badge = document.getElementById(id);
  badge.className = `badge ${signal || "neutral"}`;
  badge.textContent = customText || translateSignal(signal || "neutral");
}

function setLoading(isLoading) {
  loading.classList.toggle("hidden", !isLoading);
}

function showStatus(message, signal, hidden = false) {
  statusBanner.textContent = message;
  statusBanner.className = `status-banner ${signal || "neutral"} ${hidden ? "hidden" : ""}`.trim();
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return t("na");
  return new Intl.NumberFormat(currentLocale(), {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return t("na");
  return new Intl.NumberFormat(currentLocale(), { maximumFractionDigits: 2 }).format(value);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return t("na");
  return `${new Intl.NumberFormat(currentLocale(), { maximumFractionDigits: 2 }).format(value)}%`;
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(currentLocale());
}

function translateSignal(value) {
  if (value === "positive") return t("positive");
  if (value === "negative") return t("negative");
  return t("neutral");
}

function t(key, ...args) {
  const value = translations[uiState.language][key];
  return typeof value === "function" ? value(...args) : value;
}

function currentLocale() {
  return uiState.language === "he" ? "he-IL" : "en-US";
}

function setText(selector, value) {
  const element = document.querySelector(selector);
  if (element) {
    element.textContent = value;
  }
}

function setLanguageMenuOpen(isOpen) {
  if (!languageButton || !languageMenu) {
    return;
  }
  languageButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
  languageMenu.classList.toggle("hidden", !isOpen);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

applyLanguage();
