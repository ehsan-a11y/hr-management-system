/**
 * HR Management System — Bayzat-style Frontend
 * Vanilla JS + Chart.js, communicates with FastAPI backend
 */

const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:8000"
  : "";

// ─── Utilities ──────────────────────────────────────────────────────────────

async function fetchJSON(url, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (options.body instanceof FormData) delete headers["Content-Type"];
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${type === "success" ? "✓" : type === "error" ? "✕" : "ℹ"}</span> ${msg}`;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function badge(status) {
  const map = {
    active: "badge-success", inactive: "badge-default",
    on_leave: "badge-warning", terminated: "badge-danger",
    pending: "badge-warning", approved: "badge-success",
    rejected: "badge-danger", present: "badge-success",
    absent: "badge-danger", late: "badge-warning",
    half_day: "badge-info", paid: "badge-success",
    draft: "badge-default", submitted: "badge-info",
    completed: "badge-success", expired: "badge-danger",
    expiring_soon: "badge-warning", valid: "badge-success",
    low: "badge-default", medium: "badge-warning",
    high: "badge-danger", urgent: "badge-danger",
  };
  return `<span class="badge ${map[status] || "badge-default"}">${status?.replace(/_/g, " ")}</span>`;
}

function initials(first, last) {
  return ((first?.[0] || "") + (last?.[0] || "")).toUpperCase();
}

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function formatCurrency(n) {
  return new Intl.NumberFormat("en-AE", { style: "currency", currency: "AED", maximumFractionDigits: 0 }).format(n || 0);
}

function loading(id) {
  document.getElementById(id).innerHTML = `<div class="loading-row"><div class="spinner"></div><span>Loading…</span></div>`;
}

function emptyState(id, msg = "No records found") {
  document.getElementById(id).innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>${msg}</p></div>`;
}

const avatarColors = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];
function avatarColor(name) {
  let h = 0;
  for (let c of name || "") h = c.charCodeAt(0) + h * 31;
  return avatarColors[Math.abs(h) % avatarColors.length];
}

function avatarEl(emp, size = 36) {
  if (emp?.avatar_url) {
    return `<img src="${emp.avatar_url}" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;" alt="avatar">`;
  }
  const name = `${emp?.first_name || ""}${emp?.last_name || ""}`;
  const color = avatarColor(name);
  const ini = initials(emp?.first_name, emp?.last_name) || "?";
  return `<div class="avatar-circle" style="width:${size}px;height:${size}px;background:${color};font-size:${Math.round(size*0.38)}px;">${ini}</div>`;
}

function starsEl(rating) {
  const r = Math.round(rating || 0);
  return Array.from({ length: 5 }, (_, i) =>
    `<span class="star ${i < r ? "filled" : ""}">${i < r ? "★" : "☆"}</span>`
  ).join("");
}

function docStatusEl(doc) {
  if (!doc.expiry_date) return badge("valid");
  const days = Math.ceil((new Date(doc.expiry_date) - new Date()) / 86400000);
  if (days < 0) return badge("expired");
  if (days <= 30) return badge("expiring_soon");
  return badge("valid");
}

function v(id) { return document.getElementById(id)?.value?.trim() || ""; }
function setVal(id, val) { const el = document.getElementById(id); if (el) el.value = val ?? ""; }

