// PAIMANA AI - API Client
const API_BASE = "";

const PaimanaAPI = {
  async getDashboardKPIs() {
    const res = await fetch(`${API_BASE}/api/dashboard/kpis`);
    return await res.json();
  },

  async getDashboardCharts() {
    const res = await fetch(`${API_BASE}/api/dashboard/charts`);
    return await res.json();
  },

  async getProjects(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/api/projects?${query}`);
    return await res.json();
  },

  async getProjectDetail(projectId) {
    const res = await fetch(`${API_BASE}/api/projects/${encodeURIComponent(projectId)}`);
    return await res.json();
  },

  async createProject(projectData) {
    const res = await fetch(`${API_BASE}/api/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(projectData)
    });
    return await res.json();
  },

  async resetDemo() {
    const res = await fetch(`${API_BASE}/api/projects/reset-demo`, {
      method: "POST"
    });
    return await res.json();
  },

  async getWarnings(severity = "All") {
    const url = severity && severity !== "All" ? `${API_BASE}/api/warnings?severity=${severity}` : `${API_BASE}/api/warnings`;
    const res = await fetch(url);
    return await res.json();
  },

  async getAnomalies() {
    const res = await fetch(`${API_BASE}/api/anomalies`);
    return await res.json();
  },

  async getPriorityQueue(limit = 10) {
    const res = await fetch(`${API_BASE}/api/priority-queue?limit=${limit}`);
    return await res.json();
  },

  async simulateWhatIf(simData) {
    const res = await fetch(`${API_BASE}/api/what-if`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(simData)
    });
    return await res.json();
  },

  async askAssistant(queryText) {
    const res = await fetch(`${API_BASE}/api/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText })
    });
    return await res.json();
  },

  async uploadPreview(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/api/upload/preview`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload validation failed");
    }
    return await res.json();
  },

  async uploadCommit(filename, mapping) {
    const formData = new FormData();
    formData.append("filename", filename);
    formData.append("mapping", JSON.stringify(mapping));
    const res = await fetch(`${API_BASE}/api/upload/commit`, {
      method: "POST",
      body: formData
    });
    return await res.json();
  }
};
