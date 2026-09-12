// PAIMANA AI - Master Application Controller
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

let currentProjects = [];
let uploadPreviewData = null;
let selectedFile = null;

async function initApp() {
  setupNavigation();
  setupEventListeners();
  await loadDashboardData();
  await populateFilterDropdowns();
}

// ----------------------------------------------------
// Navigation Tab Handler
// ----------------------------------------------------
function setupNavigation() {
  const tabs = document.querySelectorAll(".nav-tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const targetId = tab.dataset.target;
      document.querySelectorAll(".tab-view").forEach(view => {
        view.style.display = "none";
      });

      const targetView = document.getElementById(targetId);
      if (targetView) {
        targetView.style.display = "block";
      }

      // Refresh view-specific content
      if (targetId === "view-projects") {
        loadProjectsExplorer();
      } else if (targetId === "view-warnings") {
        loadEarlyWarnings();
      } else if (targetId === "view-anomalies") {
        loadAnomalies();
      } else if (targetId === "view-analytics") {
        loadAnalyticsView();
      } else if (targetId === "view-dashboard") {
        loadDashboardData();
      }
    });
  });

  document.getElementById("btn-goto-warnings")?.addEventListener("click", () => {
    document.querySelector('[data-target="view-warnings"]')?.click();
  });
}

// ----------------------------------------------------
// Event Listeners
// ----------------------------------------------------
function setupEventListeners() {
  // Reset Demo
  document.getElementById("btn-reset-demo")?.addEventListener("click", async () => {
    if (confirm("Reset dataset back to standard 40+ prototype synthetic records?")) {
      await PaimanaAPI.resetDemo();
      await loadDashboardData();
      await populateFilterDropdowns();
      alert("Database reset to demo state successfully.");
    }
  });

  // Quick Manual Project button in header
  document.getElementById("btn-quick-new-project")?.addEventListener("click", () => {
    document.querySelector('[data-target="view-upload"]')?.click();
    document.querySelector('input[name="project_id"]')?.focus();
  });

  // Filters in Explorer
  ["filter-search", "filter-ministry", "filter-sector", "filter-state", "filter-risk", "filter-sort"].forEach(id => {
    document.getElementById(id)?.addEventListener("change", loadProjectsExplorer);
  });
  document.getElementById("filter-search")?.addEventListener("input", debounce(loadProjectsExplorer, 300));

  document.getElementById("btn-reset-filters")?.addEventListener("click", () => {
    document.getElementById("filter-search").value = "";
    document.getElementById("filter-ministry").value = "All";
    document.getElementById("filter-sector").value = "All";
    document.getElementById("filter-state").value = "All";
    document.getElementById("filter-risk").value = "All";
    document.getElementById("filter-sort").value = "priority_rank";
    loadProjectsExplorer();
  });

  // Export buttons
  document.getElementById("btn-export-reports")?.addEventListener("click", () => {
    window.location.href = "/api/export/csv";
  });
  document.getElementById("btn-export-projects-csv")?.addEventListener("click", () => {
    window.location.href = "/api/export/csv";
  });
  document.getElementById("btn-export-projects-xlsx")?.addEventListener("click", () => {
    window.location.href = "/api/export/xlsx";
  });

  // Modal close
  document.getElementById("btn-close-project-modal")?.addEventListener("click", closeModal);
  document.getElementById("btn-modal-close-footer")?.addEventListener("click", closeModal);

  // Manual Project Form
  document.getElementById("form-manual-project")?.addEventListener("submit", handleManualProjectSubmit);

  // File Upload Handlers
  document.getElementById("btn-choose-file")?.addEventListener("click", () => {
    document.getElementById("file-upload-input")?.click();
  });
  document.getElementById("file-upload-input")?.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      selectedFile = e.target.files[0];
      document.getElementById("selected-file-label").textContent = `Selected: ${selectedFile.name} (${(selectedFile.size/1024).toFixed(1)} KB)`;
      document.getElementById("btn-validate-upload").disabled = false;
    }
  });

  document.getElementById("btn-validate-upload")?.addEventListener("click", handleFileValidate);
  document.getElementById("btn-process-dataset")?.addEventListener("click", handleFileCommit);
  document.getElementById("btn-download-sample-csv")?.addEventListener("click", () => {
    window.location.href = "/api/export/csv";
  });

  // AI Assistant Handlers
  document.getElementById("btn-send-ai-query")?.addEventListener("click", handleAssistantQuery);
  document.getElementById("ai-query-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAssistantQuery();
  });

  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      document.getElementById("ai-query-input").value = chip.dataset.query;
      handleAssistantQuery();
    });
  });

  // Warning Severity Filter
  document.querySelectorAll(".filter-warn-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-warn-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadEarlyWarnings(btn.dataset.sev);
    });
  });
}