async function compressImage(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const size = 200;
        canvas.width = size; canvas.height = size;
        const ctx = canvas.getContext("2d");
        const sq = Math.min(img.width, img.height);
        const sx = (img.width - sq) / 2;
        const sy = (img.height - sq) / 2;
        ctx.drawImage(img, sx, sy, sq, sq, 0, 0, size, size);
        resolve(canvas.toDataURL("image/jpeg", 0.8));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ─── Navigation ─────────────────────────────────────────────────────────────

const PAGE_META = {
  dashboard:     { title: "Dashboard",       subtitle: "Welcome back! Here's what's happening today." },
  analytics:     { title: "Analytics",       subtitle: "Workforce insights and key performance metrics." },
  announcements: { title: "Announcements",   subtitle: "Company-wide news and updates." },
  employees:     { title: "Employees",        subtitle: "Manage your workforce directory." },
  departments:   { title: "Departments",      subtitle: "Organizational structure and teams." },
  orgchart:      { title: "Org Chart",        subtitle: "Visual hierarchy of your organization." },
  attendance:    { title: "Attendance",       subtitle: "Track daily presence and working hours." },
  leaves:        { title: "Leave Management", subtitle: "Requests, approvals, and leave balances." },
  payroll:       { title: "Payroll",          subtitle: "Salary processing and payment records." },
  performance:   { title: "Performance",      subtitle: "Reviews, goals, and employee ratings." },
  documents:     { title: "Documents",        subtitle: "Employee files, contracts, and certificates." },
  benefits:      { title: "Benefits",         subtitle: "Insurance, allowances, and employee perks." },
};

let currentPage = "dashboard";

function showPage(name) {
  currentPage = name;
  document.querySelectorAll(".page-section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const section = document.getElementById(`page-${name}`);
  if (section) section.classList.add("active");

  document.querySelectorAll(`.nav-item[data-page="${name}"]`).forEach(n => n.classList.add("active"));

  const meta = PAGE_META[name] || {};
  const titleEl = document.getElementById("page-title");
  const subtitleEl = document.getElementById("page-subtitle");
  if (titleEl) titleEl.textContent = meta.title || name;
  if (subtitleEl) subtitleEl.textContent = meta.subtitle || "";

  document.getElementById("sidebar")?.classList.remove("open");

  const loaders = {
    dashboard:     loadDashboard,
    analytics:     loadAnalytics,
    announcements: loadAnnouncements,
    employees:     loadEmployees,
    departments:   loadDepartments,
    orgchart:      loadOrgChart,
    attendance:    loadAttendance,
    leaves:        loadLeaves,
    payroll:       loadPayroll,
    performance:   loadPerformance,
    documents:     loadDocuments,
    benefits:      loadBenefits,
  };
  loaders[name]?.();
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const [emps, depts, leaves, payrolls, announcements] = await Promise.all([
      fetchJSON(`${API}/api/employees`),
      fetchJSON(`${API}/api/departments`),
      fetchJSON(`${API}/api/leaves`),
      fetchJSON(`${API}/api/payroll`),
      fetchJSON(`${API}/api/announcements`).catch(() => []),
    ]);

    const active = emps.filter(e => e.status === "active").length;
    const pendingLeaves = leaves.filter(l => l.status === "pending").length;
    const thisMonth = new Date().toISOString().slice(0, 7);
    const monthPay = payrolls.filter(p => p.period?.startsWith(thisMonth));
    const totalPayroll = monthPay.reduce((s, p) => s + (p.net_salary || 0), 0);

    document.getElementById("stat-employees").textContent = active;
    document.getElementById("stat-departments").textContent = depts.length;
    document.getElementById("stat-leaves").textContent = pendingLeaves;
    document.getElementById("stat-payroll").textContent = formatCurrency(totalPayroll);

    // Recent employees
    const recentEl = document.getElementById("recent-employees");
    const recent = emps.slice(-5).reverse();
    recentEl.innerHTML = recent.length ? recent.map(e => `
      <div class="emp-row clickable" onclick="openProfile(${e.id})">
        ${avatarEl(e)}
        <div class="emp-info">
          <div class="emp-name">${e.first_name} ${e.last_name}</div>
          <div class="emp-sub">${e.position || "—"} · ${e.department?.name || "—"}</div>
        </div>
        ${badge(e.status)}
      </div>
    `).join("") : '<div class="empty-state"><p>No employees yet</p></div>';

    // Announcements mini
    const annEl = document.getElementById("dash-announcements");
    if (annEl) {
      annEl.innerHTML = announcements.slice(0, 3).map(a => `
        <div class="announce-mini" onclick="showPage('announcements')">
          <span class="ann-priority ann-${a.priority}">${a.priority}</span>
          <strong>${a.title}</strong>
          <span class="ann-date">${formatDate(a.created_at)}</span>
        </div>
      `).join("") || '<p class="muted">No announcements</p>';
    }

    // Quick actions
    const qaEl = document.getElementById("quick-actions");
    if (qaEl) {
      qaEl.innerHTML = [
        { icon: "👤", label: "Add Employee",   action: "employees" },
        { icon: "📋", label: "New Leave",      action: "leaves" },
        { icon: "💰", label: "Run Payroll",    action: "payroll" },
        { icon: "📄", label: "Upload Doc",     action: "documents" },
        { icon: "📢", label: "Announce",       action: "announcements" },
        { icon: "📊", label: "Analytics",      action: "analytics" },
      ].map(q => `
        <button class="qa-btn" onclick="showPage('${q.action}')">
          <span class="qa-icon">${q.icon}</span>
          <span>${q.label}</span>
        </button>
      `).join("");
    }

  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Analytics ───────────────────────────────────────────────────────────────

let _charts = {};

function destroyCharts() {
  Object.values(_charts).forEach(c => c?.destroy?.());
  _charts = {};
}

async function loadAnalytics() {
  destroyCharts();
  try {
    const data = await fetchJSON(`${API}/api/analytics`);

    // Dept distribution doughnut
    const dCtx = document.getElementById("chart-dept")?.getContext("2d");
    if (dCtx && data.dept_distribution) {
      _charts.dept = new Chart(dCtx, {
        type: "doughnut",
        data: {
          labels: data.dept_distribution.map(d => d.name),
          datasets: [{ data: data.dept_distribution.map(d => d.count), backgroundColor: avatarColors, borderWidth: 2 }]
        },
        options: { responsive: true, plugins: { legend: { position: "right" } } }
      });
    }

    // Attendance trend line
    const aCtx = document.getElementById("chart-attendance")?.getContext("2d");
    if (aCtx && data.attendance_trend) {
      _charts.att = new Chart(aCtx, {
        type: "line",
        data: {
          labels: data.attendance_trend.map(d => d.date),
          datasets: [
            { label: "Present", data: data.attendance_trend.map(d => d.present), borderColor: "#10b981", backgroundColor: "rgba(16,185,129,0.1)", tension: 0.4, fill: true },
            { label: "Absent",  data: data.attendance_trend.map(d => d.absent),  borderColor: "#ef4444", backgroundColor: "rgba(239,68,68,0.05)", tension: 0.4 },
          ]
        },
        options: { responsive: true, plugins: { legend: { position: "top" } }, scales: { y: { beginAtZero: true } } }
      });
    }

    // Payroll bar
    const pCtx = document.getElementById("chart-payroll")?.getContext("2d");
    if (pCtx && data.payroll_trend) {
      _charts.pay = new Chart(pCtx, {
        type: "bar",
        data: {
          labels: data.payroll_trend.map(d => d.period),
          datasets: [{ label: "Total Payroll (AED)", data: data.payroll_trend.map(d => d.total), backgroundColor: "#4f46e5", borderRadius: 6 }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
      });
    }

    // Leave types pie
    const lCtx = document.getElementById("chart-leave")?.getContext("2d");
    if (lCtx && data.leave_types) {
      _charts.leave = new Chart(lCtx, {
        type: "pie",
        data: {
          labels: data.leave_types.map(d => d.type),
          datasets: [{ data: data.leave_types.map(d => d.count), backgroundColor: ["#4f46e5","#10b981","#f59e0b","#ef4444","#0ea5e9"] }]
        },
        options: { responsive: true, plugins: { legend: { position: "right" } } }
      });
    }

    // KPI cards
    const kpiEl = document.getElementById("analytics-kpis");
    if (kpiEl && data.kpis) {
      const k = data.kpis;
      kpiEl.innerHTML = `
        <div class="kpi-card"><div class="kpi-val">${k.total_employees ?? "—"}</div><div class="kpi-lbl">Total Employees</div></div>
        <div class="kpi-card"><div class="kpi-val">${k.avg_attendance_pct ?? "—"}%</div><div class="kpi-lbl">Avg Attendance</div></div>
        <div class="kpi-card"><div class="kpi-val">${formatCurrency(k.avg_salary)}</div><div class="kpi-lbl">Avg Salary</div></div>
        <div class="kpi-card"><div class="kpi-val">${k.pending_leaves ?? "—"}</div><div class="kpi-lbl">Pending Leaves</div></div>
      `;
    }
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Announcements ────────────────────────────────────────────────────────────

async function loadAnnouncements() {
  loading("ann-list");
  try {
    const items = await fetchJSON(`${API}/api/announcements`);
    const el = document.getElementById("ann-list");
    el.innerHTML = items.length ? items.map(a => `
      <div class="announce-card priority-${a.priority}">
        <div class="ann-header">
          <div>
            <span class="ann-cat">${a.category || "General"}</span>
            ${badge(a.priority)}
          </div>
          <div class="ann-actions">
            <button class="btn-icon" onclick="editAnnouncement(${a.id})" title="Edit">✏️</button>
            <button class="btn-icon danger" onclick="deleteAnnouncement(${a.id})" title="Delete">🗑️</button>
          </div>
        </div>
        <h3 class="ann-title">${a.title}</h3>
        <p class="ann-body">${a.content}</p>
        <div class="ann-footer">
          <span>By <strong>${a.author || "Admin"}</strong></span>
          <span>${formatDate(a.created_at)}</span>
        </div>
      </div>
    `).join("") : '<div class="empty-state"><div class="empty-icon">📢</div><p>No announcements yet</p></div>';
  } catch (e) {
    emptyState("ann-list", e.message);
  }
}

function openAnnForm(data = {}) {
  setVal("ann-id", data.id || "");
  setVal("ann-title", data.title || "");
  setVal("ann-content", data.content || "");
  setVal("ann-priority", data.priority || "medium");
  setVal("ann-category", data.category || "General");
  setVal("ann-author", data.author || "");
  document.getElementById("ann-modal-title").textContent = data.id ? "Edit Announcement" : "New Announcement";
  openModal("ann-modal");
}

async function editAnnouncement(id) {
  try {
    const items = await fetchJSON(`${API}/api/announcements`);
    const a = items.find(x => x.id === id);
    if (a) openAnnForm(a);
  } catch (e) { toast(e.message, "error"); }
}

async function saveAnnouncement() {
  const id = v("ann-id");
  const body = {
    title: v("ann-title"), content: v("ann-content"),
    priority: v("ann-priority"), category: v("ann-category"),
    author: v("ann-author"),
  };
  if (!body.title || !body.content) return toast("Title and content required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/announcements/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/announcements`, { method: "POST", body: JSON.stringify(body) });
    closeModal("ann-modal");
    toast(id ? "Updated" : "Announced!");
    loadAnnouncements();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteAnnouncement(id) {
  if (!confirm("Delete this announcement?")) return;
  try {
    await fetchJSON(`${API}/api/announcements/${id}`, { method: "DELETE" });
    toast("Deleted"); loadAnnouncements();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Employees ────────────────────────────────────────────────────────────────

let _departments = [];

async function loadEmployees() {
  loading("emp-table");
  try {
    const [emps, depts] = await Promise.all([
      fetchJSON(`${API}/api/employees`),
      fetchJSON(`${API}/api/departments`),
    ]);
    _departments = depts;

    const searchEl = document.getElementById("emp-search");
    const render = (list) => {
      const el = document.getElementById("emp-table");
      el.innerHTML = list.length ? `
        <table class="data-table">
          <thead><tr><th></th><th>Name</th><th>Department</th><th>Position</th><th>Email</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>${list.map(e => `
            <tr>
              <td>${avatarEl(e, 36)}</td>
              <td class="clickable" onclick="openProfile(${e.id})"><strong>${e.first_name} ${e.last_name}</strong></td>
              <td>${e.department?.name || "—"}</td>
              <td>${e.position || "—"}</td>
              <td>${e.email}</td>
              <td>${badge(e.status)}</td>
              <td>
                <button class="btn-icon" onclick="editEmployee(${e.id})" title="Edit">✏️</button>
                <button class="btn-icon danger" onclick="deleteEmployee(${e.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `).join("")}</tbody>
        </table>
      ` : '<div class="empty-state"><div class="empty-icon">👥</div><p>No employees found</p></div>';
    };

    render(emps);
    if (searchEl) {
      searchEl.oninput = () => {
        const q = searchEl.value.toLowerCase();
        render(emps.filter(e =>
          `${e.first_name} ${e.last_name} ${e.email} ${e.position || ""} ${e.department?.name || ""}`.toLowerCase().includes(q)
        ));
      };
    }

    // Populate dept select in form
    const deptSel = document.getElementById("emp-dept");
    if (deptSel) {
      deptSel.innerHTML = '<option value="">Select Department</option>' +
        depts.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
    }
  } catch (e) {
    emptyState("emp-table", e.message);
  }
}

function openEmpForm(data = {}) {
  setVal("emp-id", data.id || "");
  setVal("emp-first", data.first_name || "");
  setVal("emp-last", data.last_name || "");
  setVal("emp-email", data.email || "");
  setVal("emp-phone", data.phone || "");
  setVal("emp-position", data.position || "");
  setVal("emp-dept", data.department_id || "");
  setVal("emp-salary", data.salary || "");
  setVal("emp-hire", data.hire_date || "");
  setVal("emp-status", data.status || "active");
  setVal("emp-avatar-url", data.avatar_url || "");
  const preview = document.getElementById("emp-avatar-preview");
  if (preview) preview.innerHTML = data.avatar_url ? `<img src="${data.avatar_url}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;">` : "";
  document.getElementById("emp-modal-title").textContent = data.id ? "Edit Employee" : "Add Employee";
  openModal("emp-modal");
}

async function editEmployee(id) {
  try {
    const emps = await fetchJSON(`${API}/api/employees`);
    const e = emps.find(x => x.id === id);
    if (e) openEmpForm(e);
  } catch (e) { toast(e.message, "error"); }
}

async function saveEmployee() {
  const id = v("emp-id");
  const body = {
    first_name: v("emp-first"), last_name: v("emp-last"),
    email: v("emp-email"), phone: v("emp-phone"),
    position: v("emp-position"),
    department_id: v("emp-dept") ? parseInt(v("emp-dept")) : null,
    salary: v("emp-salary") ? parseFloat(v("emp-salary")) : null,
    hire_date: v("emp-hire") || null,
    status: v("emp-status"),
    avatar_url: v("emp-avatar-url") || null,
  };
  if (!body.first_name || !body.last_name || !body.email) return toast("Name and email required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/employees/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/employees`, { method: "POST", body: JSON.stringify(body) });
    closeModal("emp-modal");
    toast(id ? "Employee updated" : "Employee added!");
    loadEmployees();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteEmployee(id) {
  if (!confirm("Delete this employee? This cannot be undone.")) return;
  try {
    await fetchJSON(`${API}/api/employees/${id}`, { method: "DELETE" });
    toast("Employee deleted"); loadEmployees();
  } catch (e) { toast(e.message, "error"); }
}

async function handleAvatarUpload(input) {
  const file = input.files?.[0];
  if (!file) return;
  const compressed = await compressImage(file);
  setVal("emp-avatar-url", compressed);
  const preview = document.getElementById("emp-avatar-preview");
  if (preview) preview.innerHTML = `<img src="${compressed}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;">`;
}

// Employee profile modal
async function openProfile(empId) {
  try {
    const [emps, leaves, docs, perfs, benefits] = await Promise.all([
      fetchJSON(`${API}/api/employees`),
      fetchJSON(`${API}/api/leaves`).catch(() => []),
      fetchJSON(`${API}/api/documents`).catch(() => []),
      fetchJSON(`${API}/api/performance`).catch(() => []),
      fetchJSON(`${API}/api/benefits`).catch(() => []),
    ]);
    const e = emps.find(x => x.id === empId);
    if (!e) return;

    const empLeaves = leaves.filter(l => l.employee_id === empId);
    const empDocs   = docs.filter(d => d.employee_id === empId);
    const empPerfs  = perfs.filter(p => p.employee_id === empId);
    const empBen    = benefits.filter(b => b.employee_id === empId);

    document.getElementById("profile-content").innerHTML = `
      <div class="profile-header">
        <div>${avatarEl(e, 80)}</div>
        <div class="profile-info">
          <h2>${e.first_name} ${e.last_name}</h2>
          <div class="profile-sub">${e.position || "—"} · ${e.department?.name || "—"}</div>
          <div class="profile-sub">${e.email} ${e.phone ? "· " + e.phone : ""}</div>
          ${badge(e.status)}
        </div>
        <button class="btn-secondary" onclick="editEmployee(${e.id});closeModal('profile-modal')">✏️ Edit</button>
      </div>
      <div class="profile-tabs">
        <div class="profile-section">
          <h4>Details</h4>
          <div class="detail-grid">
            <div><span class="lbl">Hire Date</span><span>${formatDate(e.hire_date)}</span></div>
            <div><span class="lbl">Salary</span><span>${formatCurrency(e.salary)}</span></div>
          </div>
        </div>
        ${empPerfs.length ? `
        <div class="profile-section">
          <h4>Latest Performance</h4>
          ${empPerfs.slice(-1).map(p => `
            <div class="perf-mini">
              <div>${starsEl(p.rating)} <strong>${p.period}</strong></div>
              <div class="muted">${p.goals || ""}</div>
            </div>
          `).join("")}
        </div>` : ""}
        ${empLeaves.length ? `
        <div class="profile-section">
          <h4>Leave History (${empLeaves.length})</h4>
          <div class="mini-list">${empLeaves.slice(-3).map(l => `
            <div class="mini-row"><span>${l.leave_type}</span>${badge(l.status)}<span>${formatDate(l.start_date)}</span></div>
          `).join("")}</div>
        </div>` : ""}
        ${empDocs.length ? `
        <div class="profile-section">
          <h4>Documents (${empDocs.length})</h4>
          <div class="mini-list">${empDocs.map(d => `
            <div class="mini-row"><span>${d.name}</span>${docStatusEl(d)}</div>
          `).join("")}</div>
        </div>` : ""}
        ${empBen.length ? `
        <div class="profile-section">
          <h4>Benefits (${empBen.length})</h4>
          <div class="mini-list">${empBen.map(b => `
            <div class="mini-row"><span>${b.benefit_type}</span>${badge(b.status)}<span>${b.provider || ""}</span></div>
          `).join("")}</div>
        </div>` : ""}
      </div>
    `;
    openModal("profile-modal");
  } catch (e) { toast(e.message, "error"); }
}

// ─── Departments ──────────────────────────────────────────────────────────────

async function loadDepartments() {
  loading("dept-table");
  try {
    const [depts, emps] = await Promise.all([
      fetchJSON(`${API}/api/departments`),
      fetchJSON(`${API}/api/employees`),
    ]);
    const empCount = {};
    emps.forEach(e => { empCount[e.department_id] = (empCount[e.department_id] || 0) + 1; });
    const el = document.getElementById("dept-table");
    el.innerHTML = depts.length ? `
      <table class="data-table">
        <thead><tr><th>Name</th><th>Description</th><th>Employees</th><th>Actions</th></tr></thead>
        <tbody>${depts.map(d => `
          <tr>
            <td><strong>${d.name}</strong></td>
            <td>${d.description || "—"}</td>
            <td><span class="emp-count">${empCount[d.id] || 0}</span></td>
            <td>
              <button class="btn-icon" onclick="editDept(${d.id})" title="Edit">✏️</button>
              <button class="btn-icon danger" onclick="deleteDept(${d.id})" title="Delete">🗑️</button>
            </td>
          </tr>
        `).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">🏢</div><p>No departments yet</p></div>';
  } catch (e) {
    emptyState("dept-table", e.message);
  }
}

function openDeptForm(data = {}) {
  setVal("dept-id", data.id || "");
  setVal("dept-name", data.name || "");
  setVal("dept-desc", data.description || "");
  document.getElementById("dept-modal-title").textContent = data.id ? "Edit Department" : "Add Department";
  openModal("dept-modal");
}

async function editDept(id) {
  try {
    const depts = await fetchJSON(`${API}/api/departments`);
    const d = depts.find(x => x.id === id);
    if (d) openDeptForm(d);
  } catch (e) { toast(e.message, "error"); }
}

async function saveDept() {
  const id = v("dept-id");
  const body = { name: v("dept-name"), description: v("dept-desc") };
  if (!body.name) return toast("Name required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/departments/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/departments`, { method: "POST", body: JSON.stringify(body) });
    closeModal("dept-modal");
    toast(id ? "Updated" : "Department added!");
    loadDepartments();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteDept(id) {
  if (!confirm("Delete this department?")) return;
  try {
    await fetchJSON(`${API}/api/departments/${id}`, { method: "DELETE" });
    toast("Deleted"); loadDepartments();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Org Chart ───────────────────────────────────────────────────────────────

async function loadOrgChart() {
  const el = document.getElementById("orgchart-container");
  el.innerHTML = `<div class="loading-row"><div class="spinner"></div><span>Loading…</span></div>`;
  try {
    const data = await fetchJSON(`${API}/api/orgchart`);
    if (!data?.departments?.length) {
      el.innerHTML = '<div class="empty-state"><div class="empty-icon">🌳</div><p>No data for org chart</p></div>';
      return;
    }
    el.innerHTML = `
      <div class="orgchart">
        <div class="org-root">
          <div class="org-node root-node">
            <div class="org-icon">🏢</div>
            <div class="org-label">${data.company || "Organization"}</div>
          </div>
        </div>
        <div class="org-depts">
          ${data.departments.map(dept => `
            <div class="org-dept-col">
              <div class="org-node dept-node">
                <div class="org-icon">🏬</div>
                <div class="org-label">${dept.name}</div>
                <div class="org-count">${dept.employees?.length || 0} members</div>
              </div>
              <div class="org-employees">
                ${(dept.employees || []).map(emp => `
                  <div class="org-emp-card clickable" onclick="openProfile(${emp.id})">
                    ${avatarEl(emp, 32)}
                    <div class="org-emp-info">
                      <div class="org-emp-name">${emp.first_name} ${emp.last_name}</div>
                      <div class="org-emp-pos">${emp.position || "—"}</div>
                    </div>
                  </div>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
  }
}

// ─── Attendance ───────────────────────────────────────────────────────────────

async function loadAttendance() {
  loading("att-table");
  try {
    const [records, emps] = await Promise.all([
      fetchJSON(`${API}/api/attendance`),
      fetchJSON(`${API}/api/employees`),
    ]);

    // Summary
    const summaryEl = document.getElementById("att-summary");
    if (summaryEl) {
      const present = records.filter(r => r.status === "present").length;
      const absent  = records.filter(r => r.status === "absent").length;
      const late    = records.filter(r => r.status === "late").length;
      summaryEl.innerHTML = `
        <span class="att-pill present">Present: ${present}</span>
        <span class="att-pill absent">Absent: ${absent}</span>
        <span class="att-pill late">Late: ${late}</span>
      `;
    }

    // Populate emp select in form
    const sel = document.getElementById("att-emp");
    if (sel) {
      sel.innerHTML = '<option value="">Select Employee</option>' +
        emps.map(e => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("");
    }

    const el = document.getElementById("att-table");
    el.innerHTML = records.length ? `
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Date</th><th>Check In</th><th>Check Out</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${records.map(r => {
          const emp = emps.find(e => e.id === r.employee_id);
          return `
            <tr>
              <td>${emp ? `<div style="display:flex;align-items:center;gap:8px">${avatarEl(emp, 30)}<span>${emp.first_name} ${emp.last_name}</span></div>` : r.employee_id}</td>
              <td>${formatDate(r.date)}</td>
              <td>${r.check_in || "—"}</td>
              <td>${r.check_out || "—"}</td>
              <td>${badge(r.status)}</td>
              <td>
                <button class="btn-icon" onclick="editAttendance(${r.id})" title="Edit">✏️</button>
                <button class="btn-icon danger" onclick="deleteAttendance(${r.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `;
        }).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">📅</div><p>No attendance records</p></div>';
  } catch (e) {
    emptyState("att-table", e.message);
  }
}

function openAttForm(data = {}) {
  setVal("att-id", data.id || "");
  setVal("att-emp", data.employee_id || "");
  setVal("att-date", data.date || new Date().toISOString().slice(0, 10));
  setVal("att-checkin", data.check_in || "");
  setVal("att-checkout", data.check_out || "");
  setVal("att-status", data.status || "present");
  document.getElementById("att-modal-title").textContent = data.id ? "Edit Record" : "Add Attendance";
  openModal("att-modal");
}

async function editAttendance(id) {
  const records = await fetchJSON(`${API}/api/attendance`);
  const r = records.find(x => x.id === id);
  if (r) openAttForm(r);
}

async function saveAttendance() {
  const id = v("att-id");
  const body = {
    employee_id: parseInt(v("att-emp")),
    date: v("att-date"),
    check_in: v("att-checkin") || null,
    check_out: v("att-checkout") || null,
    status: v("att-status"),
  };
  if (!body.employee_id || !body.date) return toast("Employee and date required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/attendance/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/attendance`, { method: "POST", body: JSON.stringify(body) });
    closeModal("att-modal");
    toast("Saved"); loadAttendance();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteAttendance(id) {
  if (!confirm("Delete this record?")) return;
  try {
    await fetchJSON(`${API}/api/attendance/${id}`, { method: "DELETE" });
    toast("Deleted"); loadAttendance();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Leaves ───────────────────────────────────────────────────────────────────

async function loadLeaves() {
  loading("leave-table");
  try {
    const [leaves, emps, balances] = await Promise.all([
      fetchJSON(`${API}/api/leaves`),
      fetchJSON(`${API}/api/employees`),
      fetchJSON(`${API}/api/leave-balances`).catch(() => []),
    ]);

    // Leave balances
    const balEl = document.getElementById("leave-balances");
    if (balEl && balances.length) {
      balEl.innerHTML = balances.slice(0, 3).map(b => {
        const annUsed = b.annual_used || 0; const annTotal = b.annual_total || 21;
        const sickUsed = b.sick_used || 0; const sickTotal = b.sick_total || 10;
        const emp = emps.find(e => e.id === b.employee_id);
        return `
          <div class="balance-card">
            <div class="bal-emp">${emp ? `${emp.first_name} ${emp.last_name}` : `Emp #${b.employee_id}`}</div>
            <div class="bal-row">
              <span class="bal-lbl">Annual</span>
              <div class="bal-bar"><div class="bal-fill annual" style="width:${Math.min(100,(annUsed/annTotal)*100)}%"></div></div>
              <span class="bal-num">${annUsed}/${annTotal}</span>
            </div>
            <div class="bal-row">
              <span class="bal-lbl">Sick</span>
              <div class="bal-bar"><div class="bal-fill sick" style="width:${Math.min(100,(sickUsed/sickTotal)*100)}%"></div></div>
              <span class="bal-num">${sickUsed}/${sickTotal}</span>
            </div>
          </div>
        `;
      }).join("");
    }

    // Populate emp select
    const sel = document.getElementById("leave-emp");
    if (sel) {
      sel.innerHTML = '<option value="">Select Employee</option>' +
        emps.map(e => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("");
    }

    const el = document.getElementById("leave-table");
    el.innerHTML = leaves.length ? `
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Type</th><th>From</th><th>To</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${leaves.map(l => {
          const emp = emps.find(e => e.id === l.employee_id);
          return `
            <tr>
              <td>${emp ? `${emp.first_name} ${emp.last_name}` : l.employee_id}</td>
              <td>${l.leave_type}</td>
              <td>${formatDate(l.start_date)}</td>
              <td>${formatDate(l.end_date)}</td>
              <td>${badge(l.status)}</td>
              <td>
                ${l.status === "pending" ? `
                  <button class="btn-sm success" onclick="approveLeave(${l.id})">✓</button>
                  <button class="btn-sm danger"  onclick="rejectLeave(${l.id})">✗</button>
                ` : ""}
                <button class="btn-icon danger" onclick="deleteLeave(${l.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `;
        }).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">🏖️</div><p>No leave requests</p></div>';
  } catch (e) {
    emptyState("leave-table", e.message);
  }
}

function openLeaveForm(data = {}) {
  setVal("leave-id", data.id || "");
  setVal("leave-emp", data.employee_id || "");
  setVal("leave-type", data.leave_type || "annual");
  setVal("leave-start", data.start_date || "");
  setVal("leave-end", data.end_date || "");
  setVal("leave-reason", data.reason || "");
  document.getElementById("leave-modal-title").textContent = data.id ? "Edit Request" : "New Leave Request";
  openModal("leave-modal");
}

async function saveLeave() {
  const id = v("leave-id");
  const body = {
    employee_id: parseInt(v("leave-emp")),
    leave_type: v("leave-type"),
    start_date: v("leave-start"),
    end_date: v("leave-end"),
    reason: v("leave-reason") || null,
  };
  if (!body.employee_id || !body.start_date || !body.end_date) return toast("Fill all required fields", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/leaves/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/leaves`, { method: "POST", body: JSON.stringify(body) });
    closeModal("leave-modal");
    toast("Saved"); loadLeaves();
  } catch (e) { toast(e.message, "error"); }
}

async function approveLeave(id) {
  try {
    await fetchJSON(`${API}/api/leaves/${id}`, { method: "PUT", body: JSON.stringify({ status: "approved" }) });
    toast("Leave approved"); loadLeaves();
  } catch (e) { toast(e.message, "error"); }
}

async function rejectLeave(id) {
  try {
    await fetchJSON(`${API}/api/leaves/${id}`, { method: "PUT", body: JSON.stringify({ status: "rejected" }) });
    toast("Leave rejected", "warning"); loadLeaves();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteLeave(id) {
  if (!confirm("Delete this leave request?")) return;
  try {
    await fetchJSON(`${API}/api/leaves/${id}`, { method: "DELETE" });
    toast("Deleted"); loadLeaves();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Payroll ──────────────────────────────────────────────────────────────────

async function loadPayroll() {
  loading("payroll-table");
  try {
    const [records, emps] = await Promise.all([
      fetchJSON(`${API}/api/payroll`),
      fetchJSON(`${API}/api/employees`),
    ]);

    const total = records.reduce((s, p) => s + (p.net_salary || 0), 0);
    const paid  = records.filter(p => p.status === "paid").length;
    const summEl = document.getElementById("payroll-summary");
    if (summEl) {
      summEl.innerHTML = `
        <div class="stat-mini"><span>Total</span><strong>${formatCurrency(total)}</strong></div>
        <div class="stat-mini"><span>Paid</span><strong>${paid}</strong></div>
        <div class="stat-mini"><span>Pending</span><strong>${records.length - paid}</strong></div>
      `;
    }

    const el = document.getElementById("payroll-table");
    el.innerHTML = records.length ? `
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Period</th><th>Basic</th><th>Allowances</th><th>Deductions</th><th>Net</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${records.map(p => {
          const emp = emps.find(e => e.id === p.employee_id);
          return `
            <tr>
              <td>${emp ? `${emp.first_name} ${emp.last_name}` : p.employee_id}</td>
              <td>${p.period || "—"}</td>
              <td>${formatCurrency(p.basic_salary)}</td>
              <td>${formatCurrency(p.allowances)}</td>
              <td>${formatCurrency(p.deductions)}</td>
              <td><strong>${formatCurrency(p.net_salary)}</strong></td>
              <td>${badge(p.status)}</td>
              <td>
                ${p.status !== "paid" ? `<button class="btn-sm success" onclick="markPaid(${p.id})">Mark Paid</button>` : ""}
                <button class="btn-icon danger" onclick="deletePayroll(${p.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `;
        }).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">💰</div><p>No payroll records</p></div>';
  } catch (e) {
    emptyState("payroll-table", e.message);
  }
}

async function generatePayroll() {
  const emps = await fetchJSON(`${API}/api/employees`);
  const period = new Date().toISOString().slice(0, 7);
  let count = 0;
  for (const e of emps.filter(x => x.status === "active" && x.salary)) {
    const basic = e.salary;
    const allowances = basic * 0.15;
    const deductions = basic * 0.05;
    await fetchJSON(`${API}/api/payroll`, { method: "POST", body: JSON.stringify({
      employee_id: e.id, period, basic_salary: basic,
      allowances, deductions, net_salary: basic + allowances - deductions, status: "pending",
    })}).catch(() => {});
    count++;
  }
  toast(`Generated payroll for ${count} employees`);
  loadPayroll();
}

async function markPaid(id) {
  try {
    await fetchJSON(`${API}/api/payroll/${id}`, { method: "PUT", body: JSON.stringify({ status: "paid" }) });
    toast("Marked as paid"); loadPayroll();
  } catch (e) { toast(e.message, "error"); }
}

async function deletePayroll(id) {
  if (!confirm("Delete this payroll record?")) return;
  try {
    await fetchJSON(`${API}/api/payroll/${id}`, { method: "DELETE" });
    toast("Deleted"); loadPayroll();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Performance ─────────────────────────────────────────────────────────────

async function loadPerformance() {
  loading("perf-table");
  try {
    const [perfs, emps] = await Promise.all([
      fetchJSON(`${API}/api/performance`),
      fetchJSON(`${API}/api/employees`),
    ]);

    const sel = document.getElementById("perf-emp");
    if (sel) {
      sel.innerHTML = '<option value="">Select Employee</option>' +
        emps.map(e => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("");
    }

    const el = document.getElementById("perf-table");
    el.innerHTML = perfs.length ? `
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Period</th><th>Rating</th><th>Goals</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${perfs.map(p => {
          const emp = emps.find(e => e.id === p.employee_id);
          return `
            <tr>
              <td>${emp ? `<div style="display:flex;align-items:center;gap:8px">${avatarEl(emp,30)}<span>${emp.first_name} ${emp.last_name}</span></div>` : p.employee_id}</td>
              <td>${p.period || "—"}</td>
              <td><div class="stars-row">${starsEl(p.rating)}</div></td>
              <td>${p.goals || "—"}</td>
              <td>${badge(p.status)}</td>
              <td>
                <button class="btn-icon" onclick="editPerformance(${p.id})" title="Edit">✏️</button>
                <button class="btn-icon danger" onclick="deletePerformance(${p.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `;
        }).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">🎯</div><p>No reviews yet</p></div>';
  } catch (e) {
    emptyState("perf-table", e.message);
  }
}

function openPerfForm(data = {}) {
  setVal("perf-id", data.id || "");
  setVal("perf-emp", data.employee_id || "");
  setVal("perf-period", data.period || "");
  setVal("perf-rating", data.rating || "3");
  setVal("perf-goals", data.goals || "");
  setVal("perf-achievements", data.achievements || "");
  setVal("perf-improvements", data.areas_improvement || "");
  setVal("perf-notes", data.reviewer_notes || "");
  setVal("perf-status", data.status || "draft");
  document.getElementById("perf-modal-title").textContent = data.id ? "Edit Review" : "New Review";
  openModal("perf-modal");
}

async function editPerformance(id) {
  const perfs = await fetchJSON(`${API}/api/performance`);
  const p = perfs.find(x => x.id === id);
  if (p) openPerfForm(p);
}

async function savePerformance() {
  const id = v("perf-id");
  const body = {
    employee_id: parseInt(v("perf-emp")),
    period: v("perf-period"),
    rating: parseFloat(v("perf-rating")),
    goals: v("perf-goals") || null,
    achievements: v("perf-achievements") || null,
    areas_improvement: v("perf-improvements") || null,
    reviewer_notes: v("perf-notes") || null,
    status: v("perf-status"),
  };
  if (!body.employee_id || !body.period) return toast("Employee and period required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/performance/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/performance`, { method: "POST", body: JSON.stringify(body) });
    closeModal("perf-modal");
    toast("Saved"); loadPerformance();
  } catch (e) { toast(e.message, "error"); }
}

async function deletePerformance(id) {
  if (!confirm("Delete this review?")) return;
  try {
    await fetchJSON(`${API}/api/performance/${id}`, { method: "DELETE" });
    toast("Deleted"); loadPerformance();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Documents ────────────────────────────────────────────────────────────────

async function loadDocuments() {
  loading("doc-grid");
  try {
    const [docs, emps] = await Promise.all([
      fetchJSON(`${API}/api/documents`),
      fetchJSON(`${API}/api/employees`),
    ]);

    const sel = document.getElementById("doc-emp");
    if (sel) {
      sel.innerHTML = '<option value="">Select Employee</option>' +
        emps.map(e => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("");
    }

    const el = document.getElementById("doc-grid");
    el.innerHTML = docs.length ? docs.map(d => {
      const emp = emps.find(e => e.id === d.employee_id);
      return `
        <div class="doc-card">
          <div class="doc-icon">${docTypeIcon(d.doc_type)}</div>
          <div class="doc-body">
            <div class="doc-name">${d.name}</div>
            <div class="doc-emp">${emp ? `${emp.first_name} ${emp.last_name}` : `Emp #${d.employee_id}`}</div>
            <div class="doc-meta">
              <span class="doc-type">${d.doc_type}</span>
              ${docStatusEl(d)}
              ${d.expiry_date ? `<span class="doc-exp">Exp: ${formatDate(d.expiry_date)}</span>` : ""}
            </div>
          </div>
          <div class="doc-actions">
            ${d.file_data ? `<button class="btn-icon" onclick="viewDoc(${d.id})" title="View">👁️</button>` : ""}
            <button class="btn-icon" onclick="editDoc(${d.id})" title="Edit">✏️</button>
            <button class="btn-icon danger" onclick="deleteDoc(${d.id})" title="Delete">🗑️</button>
          </div>
        </div>
      `;
    }).join("") : '<div class="empty-state"><div class="empty-icon">📄</div><p>No documents yet</p></div>';
  } catch (e) {
    emptyState("doc-grid", e.message);
  }
}

function docTypeIcon(type) {
  const icons = { passport: "🛂", visa: "📋", contract: "📝", certificate: "🎓", medical: "🏥", id_card: "💳" };
  return icons[type] || "📄";
}

function openDocForm(data = {}) {
  setVal("doc-id", data.id || "");
  setVal("doc-emp", data.employee_id || "");
  setVal("doc-type", data.doc_type || "contract");
  setVal("doc-name", data.name || "");
  setVal("doc-expiry", data.expiry_date || "");
  setVal("doc-notes", data.notes || "");
  setVal("doc-file-data", data.file_data || "");
  document.getElementById("doc-modal-title").textContent = data.id ? "Edit Document" : "Upload Document";
  openModal("doc-modal");
}

async function editDoc(id) {
  const docs = await fetchJSON(`${API}/api/documents`);
  const d = docs.find(x => x.id === id);
  if (d) openDocForm(d);
}

async function handleDocUpload(input) {
  const file = input.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    setVal("doc-file-data", e.target.result);
    toast("File loaded", "info");
  };
  reader.readAsDataURL(file);
}

async function saveDoc() {
  const id = v("doc-id");
  const body = {
    employee_id: parseInt(v("doc-emp")),
    doc_type: v("doc-type"),
    name: v("doc-name"),
    expiry_date: v("doc-expiry") || null,
    notes: v("doc-notes") || null,
    file_data: v("doc-file-data") || null,
  };
  if (!body.employee_id || !body.name) return toast("Employee and document name required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/documents/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/documents`, { method: "POST", body: JSON.stringify(body) });
    closeModal("doc-modal");
    toast("Saved"); loadDocuments();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteDoc(id) {
  if (!confirm("Delete this document?")) return;
  try {
    await fetchJSON(`${API}/api/documents/${id}`, { method: "DELETE" });
    toast("Deleted"); loadDocuments();
  } catch (e) { toast(e.message, "error"); }
}

async function viewDoc(id) {
  const docs = await fetchJSON(`${API}/api/documents`);
  const d = docs.find(x => x.id === id);
  if (!d?.file_data) return toast("No file attached", "warning");
  const win = window.open();
  win.document.write(`<iframe src="${d.file_data}" style="width:100%;height:100%;border:none;"></iframe>`);
}

// ─── Benefits ────────────────────────────────────────────────────────────────

async function loadBenefits() {
  loading("benefits-table");
  try {
    const [benefits, emps] = await Promise.all([
      fetchJSON(`${API}/api/benefits`),
      fetchJSON(`${API}/api/employees`),
    ]);

    const statsEl = document.getElementById("benefits-stats");
    if (statsEl) {
      const types = [...new Set(benefits.map(b => b.benefit_type))];
      const active = benefits.filter(b => b.status === "active").length;
      const totalCost = benefits.reduce((s, b) => s + (b.cost_monthly || 0), 0);
      statsEl.innerHTML = `
        <div class="stat-mini"><span>Total Benefits</span><strong>${benefits.length}</strong></div>
        <div class="stat-mini"><span>Active</span><strong>${active}</strong></div>
        <div class="stat-mini"><span>Types</span><strong>${types.length}</strong></div>
        <div class="stat-mini"><span>Monthly Cost</span><strong>${formatCurrency(totalCost)}</strong></div>
      `;
    }

    const sel = document.getElementById("ben-emp");
    if (sel) {
      sel.innerHTML = '<option value="">Select Employee</option>' +
        emps.map(e => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("");
    }

    const el = document.getElementById("benefits-table");
    el.innerHTML = benefits.length ? `
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Type</th><th>Provider</th><th>Start</th><th>End</th><th>Monthly Cost</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${benefits.map(b => {
          const emp = emps.find(e => e.id === b.employee_id);
          return `
            <tr>
              <td>${emp ? `${emp.first_name} ${emp.last_name}` : b.employee_id}</td>
              <td>${b.benefit_type}</td>
              <td>${b.provider || "—"}</td>
              <td>${formatDate(b.start_date)}</td>
              <td>${formatDate(b.end_date)}</td>
              <td>${formatCurrency(b.cost_monthly)}</td>
              <td>${badge(b.status)}</td>
              <td>
                <button class="btn-icon" onclick="editBenefit(${b.id})" title="Edit">✏️</button>
                <button class="btn-icon danger" onclick="deleteBenefit(${b.id})" title="Delete">🗑️</button>
              </td>
            </tr>
          `;
        }).join("")}</tbody>
      </table>
    ` : '<div class="empty-state"><div class="empty-icon">🎁</div><p>No benefits configured</p></div>';
  } catch (e) {
    emptyState("benefits-table", e.message);
  }
}

function openBenefitForm(data = {}) {
  setVal("ben-id", data.id || "");
  setVal("ben-emp", data.employee_id || "");
  setVal("ben-type", data.benefit_type || "health_insurance");
  setVal("ben-provider", data.provider || "");
  setVal("ben-coverage", data.coverage_details || "");
  setVal("ben-start", data.start_date || "");
  setVal("ben-end", data.end_date || "");
  setVal("ben-cost", data.cost_monthly || "");
  setVal("ben-status", data.status || "active");
  document.getElementById("ben-modal-title").textContent = data.id ? "Edit Benefit" : "Add Benefit";
  openModal("ben-modal");
}

async function editBenefit(id) {
  const benefits = await fetchJSON(`${API}/api/benefits`);
  const b = benefits.find(x => x.id === id);
  if (b) openBenefitForm(b);
}

async function saveBenefit() {
  const id = v("ben-id");
  const body = {
    employee_id: parseInt(v("ben-emp")),
    benefit_type: v("ben-type"),
    provider: v("ben-provider") || null,
    coverage_details: v("ben-coverage") || null,
    start_date: v("ben-start") || null,
    end_date: v("ben-end") || null,
    cost_monthly: v("ben-cost") ? parseFloat(v("ben-cost")) : null,
    status: v("ben-status"),
  };
  if (!body.employee_id) return toast("Employee required", "warning");
  try {
    if (id) await fetchJSON(`${API}/api/benefits/${id}`, { method: "PUT", body: JSON.stringify(body) });
    else await fetchJSON(`${API}/api/benefits`, { method: "POST", body: JSON.stringify(body) });
    closeModal("ben-modal");
    toast("Saved"); loadBenefits();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteBenefit(id) {
  if (!confirm("Delete this benefit?")) return;
  try {
    await fetchJSON(`${API}/api/benefits/${id}`, { method: "DELETE" });
    toast("Deleted"); loadBenefits();
  } catch (e) { toast(e.message, "error"); }
}

// ─── Modals ───────────────────────────────────────────────────────────────────

function openModal(id) {
  const m = document.getElementById(id);
  if (m) { m.style.display = "flex"; m.classList.add("open"); }
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) { m.style.display = "none"; m.classList.remove("open"); }
}

// Close modals on backdrop click
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    closeModal(e.target.id);
  }
});

// ─── Search & Sidebar ─────────────────────────────────────────────────────────

function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("open");
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Nav click handlers
  document.querySelectorAll(".nav-item[data-page]").forEach(item => {
    item.addEventListener("click", () => showPage(item.dataset.page));
  });

  // Hamburger
  document.getElementById("hamburger")?.addEventListener("click", toggleSidebar);

  // Global search
  const globalSearch = document.getElementById("global-search");
  if (globalSearch) {
    globalSearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const q = globalSearch.value.trim();
        if (q) { showPage("employees"); setTimeout(() => {
          const empSearch = document.getElementById("emp-search");
          if (empSearch) { empSearch.value = q; empSearch.dispatchEvent(new Event("input")); }
        }, 300); }
      }
    });
  }

  showPage("dashboard");
});
