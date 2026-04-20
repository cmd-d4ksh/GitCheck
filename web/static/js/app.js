const form = document.getElementById("analyze-form");
const repoInput = document.getElementById("repo-url");
const statusEl = document.getElementById("form-status");
const compareInput = document.getElementById("repo-compare");
const meterValue = document.getElementById("meter-value");
const meterLabel = document.getElementById("meter-label");
const meterRing = document.querySelector(".meter-ring");
const repoName = document.getElementById("repo-name");
const recommendation = document.getElementById("recommendation");
const signals = document.getElementById("signals");
const warnings = document.getElementById("warnings");
const compareGrid = document.getElementById("compare-grid");
const compareTable = document.getElementById("compare-table");
const compareSection = document.getElementById("compare");
const summaryBoard = document.getElementById("summary-board");
const dashboardSection = document.getElementById("dashboard");
const timelineSection = document.getElementById("timeline");
const explainSection = document.getElementById("explain");
const compareTableSection = document.getElementById("compare-table-section");
const watchlistSection = document.getElementById("watchlist");
const watchlistGrid = document.getElementById("watchlist-grid");
const watchlistSave = document.getElementById("watchlist-save");
const watchlistRefresh = document.getElementById("watchlist-refresh");
const shareReport = document.getElementById("share-report");
const weightsEl = document.getElementById("weights");
const thresholdsEl = document.getElementById("thresholds");
const contributionsEl = document.getElementById("contributions");
const timelineBars = document.getElementById("timeline-bars");
const timelineNote = document.getElementById("timeline-note");
const dashStars = document.getElementById("dash-stars");
const dashForks = document.getElementById("dash-forks");
const dashContrib = document.getElementById("dash-contrib");
const dashIssues = document.getElementById("dash-issues");
const dashCommits = document.getElementById("dash-commits");
const dashCloseRate = document.getElementById("dash-close-rate");
const dashIssuesBar = document.getElementById("dash-issues-bar");
const dashCommitsSpark = document.getElementById("dash-commits-spark");
const dashSecurity = document.getElementById("dash-security");
const dashLicense = document.getElementById("dash-license");
const grid = document.querySelector(".bg-grid");
const summaryDecision = document.getElementById("summary-decision");
const summaryRisk = document.getElementById("summary-risk");
const summaryMeta = document.getElementById("summary-meta");
const summaryHighlights = document.getElementById("summary-highlights");
const summaryRisks = document.getElementById("summary-risks");

const clampTo99 = (value) => Math.max(0, Math.min(99, Math.round(value)));
const formatPercent = (value) => (value === 0 ? "0%" : value ? `${Math.round(value * 100)}%` : "—");
const joinLines = (items) => items.filter(Boolean).join("\n");
const WATCHLIST_KEY = "gitcheck_watchlist";
const HISTORY_KEY = "gitcheck_history";

const getWatchlist = () => {
  try {
    return JSON.parse(localStorage.getItem(WATCHLIST_KEY) || "[]");
  } catch {
    return [];
  }
};

const setWatchlist = (list) => {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
};

const getHistory = () => {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "{}");
  } catch {
    return {};
  }
};

const setHistory = (history) => {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
};

const updateHistory = (repo, score) => {
  const history = getHistory();
  const list = history[repo] || [];
  list.push({ ts: Date.now(), score });
  history[repo] = list.slice(-12);
  setHistory(history);
};

const renderWatchlist = () => {
  const list = getWatchlist();
  const history = getHistory();
  if (!list.length) {
    watchlistGrid.innerHTML = "<div class=\"summary-value\">No saved repos yet.</div>";
    return;
  }

  watchlistGrid.innerHTML = list
    .map((item) => {
      const entries = history[item.repo] || [];
      const last = entries[entries.length - 1];
      const score = last ? `${clampTo99(last.score)}%` : "—";
      const sparkMax = Math.max(...entries.map((e) => e.score || 0), 1);
      const spark = entries
        .map((e) => {
          const height = Math.max(6, Math.round(((e.score || 0) / sparkMax) * 100));
          return `<div class="spark-bar" style="height:${height}%;"></div>`;
        })
        .join("");

      return `
        <div class="watch-card">
          <div class="watch-title">${item.repo}</div>
          <div class="compare-score">${score}</div>
          <div class="watch-meta">Maturity: ${item.maturity || "—"}\nLast updated: ${item.updated || "—"}</div>
          <div class="watch-spark">${spark || ""}</div>
        </div>
      `;
    })
    .join("");
};

