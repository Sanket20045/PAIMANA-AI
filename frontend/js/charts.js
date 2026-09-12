// PAIMANA AI - Chart Renderers (Government Minimal Style)
let chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

const PaimanaCharts = {
  renderRiskDistribution(canvasId, distData) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext("2d");
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Low (0–30)", "Medium (31–60)", "High (61–80)", "Critical (81–100)"],
        datasets: [{
          data: [
            distData.Low || 0,
            distData.Medium || 0,
            distData.High || 0,
            distData.Critical || 0
          ],
          backgroundColor: ["#16a34a", "#d97706", "#ea580c", "#dc2626"],
          borderWidth: 1,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { font: { size: 11, family: "Inter" }, boxWidth: 12 }
          },
          tooltip: {
            callbacks: {
              label: (context) => ` ${context.label}: ${context.raw} projects`
            }
          }
        }
      }
    });
  },

  renderSectorRisk(canvasId, sectorData) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext("2d");
    if (!ctx) return;

    const labels = sectorData.map(s => s.sector);
    const scores = sectorData.map(s => s.avg_risk);

    chartInstances[canvasId] = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Average Risk Score",
          data: scores,
          backgroundColor: scores.map(s => s > 70 ? "#dc2626" : (s > 50 ? "#ea580c" : (s > 35 ? "#d97706" : "#2563eb"))),
          borderWidth: 1,
          borderColor: "#d1d5db"
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            min: 0,
            max: 100,
            grid: { color: "#f1f5f9" },
            title: { display: true, text: "Average Risk Score (0–100)", font: { size: 11 } }
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 11 } }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  },

  renderCostVsProgress(canvasId, scatterData) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext("2d");
    if (!ctx) return;

    const points = scatterData.map(d => ({
      x: d.physical_progress,
      y: Math.min(d.cost, 45000),
      raw: d
    }));

    chartInstances[canvasId] = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [{
          label: "Projects",
          data: points,
          backgroundColor: scatterData.map(d => {
            const cat = d.risk_category;
            if (cat === "Critical") return "#dc2626";
            if (cat === "High") return "#ea580c";
            if (cat === "Medium") return "#d97706";
            return "#16a34a";
          }),
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            min: 0,
            max: 100,
            title: { display: true, text: "Physical Progress (%)", font: { size: 11 } },
            grid: { color: "#f1f5f9" }
          },
          y: {
            title: { display: true, text: "Sanctioned Cost (₹ Cr)", font: { size: 11 } },
            grid: { color: "#f1f5f9" }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const item = context.raw.raw;
                return ` ${item.project_name}: Progress ${item.physical_progress}% | Cost ₹${item.cost} Cr | Risk: ${item.risk_score} (${item.risk_category})`;
              }
            }
          }
        }
      }
    });
  },

  renderMinistryRisk(canvasId, ministryData) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext("2d");
    if (!ctx) return;

    chartInstances[canvasId] = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ministryData.map(m => m.ministry.replace("Ministry of ", "")),
        datasets: [{
          label: "Avg Risk",
          data: ministryData.map(m => m.avg_risk),
          backgroundColor: "#0f2a4a",
          borderWidth: 1,
          borderColor: "#0a1e36"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100, grid: { color: "#f1f5f9" } },
          x: { ticks: { font: { size: 10 } }, grid: { display: false } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  },

  renderGapDistribution(canvasId, projects) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext("2d");
    if (!ctx) return;

    // Buckets: <=0%, 1-15%, 16-30%, >30%
    let b1 = 0, b2 = 0, b3 = 0, b4 = 0;
    for (let p of projects) {
      const gap = p.derived_indicators?.progress_gap || 0;
      if (gap <= 0) b1++;
      else if (gap <= 15) b2++;
      else if (gap <= 30) b3++;
      else b4++;
    }

    chartInstances[canvasId] = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Aligned (≤ 0%)", "Mild Gap (1–15%)", "Elevated Gap (16–30%)", "Severe Gap (> 30%)"],
        datasets: [{
          label: "Projects",
          data: [b1, b2, b3, b4],
          backgroundColor: ["#16a34a", "#3b82f6", "#f59e0b", "#ef4444"],
          borderWidth: 1,
          borderColor: "#d1d5db"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { grid: { color: "#f1f5f9" }, ticks: { stepSize: 1 } },
          x: { grid: { display: false }, ticks: { font: { size: 11 } } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
};
