const form = document.getElementById("analyze-form");
const input = document.getElementById("symbol-input");
const dashboard = document.getElementById("dashboard");
const loading = document.getElementById("loading");
const statusBanner = document.getElementById("status-banner");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const symbol = input.value.trim().toUpperCase();
  if (!symbol) {
    showStatus("Please enter a stock symbol.", "negative");
    return;
  }

  setLoading(true);
  showStatus("", "neutral", true);

  try {
    const response = await fetch(`/analyze/${encodeURIComponent(symbol)}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis failed.");
    }
    renderDashboard(payload);
    showStatus(`Analysis loaded for ${payload.symbol}.`, "positive");
  } catch (error) {
    dashboard.classList.add("hidden");
    showStatus(error.message || "Unable to fetch analysis.", "negative");
  } finally {
    setLoading(false);
  }
});

function renderDashboard(data) {
  dashboard.classList.remove("hidden");

  document.getElementById("company-name").textContent = `${data.company_overview.name} (${data.symbol})`;
  document.getElementById("generated-at").textContent = `Generated: ${formatDate(data.generated_at)}`;
  document.getElementById("company-meta").textContent =
    [data.company_overview.sector, data.company_overview.industry, data.company_overview.website]
      .filter(Boolean)
      .join(" • ");
  document.getElementById("company-description").textContent = data.company_overview.description;
  renderList(
    document.getElementById("company-products"),
    data.company_overview.products_services,
    "No specific products/services extracted."
  );

  document.getElementById("support-methodology").textContent = data.support_resistance.methodology;
  renderPriceLevels(document.getElementById("support-levels"), data.support_resistance.support_levels, "No support levels found.");
  renderPriceLevels(document.getElementById("resistance-levels"), data.support_resistance.resistance_levels, "No resistance levels found.");

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
    "No recent insider transactions available."
  );

  setBadge("revenue-badge", data.revenue_analysis.signal);
  document.getElementById("revenue-figures").textContent =
    `${formatCurrency(data.revenue_analysis.latest_revenue)} vs ${formatCurrency(data.revenue_analysis.year_ago_revenue)} (${formatPercent(data.revenue_analysis.growth_percent)})`;
  document.getElementById("revenue-interpretation").textContent = data.revenue_analysis.interpretation;

  setBadge("pe-badge", data.pe_analysis.signal);
  document.getElementById("pe-figures").textContent =
    `Current: ${formatNumber(data.pe_analysis.current_pe)} | Previous year: ${formatNumber(data.pe_analysis.previous_year_pe)}`;
  document.getElementById("pe-interpretation").textContent = data.pe_analysis.interpretation;

  setBadge("trends-badge", data.google_trends.signal);
  document.getElementById("trends-score").textContent =
    `Keyword: ${data.google_trends.keyword} | Score: ${data.google_trends.score ?? "N/A"} | Direction: ${data.google_trends.direction}`;
  document.getElementById("trends-interpretation").textContent = data.google_trends.interpretation;

  setBadge("vix-badge", data.vix_status.signal, data.vix_status.label_he);
  document.getElementById("vix-value").textContent = `VIX: ${formatNumber(data.vix_status.value)}`;
  document.getElementById("vix-interpretation").textContent = data.vix_status.interpretation;

  setBadge("relevance-badge", data.product_relevance.signal);
  document.getElementById("relevance-score").textContent = `Score: ${data.product_relevance.score}/100`;
  document.getElementById("relevance-interpretation").textContent = data.product_relevance.interpretation;
  renderList(document.getElementById("relevance-drivers"), data.product_relevance.drivers, "No specific drivers identified.");

  renderStats(data.analyst_targets.stats);
  renderTableRows(
    document.getElementById("targets-table"),
    data.analyst_targets.targets,
    (item) => `
      <tr>
        <td>${escapeHtml(item.analyst || item.source)}</td>
        <td>${formatCurrency(item.target_price)}</td>
        <td>${escapeHtml(item.published_at || "-")}</td>
      </tr>
    `,
    3,
    "No analyst targets available."
  );

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
    ["Min", formatCurrency(stats.minimum)],
    ["Average", formatCurrency(stats.average)],
    ["Median", formatCurrency(stats.median)],
    ["Max", formatCurrency(stats.maximum)],
  ];
  container.innerHTML = chips
    .map(([label, value]) => `<div class="stat-chip"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderNews(items) {
  const container = document.getElementById("news-list");
  if (!items || !items.length) {
    container.innerHTML = `<div class="news-item">No recent news articles available.</div>`;
    return;
  }

  container.innerHTML = items
    .map((item) => `
      <article class="news-item">
        <div class="card-header">
          <h4>${escapeHtml(item.title)}</h4>
          <span class="badge ${item.sentiment}">${capitalize(item.sentiment)}</span>
        </div>
        <p>${escapeHtml(item.summary)}</p>
        <p class="muted">${escapeHtml(item.publisher || "Unknown publisher")} • ${escapeHtml(item.published_at || "-")}</p>
        ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">Open article</a>` : ""}
      </article>
    `)
    .join("");
}

function renderPartnerships(items) {
  const container = document.getElementById("partnerships-list");
  if (!items || !items.length) {
    container.innerHTML = `<div class="partnership-item">No clear partnerships or contracts were identified from recent coverage.</div>`;
    return;
  }

  container.innerHTML = items
    .map((item) => `
      <article class="partnership-item">
        <h4>${escapeHtml(item.title)}</h4>
        <p>${escapeHtml(item.summary)}</p>
        <p class="muted">Confidence: ${escapeHtml(item.confidence)}</p>
        ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">Source</a>` : ""}
      </article>
    `)
    .join("");
}

function setBadge(id, signal, customText) {
  const badge = document.getElementById(id);
  badge.className = `badge ${signal || "neutral"}`;
  badge.textContent = customText || capitalize(signal || "neutral");
}

function setLoading(isLoading) {
  loading.classList.toggle("hidden", !isLoading);
}

function showStatus(message, signal, hidden = false) {
  statusBanner.textContent = message;
  statusBanner.className = `status-banner ${signal || "neutral"} ${hidden ? "hidden" : ""}`.trim();
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return `${value}%`;
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function capitalize(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