// ----------------------------------------------------
// 1. Dashboard Loader
// ----------------------------------------------------
async function loadDashboardData() {
  try {
    const kpis = await PaimanaAPI.getDashboardKPIs();
    document.getElementById("kpi-total-projects").textContent = kpis.total_projects;
    document.getElementById("kpi-crit-projects").textContent = kpis.critical_risk_count;
    document.getElementById("kpi-high-projects").textContent = kpis.high_risk_count;
    document.getElementById("kpi-total-warnings").textContent = kpis.total_warnings;
    document.getElementById("kpi-total-anomalies").textContent = kpis.total_anomalies;
    document.getElementById("kpi-avg-risk").textContent = `${kpis.avg_risk_score} / 100`;
    document.getElementById("kpi-cost-monitored").textContent = `Sanctioned: ₹${kpis.total_revised_cost.toLocaleString()} Cr`;

    document.getElementById("nav-warning-badge").textContent = kpis.total_warnings;
    document.getElementById("nav-anomaly-badge").textContent = kpis.total_anomalies;

    // Load Charts
    const charts = await PaimanaAPI.getDashboardCharts();
    PaimanaCharts.renderRiskDistribution("chart-risk-distribution", charts.risk_distribution);
    PaimanaCharts.renderSectorRisk("chart-sector-risk", charts.sector_risk);
    PaimanaCharts.renderCostVsProgress("chart-cost-vs-progress", charts.cost_vs_progress);

    // State table
    renderStateRiskTable(charts.state_risk);

    // Priority Attention Queue (top 6)
    const priorityQueue = await PaimanaAPI.getPriorityQueue(6);
    renderAttentionQueue(priorityQueue);

    // Recent critical warnings
    const warnings = await PaimanaAPI.getWarnings("Critical");
    renderRecentWarnings(warnings.slice(0, 5));
  } catch (err) {
    console.error("Failed loading dashboard:", err);
  }
}