const setRiskTheme = (riskLevel) => {
  const root = document.documentElement;
  let color = "#d9a441";
  if (riskLevel === "Low") color = "#1f7a5a";
  if (riskLevel === "High") color = "#a53d2a";
  root.style.setProperty("--risk-color", color);
  root.style.setProperty(
    "--risk-glow",
    riskLevel === "Low"
      ? "rgba(31, 122, 90, 0.18)"
      : riskLevel === "High"
      ? "rgba(165, 61, 42, 0.2)"
      : "rgba(217, 164, 65, 0.18)"
  );

  document.body.classList.remove("risk-low", "risk-medium", "risk-high");
  if (riskLevel === "Low") document.body.classList.add("risk-low");
  if (riskLevel === "Medium") document.body.classList.add("risk-medium");
  if (riskLevel === "High") document.body.classList.add("risk-high");
};

const setMeter = (value, riskLevel) => {
  const percent = clampTo99(value);
  const degrees = Math.round((percent / 99) * 360);

  meterValue.textContent = `${percent}%`;
  meterLabel.textContent = riskLevel ? `${riskLevel} risk` : "Trust Meter";

  setRiskTheme(riskLevel);
  const color = getComputedStyle(document.documentElement).getPropertyValue("--risk-color") || "#d9a441";
  meterRing.style.background = `conic-gradient(${color} 0deg, ${color} ${degrees}deg, #f1ece6 ${degrees}deg)`;
};

const renderSignals = (data) => {
  const features = data.features || {};
  const metadata = data.metadata || {};

  return `Commits: ${features.commit_score ?? "-"} | Contributors: ${features.contributor_score ?? "-"} | Issues: ${features.issue_score ?? "-"}\nStars: ${metadata.stars ?? "-"} | Forks: ${metadata.forks ?? "-"}`;
};

