/* GitCheck frontend. */

const $ = (id) => document.getElementById(id);
const form = $("analyze-form");
const repoInput = $("repo-url");
const compareInput = $("repo-compare");
const analyzeBtn = $("analyze-btn");
const formStatus = $("form-status");
const toast = $("toast");

const report = $("report");
const compareSection = $("compare-section");

const RING_CIRC = 2 * Math.PI * 50;

const RISK_COLORS = {
  Low: "#22e37a",
  Medium: "#ffb84a",
  High: "#ff6b87",
};

const STATUS_EMOJI = {
  Thriving: "🚀",
  Active: "✅",
  Moderate: "🟡",
  Risky: "⚠️",
  Stale: "🕸",
  Abandoned: "🪦",
  Archived: "📦",
  Empty: "∅",
  Unknown: "❓",
};

const fmtNumber = (n) => {
  if (n === null || n === undefined) return "—";
  if (typeof n !== "number") return String(n);
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "k";
  return n.toLocaleString();
};

const fmtPercent = (v) => (v === null || v === undefined) ? "—" : `${Math.round(v * 100)}%`;

const fmtDaysAgo = (days) => {
  if (days === null || days === undefined) return "—";
  if (days === 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.round(days / 30)}mo ago`;
  const y = (days / 365).toFixed(1).replace(/\.0$/, "");
  return `${y}y ago`;
};

const riskClass = (risk) =>
  risk === "Low" ? "good" : risk === "Medium" ? "warn" : risk === "High" ? "bad" : "";

const setRiskTheme = (risk) => {
  const color = RISK_COLORS[risk] || "#7c5cff";
  document.documentElement.style.setProperty("--risk-color", color);
};

const showToast = (message, isError = true) => {
  toast.textContent = message;
  toast.style.borderColor = isError ? "var(--bad)" : "var(--good)";
  toast.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("show"), 4500);
};

const setLoading = (loading) => {
  analyzeBtn.disabled = loading;
  analyzeBtn.classList.toggle("loading", loading);
};

const parseRepoInput = (value) => {
  if (!value) return null;
  return value.trim();
};

const parseCompareList = (raw) => {
  if (!raw || !raw.trim()) return [];
  return raw
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 5);
};

const fetchAnalysis = async (repoUrl) => {
  const res = await fetch(`/api/analyze?repo_url=${encodeURIComponent(repoUrl)}`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
};

const renderSingle = (data) => {
  report.classList.remove("hidden");

  const score = Math.max(0, Math.min(100, Math.round(data.score || 0)));
  const risk = data.risk_level || "Unknown";
  const status = data.status || "Unknown";
  setRiskTheme(risk);

  const ring = $("ring-fg");
  ring.setAttribute("stroke-dasharray", String(RING_CIRC));
  ring.setAttribute("stroke-dashoffset", String(RING_CIRC * (1 - score / 100)));

  animateNumber($("score-value"), score, { suffix: "" });
  $("score-sub").textContent = "out of 100";

  const pillStatus = $("pill-status");
  pillStatus.textContent = `${STATUS_EMOJI[status] || ""} ${status}`.trim();
  pillStatus.className = `pill ${riskClass(risk)}`;

  const pillRisk = $("pill-risk");
  pillRisk.textContent = `${risk} risk`;
  pillRisk.className = `pill ${riskClass(risk)}`;

  const avatar = $("repo-avatar");
  avatar.textContent = (data.repository || "?")[0].toUpperCase();

  $("repo-name").textContent = data.repository || "—";
  $("repo-desc").textContent = data.description || "No description provided.";

  const metaBits = [];
  if (data.language) metaBits.push(data.language);
  if (data.license) metaBits.push(data.license);
  if (data.latest_release) metaBits.push(`Latest: ${data.latest_release}`);
  if (data.metadata?.age_days) metaBits.push(`Created ${fmtDaysAgo(data.metadata.age_days)}`);
  const metaEl = $("repo-meta");
  metaEl.innerHTML = metaBits.length
    ? metaBits.map((b) => `<span class="meta-chip">${escapeHtml(b)}</span>`).join("")
    : '<span class="meta-chip">—</span>';

  const callout = $("report-callout");
  callout.style.borderLeftColor = RISK_COLORS[risk] || "var(--risk-color)";
  $("callout-icon").textContent = STATUS_EMOJI[status] || "★";
  $("callout-title").textContent = status;
  $("callout-body").textContent = data.recommendation || "—";

  const m = data.metadata || {};
  const a = data.activity || {};
  setKpi("kpi-stars", fmtNumber(m.stars));
  setKpi("kpi-forks", fmtNumber(m.forks));
  setKpi("kpi-contrib", fmtNumber(m.contributors));
  setKpi("kpi-issues", fmtNumber(m.open_issues));
  setKpi("kpi-commits", fmtNumber(a.commits_last_90_days));
  setKpi("kpi-close-rate", fmtPercent(a.issue_close_rate));
  setKpi("kpi-pr-rate", fmtPercent(a.pr_merge_rate));
  setKpi("kpi-last-push", fmtDaysAgo(m.days_since_push));

  renderList("highlights-list", data.highlights, "No notable positives detected.");
  renderList("risks-list", data.risks, "No major risks detected.");
  renderChart(a.weekly_commits);
  renderBreakdown(data.breakdown || []);
  renderCategories(data.categories || []);
  renderContributors(data.top_contributors || []);

  scrollTo({ top: report.offsetTop - 60, behavior: "smooth" });
};

const setKpi = (id, value) => {
  const el = $(id);
  if (!el) return;
  el.textContent = value ?? "—";
};

const animateNumber = (el, target, opts = {}) => {
  const duration = 700;
  const start = 0;
  const t0 = performance.now();
  const suffix = opts.suffix ?? "";
  const tick = (now) => {
    const t = Math.min(1, (now - t0) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    const v = Math.round(start + (target - start) * eased);
    el.textContent = `${v}${suffix}`;
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};

const renderList = (id, items, emptyMessage) => {
  const el = $(id);
  if (!items || items.length === 0) {
    el.innerHTML = `<li class="empty">${escapeHtml(emptyMessage)}</li>`;
    return;
  }
  el.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
};

const renderChart = (weekly) => {
  const el = $("commit-chart");
  const note = $("chart-note");
  if (!Array.isArray(weekly) || weekly.length === 0) {
    el.innerHTML = "";
    note.textContent = "Timeline unavailable for this repo.";
    return;
  }
  const totals = weekly.map((w) => w.total || 0);
  const max = Math.max(...totals, 1);
  const peak = totals.indexOf(max);
  el.innerHTML = totals
    .map((v, i) => {
      const h = Math.max(2, Math.round((v / max) * 100));
      const delay = i * 8;
      return `<div class="chart-bar" title="Week ${i + 1}: ${v} commits" style="height:${h}%;animation-delay:${delay}ms"></div>`;
    })
    .join("");
  const total = totals.reduce((a, b) => a + b, 0);
  note.textContent = `${totals.length} weeks • ${fmtNumber(total)} commits total • peak ${max}/wk (week ${peak + 1})`;
};

const renderBreakdown = (breakdown) => {
  const el = $("breakdown-list");
  if (!breakdown || breakdown.length === 0) {
    el.innerHTML = "";
    return;
  }
  const maxContribution = Math.max(...breakdown.map((b) => b.weight * 100));
  el.innerHTML = breakdown
    .map((row) => {
      const pct = Math.round((row.raw || 0) * 100);
      const widthPct = Math.max(2, Math.min(100, (row.contribution / maxContribution) * 100));
      return `
        <div class="bd-row">
          <div class="bd-label" title="${escapeHtml(row.label)} — weight ${(row.weight * 100).toFixed(0)}%">${escapeHtml(row.label)}</div>
          <div class="bd-track"><div class="bd-fill" style="width:${widthPct}%"></div></div>
          <div class="bd-value">${pct}%</div>
        </div>
      `;
    })
    .join("");
  requestAnimationFrame(() => {
    el.querySelectorAll(".bd-fill").forEach((n) => {
      // trigger transition by re-reading the inline style
      const w = n.style.width;
      n.style.width = "0%";
      requestAnimationFrame(() => (n.style.width = w));
    });
  });
};

const renderCategories = (cats) => {
  const el = $("category-list");
  if (!cats || cats.length === 0) {
    el.innerHTML = "";
    return;
  }
  el.innerHTML = cats
    .map((c) => {
      const pct = Math.min(100, Math.max(0, c.percent || 0));
      return `
        <div class="cat-chip">
          <div class="cat-name">${escapeHtml(c.category)}</div>
          <div class="cat-value">${Math.round(c.contribution)} / ${Math.round(c.max)}</div>
          <div class="cat-bar"><span style="width:${pct}%"></span></div>
        </div>
      `;
    })
    .join("");
};

const renderContributors = (list) => {
  const el = $("contributors-list");
  if (!list || list.length === 0) {
    el.innerHTML = '<div class="bullets"><li class="empty">No contributor data available.</li></div>';
    return;
  }
  el.innerHTML = list
    .map((c) => {
      const img = c.avatar_url
        ? `<img class="contrib-avatar" src="${escapeAttr(c.avatar_url)}" alt="" loading="lazy" />`
        : `<div class="contrib-avatar"></div>`;
      const href = c.html_url ? escapeAttr(c.html_url) : "#";
      return `
        <a class="contrib-row" href="${href}" target="_blank" rel="noreferrer">
          ${img}
          <div class="contrib-name">${escapeHtml(c.login)}</div>
          <div class="contrib-count">${fmtNumber(c.contributions)} commits</div>
        </a>
      `;
    })
    .join("");
};

const renderCompare = (reports, errors) => {
  if (!reports || reports.length === 0) {
    compareSection.classList.add("hidden");
    return;
  }
  compareSection.classList.remove("hidden");

  const cardsEl = $("compare-cards");
  cardsEl.innerHTML = reports
    .map((data, idx) => {
      const risk = data.risk_level || "Unknown";
      const rankClass = idx === 0 ? "rank-1" : idx === reports.length - 1 ? "rank-last" : "";
      const rank = idx === 0 ? "Best" : idx === reports.length - 1 && reports.length > 1 ? "Worst" : `#${idx + 1}`;
      return `
        <div class="compare-card ${rankClass}">
          <div class="compare-rank">${rank}</div>
          <div class="repo">${escapeHtml(data.repository)}</div>
          <div class="score">${Math.round(data.score)}</div>
          <div class="status">${escapeHtml(data.status)} • ${escapeHtml(risk)} risk</div>
          <div class="stats">
            <span>★ ${fmtNumber(data.metadata?.stars)}</span>
            <span>⑂ ${fmtNumber(data.metadata?.forks)}</span>
            <span>👥 ${fmtNumber(data.metadata?.contributors)}</span>
            <span>Δ ${fmtNumber(data.activity?.commits_last_90_days)}</span>
          </div>
        </div>
      `;
    })
    .join("");

  const tableEl = $("compare-table");
  tableEl.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Repository</th>
          <th>Score</th>
          <th>Status</th>
          <th>Stars</th>
          <th>Forks</th>
          <th>Contrib</th>
          <th>Commits 90d</th>
          <th>Close rate</th>
          <th>Merge rate</th>
          <th>Last push</th>
        </tr>
      </thead>
      <tbody>
        ${reports
          .map((d) => {
            const m = d.metadata || {};
            const a = d.activity || {};
            return `
              <tr>
                <td class="repo-cell">${escapeHtml(d.repository)}</td>
                <td class="score-cell">${Math.round(d.score)}</td>
                <td>${escapeHtml(d.status)}</td>
                <td>${fmtNumber(m.stars)}</td>
                <td>${fmtNumber(m.forks)}</td>
                <td>${fmtNumber(m.contributors)}</td>
                <td>${fmtNumber(a.commits_last_90_days)}</td>
                <td>${fmtPercent(a.issue_close_rate)}</td>
                <td>${fmtPercent(a.pr_merge_rate)}</td>
                <td>${fmtDaysAgo(m.days_since_push)}</td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
  `;

  if (errors && errors.length > 0) {
    const msg = errors.map((e) => `${e.repo_url}: ${e.error}`).join("\n");
    showToast(`Some repos failed: ${msg}`);
  }
};

const escapeHtml = (s) =>
  String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const escapeAttr = (s) => String(s ?? "").replace(/"/g, "&quot;");

const handleSubmit = async (event) => {
  event.preventDefault();
  const primary = parseRepoInput(repoInput.value);
  const compareUrls = parseCompareList(compareInput.value);

  if (!primary && compareUrls.length === 0) {
    formStatus.textContent = "Enter a repository URL or owner/repo.";
    formStatus.classList.add("error");
    return;
  }

  formStatus.classList.remove("error");
  setLoading(true);
  formStatus.textContent = "Contacting GitHub…";

  try {
    const urls = [primary, ...compareUrls].filter(Boolean);
    const unique = [...new Set(urls)];

    const results = await Promise.allSettled(unique.map(fetchAnalysis));
    const successes = results
      .map((r, i) => ({ r, url: unique[i] }))
      .filter(({ r }) => r.status === "fulfilled")
      .map(({ r }) => r.value);
    const failures = results
      .map((r, i) => ({ r, url: unique[i] }))
      .filter(({ r }) => r.status === "rejected")
      .map(({ r, url }) => ({ repo_url: url, error: (r.reason && r.reason.message) || "Failed" }));

    if (successes.length === 0) {
      const first = failures[0]?.error || "All analyses failed.";
      throw new Error(first);
    }

    if (primary) {
      const primaryKey = normalizeRepoKey(primary);
      const byKey = new Map(successes.map((s) => [s.repository.toLowerCase(), s]));
      const resolved = byKey.get(primaryKey) || successes[0];
      renderSingle(resolved);
    } else {
      report.classList.add("hidden");
    }

    if (successes.length > 1 || (primary && compareUrls.length > 0)) {
      renderCompare(successes.slice().sort((a, b) => b.score - a.score), failures);
    } else {
      compareSection.classList.add("hidden");
    }

    formStatus.textContent = `Analyzed ${successes.length} repository${successes.length === 1 ? "" : "ies"}.`;
    if (failures.length) {
      const first = failures[0];
      showToast(`${failures.length} repo failed: ${first.repo_url} — ${first.error}`);
    }
  } catch (err) {
    formStatus.textContent = err.message || "Something went wrong.";
    formStatus.classList.add("error");
    showToast(err.message || "Analysis failed.");
  } finally {
    setLoading(false);
  }
};

const normalizeRepoKey = (input) => {
  const match = input.match(/github\.com[\/:]+([\w.\-]+)\/([\w.\-]+?)(?:\.git)?\/?$/i);
  if (match) return `${match[1]}/${match[2]}`.toLowerCase();
  if (/^[\w.\-]+\/[\w.\-]+$/.test(input)) return input.toLowerCase();
  return input.toLowerCase();
};

form.addEventListener("submit", handleSubmit);

document.querySelectorAll(".chip[data-example]").forEach((chip) => {
  chip.addEventListener("click", () => {
    repoInput.value = chip.getAttribute("data-example");
    repoInput.focus();
  });
});

repoInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

const updateRateLimit = async () => {
  try {
    const res = await fetch("/api/rate-limit");
    if (!res.ok) return;
    const data = await res.json();
    const el = $("rate-text");
    const dot = document.querySelector(".nav-link.ghost .dot");
    if (!el || !dot) return;
    el.textContent = `API ${data.remaining}`;
    const color =
      data.status === "healthy" ? "var(--good)" : data.status === "warning" ? "var(--warn)" : "var(--bad)";
    dot.style.background = color;
    dot.style.boxShadow = `0 0 8px ${color}`;
  } catch {
    // ignore
  }
};

updateRateLimit();

const ring = $("ring-fg");
if (ring) {
  ring.setAttribute("stroke-dasharray", String(RING_CIRC));
  ring.setAttribute("stroke-dashoffset", String(RING_CIRC));
}