function renderAttentionQueue(projects) {
  const tbody = document.querySelector("#table-attention-queue tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  projects.forEach((p, idx) => {
    const risk = p.risk_report;
    const catClass = risk.risk_category.toLowerCase();
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 700; text-align: center;">#${p.priority_rank || (idx + 1)}</td>
      <td>
        <div style="font-weight: 600; color: var(--gov-navy);">${escapeHtml(p.project_name)}</div>
        <div style="font-size: 11px; color: var(--text-light);">${escapeHtml(p.project_id)} • ${escapeHtml(p.state)}</div>
      </td>
      <td>${escapeHtml(p.ministry.replace("Ministry of ", ""))}</td>
      <td>${escapeHtml(p.sector)}</td>
      <td style="text-align: right; font-weight: 600;">₹${p.revised_cost.toLocaleString()}</td>
      <td><span class="badge-risk ${catClass}">${risk.risk_category}</span></td>
      <td style="text-align: right; font-weight: 700;">${risk.overall_risk_score}</td>
      <td>
        <button class="btn btn-outline" style="padding: 3px 8px; font-size: 11px;" onclick="openProjectDrillDown('${p.project_id}')">Inspect</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderStateRiskTable(states) {
  const tbody = document.querySelector("#table-state-risk tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  states.slice(0, 8).forEach(st => {
    let cat = "Low";
    if (st.avg_risk > 80) cat = "Critical";
    else if (st.avg_risk > 60) cat = "High";
    else if (st.avg_risk > 30) cat = "Medium";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 600;">${escapeHtml(st.state)}</td>
      <td style="text-align: center;">${st.count}</td>
      <td style="text-align: center; font-weight: 700;">${st.avg_risk}</td>
      <td><span class="badge-risk ${cat.toLowerCase()}">${cat}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderRecentWarnings(warnings) {
  const tbody = document.querySelector("#table-recent-warnings tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (warnings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: var(--text-light); padding: 12px;">No active critical warnings.</td></tr>`;
    return;
  }

  warnings.forEach(w => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div style="font-weight: 600;">${escapeHtml(w.project_name)}</div>
        <div style="font-size: 10px; color: var(--text-light);">${w.project_id}</div>
      </td>
      <td style="font-size: 11px;">
        <div style="font-weight: 600; color: var(--risk-crit);">${escapeHtml(w.warning_type)}</div>
        <div style="color: var(--text-muted); font-size: 10px;">${escapeHtml(w.triggering_indicator)}</div>
      </td>
      <td><span class="badge-risk ${w.severity.toLowerCase()}">${w.severity}</span></td>
      <td>
        <button class="btn btn-outline" style="padding: 2px 6px; font-size: 10px;" onclick="openProjectDrillDown('${w.project_id}')">View</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------------------------------------------
// 2. Project Explorer
// ----------------------------------------------------
async function populateFilterDropdowns() {
  const projects = await PaimanaAPI.getProjects();
  currentProjects = projects;

  const ministries = new Set();
  const sectors = new Set();
  const states = new Set();

  projects.forEach(p => {
    if (p.ministry) ministries.add(p.ministry);
    if (p.sector) sectors.add(p.sector);
    if (p.state) states.add(p.state);
  });

  populateSelect("filter-ministry", Array.from(ministries).sort());
  populateSelect("filter-sector", Array.from(sectors).sort());
  populateSelect("filter-state", Array.from(states).sort());
}

function populateSelect(id, items) {
  const sel = document.getElementById(id);
  if (!sel) return;
  const currentVal = sel.value;
  sel.innerHTML = `<option value="All">All ${id.replace("filter-", "").replace(/^\w/, c => c.toUpperCase())}s</option>`;
  items.forEach(item => {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    sel.appendChild(opt);
  });
  if (currentVal && items.includes(currentVal)) {
    sel.value = currentVal;
  }
}

async function loadProjectsExplorer() {
  const params = {
    search: document.getElementById("filter-search")?.value || "",
    ministry: document.getElementById("filter-ministry")?.value || "All",
    sector: document.getElementById("filter-sector")?.value || "All",
    state: document.getElementById("filter-state")?.value || "All",
    risk_category: document.getElementById("filter-risk")?.value || "All",
    sort_by: document.getElementById("filter-sort")?.value || "priority_rank"
  };

  const projects = await PaimanaAPI.getProjects(params);
  const tbody = document.querySelector("#table-project-explorer tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (projects.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 20px; color: var(--text-muted);">No projects matching current filter criteria.</td></tr>`;
    return;
  }

  projects.forEach(p => {
    const risk = p.risk_report;
    const catClass = risk.risk_category.toLowerCase();
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: monospace; font-weight: 600;">${escapeHtml(p.project_id)}</td>
      <td style="font-weight: 600; color: var(--gov-navy); max-width: 250px;">${escapeHtml(p.project_name)}</td>
      <td>${escapeHtml(p.ministry.replace("Ministry of ", ""))}</td>
      <td>${escapeHtml(p.sector)}</td>
      <td>${escapeHtml(p.state)}</td>
      <td style="text-align: right; font-weight: 600;">₹${p.original_cost.toLocaleString()}</td>
      <td style="text-align: right;">₹${p.expenditure.toLocaleString()}</td>
      <td style="text-align: center;">
        <span style="font-weight: 600;">${p.physical_progress}%</span>
        <div class="score-bar-bg" style="height: 4px; margin-top: 3px;">
          <div class="score-bar-fill" style="width: ${p.physical_progress}%; background-color: #2563eb;"></div>
        </div>
      </td>
      <td style="text-align: center; font-weight: 700; font-size: 13px;">${risk.overall_risk_score}</td>
      <td style="text-align: center;"><span class="badge-risk ${catClass}">${risk.risk_category}</span></td>
      <td style="text-align: center; white-space: nowrap;">
        <button class="btn btn-outline" style="padding: 3px 8px; font-size: 11px;" onclick="openProjectDrillDown('${p.project_id}')">Drill-Down</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------------------------------------------
// 3. Project Drill-Down & What-If Modal
// ----------------------------------------------------
window.openProjectDrillDown = async function(projectId) {
  try {
    const data = await PaimanaAPI.getProjectDetail(projectId);
    const p = data.project;
    const ind = data.derived_indicators;
    const risk = data.risk_report;
    const warnings = data.warnings || [];
    const recs = data.recommendations || [];

    document.getElementById("modal-project-title").textContent = `${p.project_name} (${p.project_id})`;

    const modalBody = document.getElementById("modal-project-body");
    modalBody.innerHTML = `
      <!-- Metadata Strip -->
      <div style="background-color: #f8fafc; border: 1px solid var(--gov-border); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 16px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; font-size: 12px;">
        <div>
          <span style="color: var(--text-light); font-size: 11px; display: block;">Ministry & Sector</span>
          <strong>${escapeHtml(p.ministry)}</strong><br>
          <span style="color: var(--text-muted);">${escapeHtml(p.sector)} • ${escapeHtml(p.state)}</span>
        </div>
        <div>
          <span style="color: var(--text-light); font-size: 11px; display: block;">Approved & Revised Cost</span>
          <strong>₹${p.original_cost.toLocaleString()} Cr</strong> → <strong>₹${p.revised_cost.toLocaleString()} Cr</strong><br>
          <span style="color: ${ind.cost_variance_pct > 0 ? 'var(--risk-high)' : 'var(--risk-low)'}; font-weight: 600;">
            ${ind.cost_variance_pct > 0 ? '+' : ''}${ind.cost_variance_pct}% Cost Variance
          </span>
        </div>
        <div>
          <span style="color: var(--text-light); font-size: 11px; display: block;">Expenditure & Gap</span>
          <strong>₹${p.expenditure.toLocaleString()} Cr</strong> (${(ind.expenditure_ratio*100).toFixed(1)}% of Budget)<br>
          <span style="color: var(--text-muted);">Fin - Phys Gap: <strong>+${ind.progress_gap}%</strong></span>
        </div>
        <div>
          <span style="color: var(--text-light); font-size: 11px; display: block;">Timeline & Target</span>
          <span>Target: <strong>${p.expected_completion_date}</strong></span><br>
          <span style="color: ${ind.schedule_variance_months > 0 ? 'var(--risk-crit)' : 'var(--risk-low)'}; font-weight: 600;">
            ${ind.schedule_variance_months > 0 ? `+${ind.schedule_variance_months} mo delay` : 'On Schedule'}
          </span>
        </div>
      </div>

      <!-- Project Health & Risk Section -->
      <div style="margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
          <h3 style="font-size: 14px; font-weight: 700; color: var(--gov-navy-dark);">Project Health & Risk Evaluation</h3>
          <div>
            <span style="font-size: 12px; color: var(--text-muted);">Overall Risk Score:</span>
            <span style="font-size: 18px; font-weight: 800; color: ${risk.overall_risk_score >= 81 ? 'var(--risk-crit)' : (risk.overall_risk_score >= 61 ? 'var(--risk-high)' : (risk.overall_risk_score >= 31 ? 'var(--risk-med)' : 'var(--risk-low)'))};">
              ${risk.overall_risk_score} / 100
            </span>
            <span class="badge-risk ${risk.risk_category.toLowerCase()}" style="margin-left: 6px;">${risk.risk_category} Risk</span>
          </div>
        </div>

        <!-- 4 Component Score Bars -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #ffffff; border: 1px solid var(--gov-border-light); padding: 12px; border-radius: var(--radius-sm);">
          <div class="score-progress-wrapper">
            <div class="score-meta">
              <span>Cost Risk (25% weight)</span>
              <span><strong>${risk.cost_risk}</strong> / 100</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: ${risk.cost_risk}%; background-color: ${getRiskBarColor(risk.cost_risk)};"></div>
            </div>
          </div>

          <div class="score-progress-wrapper">
            <div class="score-meta">
              <span>Schedule Risk (30% weight)</span>
              <span><strong>${risk.schedule_risk}</strong> / 100</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: ${risk.schedule_risk}%; background-color: ${getRiskBarColor(risk.schedule_risk)};"></div>
            </div>
          </div>

          <div class="score-progress-wrapper">
            <div class="score-meta">
              <span>Progress Risk (25% weight)</span>
              <span><strong>${risk.progress_risk}</strong> / 100</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: ${risk.progress_risk}%; background-color: ${getRiskBarColor(risk.progress_risk)};"></div>
            </div>
          </div>

          <div class="score-progress-wrapper">
            <div class="score-meta">
              <span>Financial Risk (20% weight)</span>
              <span><strong>${risk.financial_risk}</strong> / 100</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: ${risk.financial_risk}%; background-color: ${getRiskBarColor(risk.financial_risk)};"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Why Is This Project At Risk? (Explainable AI) -->
      <div style="margin-bottom: 18px;">
        <h3 style="font-size: 13px; font-weight: 700; color: var(--gov-navy-dark); margin-bottom: 6px;">Why Is This Project At Risk?</h3>
        <p style="font-size: 12px; color: var(--text-main); background: #f8fafc; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid var(--gov-border-light); margin-bottom: 8px;">
          ${escapeHtml(risk.explanation)}
        </p>

        <div style="font-size: 12px;">
          <strong style="color: var(--text-muted); font-size: 11px; text-transform: uppercase;">Top Contributing Factors:</strong>
          <ol style="margin-left: 18px; margin-top: 4px; display: flex; flex-direction: column; gap: 4px;">
            ${risk.top_factors && risk.top_factors.length > 0 ? 
              risk.top_factors.map(f => `<li><strong>[${f.dimension}]</strong> ${escapeHtml(f.factor)}</li>`).join("") :
              `<li>No critical risk drivers detected. Project progress within standard tolerance bands.</li>`
            }
          </ol>
        </div>
      </div>

      <!-- Government-Style Early Warning Alert Box -->
      ${warnings.length > 0 ? `
        <div class="gov-alert ${warnings[0].severity === 'Critical' ? 'gov-alert-crit' : 'gov-alert-high'}">
          <div class="gov-alert-title">
            ⚠️ ${warnings[0].severity.toUpperCase()} PRIORITY WARNING: ${escapeHtml(warnings[0].warning_type)}
          </div>
          <div>${escapeHtml(warnings[0].explanation)}</div>
          <div style="margin-top: 6px; font-size: 11px; font-weight: 600;">
            Recommended Action: ${escapeHtml(warnings[0].recommended_review_action)}
          </div>
        </div>
      ` : `
        <div class="gov-alert gov-alert-info">
          <div class="gov-alert-title">Early Warning Status: Nominal</div>
          No active early warning triggers flagged for this project under current baseline metrics.
        </div>
      `}

      <!-- Decision Support Recommendations -->
      <div style="margin-bottom: 20px;">
        <h3 style="font-size: 13px; font-weight: 700; color: var(--gov-navy-dark); margin-bottom: 6px;">Recommended Decision Support Actions</h3>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${recs.map(r => `
            <div style="background: #ffffff; border: 1px solid var(--gov-border); border-left: 3px solid var(--gov-navy); padding: 8px 12px; border-radius: var(--radius-sm);">
              <div style="font-weight: 600; font-size: 12px; color: var(--gov-navy-dark);">${escapeHtml(r.title)} (${r.category})</div>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${escapeHtml(r.action)}</div>
            </div>
          `).join("")}
        </div>
      </div>

      <!-- What-If Scenario Simulator -->
      <div style="background: #f1f5f9; border: 1px solid var(--gov-border); padding: 14px; border-radius: var(--radius-sm);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 13px; font-weight: 700; color: var(--gov-navy-dark);">Interactive What-If Scenario Simulator</span>
          <span style="font-size: 11px; color: var(--text-muted);">Hypothetical Parameter Adjustment</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 10px;">
          <div>
            <label class="filter-label">Simulate Physical Progress: <span id="sim-val-prog">${p.physical_progress}%</span></label>
            <input type="range" min="0" max="100" step="1" value="${p.physical_progress}" id="sim-input-prog" style="width: 100%;">
          </div>
          <div>
            <label class="filter-label">Simulate Revised Cost (₹ Cr): <span id="sim-val-cost">₹${p.revised_cost}</span></label>
            <input type="range" min="${p.original_cost * 0.8}" max="${p.original_cost * 2.5}" step="50" value="${p.revised_cost}" id="sim-input-cost" style="width: 100%;">
          </div>
        </div>

        <div id="sim-result-box" style="background: #ffffff; border: 1px solid var(--gov-border); padding: 10px; border-radius: var(--radius-sm); font-size: 11px; display: none;">
          <!-- Populated dynamically on slider movement -->
        </div>
      </div>
    `;

    // Hook up What-If sliders
    setupWhatIfSliders(p);

    document.getElementById("modal-project-detail").classList.add("active");
  } catch (err) {
    console.error("Failed opening project drill-down:", err);
    alert("Could not load project details.");
  }
};

function setupWhatIfSliders(project) {
  const progInput = document.getElementById("sim-input-prog");
  const costInput = document.getElementById("sim-input-cost");

  async function triggerSimulation() {
    const newProg = parseFloat(progInput.value);
    const newCost = parseFloat(costInput.value);

    document.getElementById("sim-val-prog").textContent = `${newProg}%`;
    document.getElementById("sim-val-cost").textContent = `₹${newCost.toLocaleString()}`;

    try {
      const simRes = await PaimanaAPI.simulateWhatIf({
        project_id: project.project_id,
        simulated_physical_progress: newProg,
        simulated_revised_cost: newCost
      });

      const box = document.getElementById("sim-result-box");
      box.style.display = "block";
      const delta = simRes.score_change;
      const deltaColor = delta < 0 ? "var(--risk-low)" : (delta > 0 ? "var(--risk-crit)" : "var(--text-muted)");
      const deltaSign = delta > 0 ? `+${delta}` : `${delta}`;

      box.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <span>Simulated Overall Risk Score: <strong>${simRes.simulated_risk.overall_risk_score} / 100</strong> (${simRes.simulated_risk.risk_category})</span>
          <span style="font-weight: 700; color: ${deltaColor};">Score Shift: ${deltaSign} points</span>
        </div>
        <div style="color: var(--text-muted); font-size: 10px;">
          • Schedule Pressure Delta: ${simRes.derived_changes.schedule_pressure_delta > 0 ? '+' : ''}${simRes.derived_changes.schedule_pressure_delta}x | Cost Variance Delta: ${simRes.derived_changes.cost_variance_pct_delta > 0 ? '+' : ''}${simRes.derived_changes.cost_variance_pct_delta}%<br>
          <em>${simRes.scenario_notes}</em>
        </div>
      `;
    } catch (err) {
      console.error("Simulation error:", err);
    }
  }

  progInput?.addEventListener("input", debounce(triggerSimulation, 150));
  costInput?.addEventListener("input", debounce(triggerSimulation, 150));
}

function getRiskBarColor(score) {
  if (score >= 81) return "#dc2626";
  if (score >= 61) return "#ea580c";
  if (score >= 31) return "#d97706";
  return "#16a34a";
}

function closeModal() {
  document.getElementById("modal-project-detail").classList.remove("active");
}

// ----------------------------------------------------
// 4. Early Warning Center
// ----------------------------------------------------
async function loadEarlyWarnings(severity = "All") {
  const warnings = await PaimanaAPI.getWarnings(severity);
  const tbody = document.querySelector("#table-early-warnings-all tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (warnings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 20px; color: var(--text-muted);">No early warnings found for this severity filter.</td></tr>`;
    return;
  }

  warnings.forEach(w => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: monospace; font-size: 11px;">${w.warning_id}</td>
      <td>
        <div style="font-weight: 600; color: var(--gov-navy);">${escapeHtml(w.project_name)}</div>
        <div style="font-size: 10px; color: var(--text-light);">${w.project_id} • ${escapeHtml(w.state || '')}</div>
      </td>
      <td style="font-weight: 600;">${escapeHtml(w.warning_type)}</td>
      <td><span class="badge-risk ${w.severity.toLowerCase()}">${w.severity}</span></td>
      <td style="font-family: monospace; font-size: 11px; color: #991b1b;">${escapeHtml(w.triggering_indicator)}</td>
      <td style="font-size: 11px; max-width: 250px;">${escapeHtml(w.explanation)}</td>
      <td style="font-size: 11px; color: var(--text-muted); max-width: 250px;">${escapeHtml(w.recommended_review_action)}</td>
      <td><span style="font-size: 10px; background: #ecfdf5; color: #15803d; padding: 2px 6px; border-radius: 2px; font-weight: 600;">Active</span></td>
      <td>
        <button class="btn btn-outline" style="padding: 2px 6px; font-size: 10px;" onclick="openProjectDrillDown('${w.project_id}')">Inspect</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------------------------------------------
// 5. Anomalies Center
// ----------------------------------------------------
async function loadAnomalies() {
  const anomalies = await PaimanaAPI.getAnomalies();
  const tbody = document.querySelector("#table-anomalies-all tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (anomalies.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 20px; color: var(--text-muted);">No statistical anomalies detected.</td></tr>`;
    return;
  }

  anomalies.forEach(a => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: monospace; font-size: 11px;">${a.anomaly_id}</td>
      <td>
        <div style="font-weight: 600; color: var(--gov-navy);">${escapeHtml(a.project_name)}</div>
        <div style="font-size: 10px; color: var(--text-light);">${a.project_id}</div>
      </td>
      <td style="font-weight: 600; color: #4338ca;">${escapeHtml(a.anomaly_type)}</td>
      <td><span class="badge-risk ${a.severity.toLowerCase()}">${a.severity}</span></td>
      <td style="font-family: monospace; font-size: 11px;">${escapeHtml(a.trigger_indicator)}</td>
      <td style="font-size: 11px; max-width: 250px;">${escapeHtml(a.description)}</td>
      <td style="font-size: 11px; color: var(--text-muted); max-width: 200px;">${escapeHtml(a.recommended_check)}</td>
      <td>
        <button class="btn btn-outline" style="padding: 2px 6px; font-size: 10px;" onclick="openProjectDrillDown('${a.project_id}')">Inspect</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------------------------------------------
// 6. Analytics View
// ----------------------------------------------------
async function loadAnalyticsView() {
  const charts = await PaimanaAPI.getDashboardCharts();
  const projects = await PaimanaAPI.getProjects();

  PaimanaCharts.renderMinistryRisk("chart-analytics-ministry", charts.ministry_risk);
  PaimanaCharts.renderGapDistribution("chart-analytics-gap", projects);

  // Size band breakdown
  const sizeMap = {};
  projects.forEach(p => {
    const band = p.derived_indicators?.size_band || "Other";
    if (!sizeMap[band]) {
      sizeMap[band] = { count: 0, cost: 0, exp: 0, scores: [], crits: 0 };
    }
    sizeMap[band].count++;
    sizeMap[band].cost += p.revised_cost;
    sizeMap[band].exp += p.expenditure;
    sizeMap[band].scores.push(p.risk_report.overall_risk_score);
    if (p.risk_report.risk_category === "Critical") sizeMap[band].crits++;
  });

  const tbody = document.querySelector("#table-analytics-size-bands tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  Object.entries(sizeMap).forEach(([band, data]) => {
    const avgScore = (data.scores.reduce((a, b) => a + b, 0) / data.scores.length).toFixed(1);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 600;">${escapeHtml(band)}</td>
      <td style="text-align: center;">${data.count}</td>
      <td style="text-align: right; font-weight: 600;">₹${data.cost.toLocaleString()} Cr</td>
      <td style="text-align: right;">₹${data.exp.toLocaleString()} Cr</td>
      <td style="text-align: center; font-weight: 700;">${avgScore}</td>
      <td style="text-align: center; color: var(--risk-crit); font-weight: 700;">${data.crits}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------------------------------------------
// 7. PAIMANA AI Assistant Query Handler
// ----------------------------------------------------
async function handleAssistantQuery() {
  const input = document.getElementById("ai-query-input");
  const query = input.value.trim();
  if (!query) return;

  const chatLogs = document.getElementById("ai-chat-logs");

  // Append user message
  const userDiv = document.createElement("div");
  userDiv.className = "ai-msg user";
  userDiv.textContent = query;
  chatLogs.appendChild(userDiv);
  input.value = "";
  chatLogs.scrollTop = chatLogs.scrollHeight;

  // Append thinking placeholder
  const botDiv = document.createElement("div");
  botDiv.className = "ai-msg assistant";
  botDiv.innerHTML = "<em>Analyzing project dataset...</em>";
  chatLogs.appendChild(botDiv);
  chatLogs.scrollTop = chatLogs.scrollHeight;

  try {
    const res = await PaimanaAPI.askAssistant(query);
    let html = formatMarkdownToHTML(res.answer);

    // If related projects, add quick action buttons
    if (res.related_projects && res.related_projects.length > 0) {
      html += `<div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px;">`;
      res.related_projects.slice(0, 4).forEach(p => {
        html += `<button class="btn btn-outline" style="font-size: 10px; padding: 2px 6px;" onclick="openProjectDrillDown('${p.project_id}')">Open ${escapeHtml(p.project_id)}</button>`;
      });
      html += `</div>`;
    }

    botDiv.innerHTML = html;
  } catch (err) {
    botDiv.innerHTML = `<span style="color: var(--risk-crit);">Error retrieving analytical response. Please try another query.</span>`;
  }
  chatLogs.scrollTop = chatLogs.scrollHeight;
}

// ----------------------------------------------------
// 8. Data Ingestion & Manual Entry
// ----------------------------------------------------
async function handleManualProjectSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);

  const payload = {
    project_id: formData.get("project_id"),
    project_name: formData.get("project_name"),
    ministry: formData.get("ministry"),
    sector: formData.get("sector"),
    state: formData.get("state"),
    original_cost: parseFloat(formData.get("original_cost")),
    revised_cost: parseFloat(formData.get("revised_cost")),
    expenditure: parseFloat(formData.get("expenditure")),
    start_date: formData.get("start_date"),
    original_completion_date: formData.get("original_completion_date"),
    expected_completion_date: formData.get("expected_completion_date"),
    physical_progress: parseFloat(formData.get("physical_progress")),
    financial_progress: parseFloat(formData.get("financial_progress")),
    data_source: "manual"
  };

  try {
    const res = await PaimanaAPI.createProject(payload);
    alert(`Project ${payload.project_id} saved successfully! Computed Risk Score: ${res.project.risk_report.overall_risk_score}/100 (${res.project.risk_report.risk_category}).`);
    form.reset();
    await loadDashboardData();
    await populateFilterDropdowns();
    openProjectDrillDown(payload.project_id);
  } catch (err) {
    alert("Error saving project. Please check numeric and date inputs.");
  }
}

async function handleFileValidate() {
  if (!selectedFile) return;
  try {
    uploadPreviewData = await PaimanaAPI.uploadPreview(selectedFile);
    document.getElementById("upload-preview-area").style.display = "block";

    const qStats = document.getElementById("upload-quality-stats");
    qStats.innerHTML = `
      <strong>File:</strong> ${escapeHtml(uploadPreviewData.filename)} | 
      <strong>Total Records:</strong> ${uploadPreviewData.total_rows} | 
      <strong>Data Quality Score:</strong> ${uploadPreviewData.quality_score} / 100<br>
      ${uploadPreviewData.issues_detected.length > 0 ? 
        `<span style="color: var(--risk-med);">Notices: ${uploadPreviewData.issues_detected.join("; ")}</span>` : 
        `<span style="color: var(--risk-low);">All required columns verified successfully.</span>`
      }
    `;

    const mappingContainer = document.getElementById("upload-mapping-container");
    mappingContainer.innerHTML = "";
    const table = document.createElement("table");
    table.className = "gov-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Uploaded File Column</th>
          <th>Mapped System Schema Field</th>
        </tr>
      </thead>
      <tbody>
        ${uploadPreviewData.detected_columns.map(col => `
          <tr>
            <td><strong>${escapeHtml(col)}</strong></td>
            <td>
              <select class="form-control mapping-select" data-col="${escapeHtml(col)}">
                <option value="none">-- Ignore / Unmapped --</option>
                ${[
                  "project_id", "project_name", "ministry", "sector", "state",
                  "original_cost", "revised_cost", "expenditure",
                  "start_date", "original_completion_date", "expected_completion_date",
                  "physical_progress", "financial_progress"
                ].map(f => `
                  <option value="${f}" ${uploadPreviewData.recommended_mappings[col] === f ? 'selected' : ''}>
                    ${f}
                  </option>
                `).join("")}
              </select>
            </td>
          </tr>
        `).join("")}
      </tbody>
    `;
    mappingContainer.appendChild(table);
  } catch (err) {
    alert(`File validation error: ${err.message}`);
  }
}

async function handleFileCommit() {
  if (!uploadPreviewData || !selectedFile) return;

  const mapping = {};
  document.querySelectorAll(".mapping-select").forEach(sel => {
    const col = sel.dataset.col;
    const mappedTo = sel.value;
    if (mappedTo !== "none") {
      mapping[col] = mappedTo;
    }
  });

  try {
    const res = await PaimanaAPI.uploadCommit(selectedFile.name, mapping);
    alert(res.message);
    document.getElementById("upload-preview-area").style.display = "none";
    document.getElementById("selected-file-label").textContent = "";
    document.getElementById("file-upload-input").value = "";
    document.getElementById("btn-validate-upload").disabled = true;

    await loadDashboardData();
    await populateFilterDropdowns();
    document.querySelector('[data-target="view-projects"]')?.click();
  } catch (err) {
    alert("Failed committing dataset to database.");
  }
}

// ----------------------------------------------------
// Utilities
// ----------------------------------------------------
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdownToHTML(text) {
  return text
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