const fetchAnalysis = async (repoUrl) => {
  const response = await fetch(`/analyze?repo_url=${encodeURIComponent(repoUrl)}`, {
    method: "POST"
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
};

const renderCompareCard = (data, rankLabel) => {
  const score = data.rule_based_analysis?.trust_score ?? 0;
  const risk = data.rule_based_analysis?.risk_level || "Unknown";
  const percent = clampTo99(score);
  const metadata = data.metadata || {};

  return `
    <div class="compare-card">
      <div class="compare-badge">${rankLabel}</div>
      <div class="compare-repo">${data.repository || "—"}</div>
      <div class="compare-score">${percent}%</div>
      <div class="compare-risk">${risk} risk</div>
      <div class="compare-stats">
        <span>Stars ${metadata.stars ?? "-"}</span>
        <span>Forks ${metadata.forks ?? "-"}</span>
        <span>Contrib ${metadata.contributors ?? "-"}</span>
      </div>
      <div class="compare-metrics">${renderSignals(data)}</div>
    </div>
  `;
};

const parseRepoFromUrl = (url) => {
  try {
    const parts = url.replace(/\/+$/, "").split("/");
    const repo = parts.pop();
    const owner = parts.pop();
    if (!owner || !repo) return null;
    return `${owner}/${repo}`;
  } catch {
    return null;
  }
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const repoUrl = repoInput.value.trim();
  const compareUrlsRaw = compareInput.value.trim();
  const compareUrls = compareUrlsRaw
    ? compareUrlsRaw.split("\n").map((line) => line.trim()).filter(Boolean).slice(0, 3)
    : [];

  if (!repoUrl && compareUrls.length === 0) {
    statusEl.textContent = "Enter a primary URL or up to 3 compare URLs.";
    return;
  }

  statusEl.textContent = "Analyzing...";
  recommendation.textContent = "—";
  warnings.textContent = "—";
  signals.textContent = "—";
  compareGrid.innerHTML = "";
  compareTable.innerHTML = "";
  weightsEl.textContent = "—";
  thresholdsEl.textContent = "—";
  contributionsEl.textContent = "—";
  timelineBars.innerHTML = "";
  timelineNote.textContent = "—";
  summaryDecision.textContent = "—";
  summaryRisk.textContent = "—";
  summaryRisk.className = "summary-risk";
  summaryMeta.textContent = "—";
  summaryHighlights.textContent = "—";
  summaryRisks.textContent = "—";
  dashStars.textContent = "—";
  dashForks.textContent = "—";
  dashContrib.textContent = "—";
  dashIssues.textContent = "—";
  dashCommits.textContent = "—";
  dashCloseRate.textContent = "—";
  dashIssuesBar.style.width = "0%";
  dashCommitsSpark.innerHTML = "";
  dashSecurity.textContent = "—";
  dashLicense.textContent = "License: —";
  compareSection.classList.add("is-hidden");
  summaryBoard.classList.add("is-hidden");
  dashboardSection.classList.add("is-hidden");
  timelineSection.classList.add("is-hidden");
  explainSection.classList.add("is-hidden");
  compareTableSection.classList.add("is-hidden");
  watchlistSection.classList.add("is-hidden");

  try {
    const allUrls = [repoUrl, ...compareUrls].filter(Boolean);
    const uniqueUrls = [...new Set(allUrls)];
    const results = await Promise.all(uniqueUrls.map(fetchAnalysis));
    const resultMap = new Map(results.map((item) => [item.repository, item]));
    const resolveResult = (url) => {
      const repoKey = parseRepoFromUrl(url);
      return resultMap.get(repoKey) || results[0];
    };

    if (allUrls.length > 0) {
      const dataList = allUrls.map((url) => resolveResult(url));
      const ranked = dataList
        .map((data) => ({
          data,
          score: clampTo99(data.rule_based_analysis?.trust_score ?? 0)
        }))
        .sort((a, b) => b.score - a.score);

      const best = ranked[0]?.data;
      if (best) {
        const data = best;
      const score = data.rule_based_analysis?.trust_score ?? 0;
      const risk = data.rule_based_analysis?.risk_level || "Unknown";
      const metadata = data.metadata || {};
      const activity = data.activity || {};
      const security = data.security || {};

      setMeter(score, risk);
      repoName.textContent = data.repository || "—";
      recommendation.textContent = data.recommendation || "—";
      signals.textContent = renderSignals(data);
      warnings.textContent = data.warnings ? data.warnings.join(" | ") : "None";
      dashStars.textContent = metadata.stars ?? "—";
      dashForks.textContent = metadata.forks ?? "—";
      dashContrib.textContent = metadata.contributors ?? "—";
      dashIssues.textContent = metadata.open_issues ?? "—";
      dashCommits.textContent = activity.commits_last_90_days ?? "—";
      dashCloseRate.textContent = formatPercent(activity.issue_close_rate);
      const issueCap = 500;
      const issueWidth = Math.min(100, Math.round(((metadata.open_issues || 0) / issueCap) * 100));
      dashIssuesBar.style.width = `${issueWidth}%`;

      const securityBadges = [
        security.security_policy ? "Security Policy" : null,
        security.dependabot ? "Dependabot" : null,
        security.code_scanning ? "Code Scanning" : null
      ].filter(Boolean);
      dashSecurity.textContent = securityBadges.length ? securityBadges.join(" • ") : "No security signals detected";
      const licenseInfo = security.license || {};
      const spdx = licenseInfo.spdx_id || licenseInfo.key || "Unknown";
      const osi = security.license_osi_approved ? "OSI-approved" : "Not OSI-approved";
      dashLicense.textContent = `License: ${spdx} • ${osi}`;

      const decisionText =
        risk === "Low"
          ? "Safe to adopt"
          : risk === "Medium"
          ? "Adopt with monitoring"
          : "Use with caution";
      summaryDecision.textContent = decisionText;
      summaryRisk.textContent = `${risk} risk`;
      summaryRisk.className = `summary-risk ${risk.toLowerCase()}`;
      summaryMeta.textContent = `Trust score: ${clampTo99(score)}%\nRepo: ${data.repository || "—"}`;
      summaryMeta.textContent += `\nMaturity: ${data.maturity || "—"}`;

      const highlightItems = [
        metadata.stars >= 1000 ? "Strong community adoption (1k+ stars)" : null,
        metadata.forks >= 200 ? "Healthy fork activity (200+ forks)" : null,
        (activity.commits_last_90_days || 0) >= 50 ? "Active development in last 90 days" : null,
        (activity.issue_close_rate || 0) >= 0.6 ? "Solid issue responsiveness" : null
      ];

      const riskItems = [
        (activity.commits_last_90_days || 0) < 10 ? "Low recent commit activity" : null,
        (activity.issue_close_rate || 0) < 0.4 ? "Slow issue closure" : null,
        metadata.open_issues >= 200 ? "Large open issue backlog" : null,
        metadata.contributors <= 2 ? "Low contributor diversity" : null,
        data.warnings && data.warnings.length ? data.warnings.join(" | ") : null
      ];

      summaryHighlights.textContent = joinLines(highlightItems) || "No major positives detected.";
      summaryRisks.textContent = joinLines(riskItems) || "No major risks detected.";

      const explanation = data.explanation || {};
      const weights = explanation.weights || {};
      const thresholds = explanation.thresholds || {};
      const contributions = explanation.contributions || {};

      weightsEl.textContent = `Commits: ${weights.commit_score ?? "-"}\nIssues: ${weights.issue_score ?? "-"}\nContributors: ${weights.contributor_score ?? "-"}\nStars: ${weights.star_score ?? "-"}\nForks: ${weights.fork_score ?? "-"}`;
      thresholdsEl.textContent = `Low risk: ${thresholds.low_risk_min ?? "-"}+\nMedium risk: ${thresholds.medium_risk_min ?? "-"}+\nHigh risk: below ${thresholds.medium_risk_min ?? "-"}`;
      contributionsEl.textContent = `Commits: ${contributions.commit ?? "-"}\nIssues: ${contributions.issues ?? "-"}\nContributors: ${contributions.contributors ?? "-"}\nStars: ${contributions.stars ?? "-"}\nForks: ${contributions.forks ?? "-"}`;

      const weekly = data.timeline?.weekly_commits;
      if (Array.isArray(weekly) && weekly.length > 0) {
        const lastWeeks = weekly.slice(-52);
        const totals = lastWeeks.map((item) => item.total || 0);
        const max = Math.max(...totals, 1);
        timelineBars.innerHTML = totals
          .map((value) => {
            const height = Math.round((value / max) * 100);
            return `<div class="timeline-bar" style="height:${height}%;"></div>`;
          })
          .join("");
        timelineNote.textContent = `Showing ${lastWeeks.length} weeks. Peak weekly commits: ${max}.`;

        const sparkWeeks = lastWeeks.slice(-20);
        dashCommitsSpark.innerHTML = sparkWeeks
          .map((item) => {
            const height = Math.max(8, Math.round(((item.total || 0) / max) * 100));
            return `<div class="spark-bar" style="height:${height}%;"></div>`;
          })
          .join("");
      } else {
        timelineNote.textContent = "Timeline not available yet. Try again in a minute.";
        dashCommitsSpark.innerHTML = "";
      }
      }
    }

    if (allUrls.length > 0) {
      const dataList = allUrls.map((url) => resolveResult(url));
      const ranked = dataList
        .map((data) => ({
          data,
          score: clampTo99(data.rule_based_analysis?.trust_score ?? 0)
        }))
        .sort((a, b) => b.score - a.score);
      const labels =
        ranked.length === 1
          ? ["Best"]
          : ranked.length === 2
          ? ["Best", "Worst"]
          : ["Best", "Mid", "Worst"];

      compareGrid.innerHTML = ranked
        .map((item, idx) => renderCompareCard(item.data, labels[idx] || ""))
        .join("");

      compareTable.innerHTML = [
        `<div class="compare-row header">
          <div>Repo</div>
          <div>Score</div>
          <div class="col-hide">Stars</div>
          <div class="col-hide">Forks</div>
          <div class="col-hide">Contrib</div>
          <div class="col-hide">Issues</div>
          <div class="col-hide">Commits</div>
        </div>`,
        ...ranked.map(({ data }) => {
          const metadata = data.metadata || {};
          const activity = data.activity || {};
          const score = clampTo99(data.rule_based_analysis?.trust_score ?? 0);
          return `<div class="compare-row">
            <div>${data.repository || "—"}</div>
            <div>${score}%</div>
            <div class="col-hide">${metadata.stars ?? "-"}</div>
            <div class="col-hide">${metadata.forks ?? "-"}</div>
            <div class="col-hide">${metadata.contributors ?? "-"}</div>
            <div class="col-hide">${metadata.open_issues ?? "-"}</div>
            <div class="col-hide">${activity.commits_last_90_days ?? "-"}</div>
          </div>`;
        })
      ].join("");

      compareSection.classList.remove("is-hidden");
      summaryBoard.classList.remove("is-hidden");
      dashboardSection.classList.remove("is-hidden");
      timelineSection.classList.remove("is-hidden");
      explainSection.classList.remove("is-hidden");
      compareTableSection.classList.remove("is-hidden");
      watchlistSection.classList.remove("is-hidden");

      ranked.forEach(({ data, score }) => {
        if (data.repository) updateHistory(data.repository, score);
      });
      renderWatchlist();
    }

    statusEl.textContent = "Done.";
  } catch (err) {
    statusEl.textContent = err.message;
    setMeter(0, "High");
    repoName.textContent = "—";
  }
});

setMeter(0, "");

shareReport?.addEventListener("click", async () => {
  const repo = repoName.textContent?.trim();
  if (!repo || repo === "—") return;
  const url = `${window.location.origin}/report/${repo}`;
  try {
    await navigator.clipboard.writeText(url);
    shareReport.textContent = "Copied";
  } catch {
    shareReport.textContent = "Copy failed";
  }
  setTimeout(() => {
    shareReport.textContent = "Share Report";
  }, 1400);
});

watchlistSave?.addEventListener("click", () => {
  const repo = repoName.textContent?.trim();
  if (!repo || repo === "—") return;
  const list = getWatchlist();
  if (!list.find((item) => item.repo === repo)) {
    const maturity = summaryMeta.textContent?.includes("Maturity:")
      ? summaryMeta.textContent.split("Maturity:")[1]?.trim()
      : "—";
    list.push({ repo, maturity, updated: new Date().toLocaleString() });
    setWatchlist(list);
  }
  renderWatchlist();
});

watchlistRefresh?.addEventListener("click", async () => {
  const list = getWatchlist();
  if (!list.length) return;
  watchlistRefresh.textContent = "Refreshing...";
  try {
    const results = await Promise.all(list.map((item) => fetchAnalysis(`https://github.com/${item.repo}`)));
    const now = new Date().toLocaleString();
    const updatedList = list.map((item, idx) => ({
      ...item,
      maturity: results[idx]?.maturity || item.maturity,
      updated: now
    }));
    setWatchlist(updatedList);
    results.forEach((data) => {
      const score = clampTo99(data.rule_based_analysis?.trust_score ?? 0);
      updateHistory(data.repository, score);
    });
  } catch {
    // ignore refresh errors
  } finally {
    watchlistRefresh.textContent = "Refresh All";
    renderWatchlist();
  }
});

const bootReport = () => {
  const path = window.location.pathname;
  if (!path.startsWith("/report/")) return;
  const parts = path.replace("/report/", "").split("/");
  if (parts.length < 2) return;
  const repo = `${parts[0]}/${parts[1]}`;
  repoInput.value = `https://github.com/${repo}`;
  form.dispatchEvent(new Event("submit", { cancelable: true }));
};

bootReport();
renderWatchlist();

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    });
  },
  { threshold: 0.15 }
);

document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

window.addEventListener("mousemove", (event) => {
  if (!grid) return;
  const { innerWidth, innerHeight } = window;
  const x = (event.clientX / innerWidth - 0.5) * 8;
  const y = (event.clientY / innerHeight - 0.5) * 8;
  grid.style.transform = `translate(${x}px, ${y}px)`;
});
