/**
 * HR Management System — Frontend Application
 * Pure vanilla JS, communicates with FastAPI backend
 */

const API = "http://localhost:8000";

// ─── Utilities ──────────────────────────────────────────────────────────────

async function fetchJSON(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    throw e;
  }
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${type === "success" ? "✓" : type === "error" ? "✕" : "⚠"}</span> ${msg}`;
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
  };
  return `<span class="badge ${map[status] || "badge-default"}">${status?.replace("_", " ")}</span>`;
}

function initials(first, last) {
  return ((first?.[0] || "") + (last?.[0] || "")).toUpperCase();
}

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function formatCurrency(n) {
  return "$" + (n || 0).toLocaleString("en-US", { minimumFractionDigits: 0 });
}

function loading(id) {
  document.getElementById(id).innerHTML = `
    <div class="loading"><div class="spinner"></div> Loading...</div>`;
}

function emptyState(id, icon, msg) {
  document.getElementById(id).innerHTML = `
    <div class="empty-state"><div class="icon">${icon}</div><p>${msg}</p></div>`;
}

// ─── Navigation ──────────────────────────────────────────────────────────────

function navigate(page) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  document.getElementById(`page-${page}`)?.classList.add("active");
  document.querySelector(`[data-page="${page}"]`)?.classList.add("active");

  const titles = {
    dashboard: "Dashboard", employees: "Employees",
    departments: "Departments", attendance: "Attendance",
    leaves: "Leave Management", payroll: "Payroll",
  };
  document.getElementById("page-title").textContent = titles[page] || page;

  const loaders = {
    dashboard: loadDashboard,
    employees: loadEmployees,
    departments: loadDepartments,
    attendance: loadAttendance,
    leaves: loadLeaves,
    payroll: loadPayroll,
  };
  loaders[page]?.();
}

// ─── Dashboard ──────────────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const [stats, employees, leaves] = await Promise.all([
      fetchJSON(`${API}/dashboard/stats`),
      fetchJSON(`${API}/employees/?limit=5`),
      fetchJSON(`${API}/leaves/?status=pending`),
    ]);

    document.getElementById("stat-total").textContent = stats.total_employees;
    document.getElementById("stat-active").textContent = stats.active_employees;
    document.getElementById("stat-depts").textContent = stats.departments;
    document.getElementById("stat-leaves").textContent = stats.pending_leaves;
    document.getElementById("stat-present").textContent = stats.present_today;
    document.getElementById("stat-payroll").textContent = formatCurrency(stats.total_payroll_month);

    // Recent employees
    const tbody = document.getElementById("recent-employees");
    tbody.innerHTML = employees.map((e) => `
      <tr>
        <td><div class="emp-info">
          <div class="emp-avatar">${initials(e.first_name, e.last_name)}</div>
          <div><div class="name">${e.first_name} ${e.last_name}</div>
          <div class="email">${e.email}</div></div>
        </div></td>
        <td>${e.position}</td>
        <td>${e.department?.name || "—"}</td>
        <td>${badge(e.status)}</td>
      </tr>`).join("") || `<tr><td colspan="4"><div class="empty-state"><p>No employees yet</p></div></td></tr>`;

    // Pending leaves
    const ltbody = document.getElementById("pending-leaves");
    ltbody.innerHTML = leaves.slice(0, 5).map((l) => `
      <tr>
        <td>Employee #${l.employee_id}</td>
        <td>${l.leave_type}</td>
        <td>${l.days} days</td>
        <td>${badge(l.status)}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="approveLeave(${l.id})">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="rejectLeave(${l.id})" style="margin-left:4px">Reject</button>
        </td>
      </tr>`).join("") || `<tr><td colspan="5"><div class="empty-state"><p>No pending leaves</p></div></td></tr>`;
  } catch (e) {
    toast("Failed to load dashboard: " + e.message, "error");
  }
}

// ─── Employees ──────────────────────────────────────────────────────────────

let allEmployees = [];
let departments = [];

async function loadEmployees() {
  loading("employees-tbody");
  try {
    [allEmployees, departments] = await Promise.all([
      fetchJSON(`${API}/employees/`),
      fetchJSON(`${API}/departments/`),
    ]);
    renderEmployeesTable(allEmployees);
    populateDeptFilter();
  } catch (e) {
    toast(e.message, "error");
  }
}

function renderEmployeesTable(data) {
  const tbody = document.getElementById("employees-tbody");
  if (!data.length) {
    emptyState("employees-tbody", "👥", "No employees found");
    return;
  }
  tbody.innerHTML = data.map((e) => `
    <tr>
      <td><div class="emp-info">
        <div class="emp-avatar" style="background:${avatarColor(e.id)}">${initials(e.first_name, e.last_name)}</div>
        <div><div class="name">${e.first_name} ${e.last_name}</div>
        <div class="email">${e.employee_id}</div></div>
      </div></td>
      <td>${e.email}</td>
      <td>${e.position}</td>
      <td>${e.department?.name || "—"}</td>
      <td>${formatCurrency(e.salary)}</td>
      <td>${formatDate(e.hire_date)}</td>
      <td>${badge(e.status)}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditEmployee(${e.id})">✏️</button>
        <button class="btn btn-danger btn-sm btn-icon" onclick="deleteEmployee(${e.id})" style="margin-left:4px">🗑</button>
      </td>
    </tr>`).join("");
}

function avatarColor(id) {
  const colors = ["#4f46e5","#0891b2","#059669","#d97706","#dc2626","#7c3aed","#db2777"];
  return colors[id % colors.length];
}

function populateDeptFilter() {
  const sel = document.getElementById("emp-dept-filter");
  if (!sel) return;
  sel.innerHTML = `<option value="">All Departments</option>` +
    departments.map((d) => `<option value="${d.id}">${d.name}</option>`).join("");
}

function filterEmployees() {
  const search = document.getElementById("emp-search")?.value?.toLowerCase() || "";
  const deptId = document.getElementById("emp-dept-filter")?.value || "";
  const status = document.getElementById("emp-status-filter")?.value || "";

  const filtered = allEmployees.filter((e) => {
    const matchSearch = !search ||
      `${e.first_name} ${e.last_name} ${e.email} ${e.employee_id}`.toLowerCase().includes(search);
    const matchDept = !deptId || String(e.department_id) === deptId;
    const matchStatus = !status || e.status === status;
    return matchSearch && matchDept && matchStatus;
  });
  renderEmployeesTable(filtered);
}

async function openAddEmployee() {
  if (!departments.length) departments = await fetchJSON(`${API}/departments/`);
  const deptOptions = departments.map((d) => `<option value="${d.id}">${d.name}</option>`).join("");
  document.getElementById("modal-title").textContent = "Add Employee";
  document.getElementById("modal-form").innerHTML = `
    <input type="hidden" id="emp-edit-id" value="">
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Employee ID *</label>
        <input class="form-control" id="f-emp-id" placeholder="EMP006" required>
      </div>
      <div class="form-group">
        <label class="form-label">Status</label>
        <select class="form-control" id="f-status">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="on_leave">On Leave</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">First Name *</label>
        <input class="form-control" id="f-first" placeholder="John" required>
      </div>
      <div class="form-group">
        <label class="form-label">Last Name *</label>
        <input class="form-control" id="f-last" placeholder="Doe" required>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Email *</label>
      <input class="form-control" id="f-email" type="email" placeholder="john@company.com" required>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Phone</label>
        <input class="form-control" id="f-phone" placeholder="555-0100">
      </div>
      <div class="form-group">
        <label class="form-label">Hire Date *</label>
        <input class="form-control" id="f-hire" type="date" required>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Position *</label>
        <input class="form-control" id="f-position" placeholder="Software Engineer" required>
      </div>
      <div class="form-group">
        <label class="form-label">Department</label>
        <select class="form-control" id="f-dept"><option value="">— Select —</option>${deptOptions}</select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Salary ($) *</label>
        <input class="form-control" id="f-salary" type="number" placeholder="60000" required>
      </div>
      <div class="form-group">
        <label class="form-label">Address</label>
        <input class="form-control" id="f-address" placeholder="123 Main St">
      </div>
    </div>`;
  openModal("modal-save-btn", saveEmployee);
}

async function openEditEmployee(id) {
  await openAddEmployee();
  const emp = allEmployees.find((e) => e.id === id);
  if (!emp) return;
  document.getElementById("modal-title").textContent = "Edit Employee";
  document.getElementById("emp-edit-id").value = id;
  document.getElementById("f-emp-id").value = emp.employee_id;
  document.getElementById("f-first").value = emp.first_name;
  document.getElementById("f-last").value = emp.last_name;
  document.getElementById("f-email").value = emp.email;
  document.getElementById("f-phone").value = emp.phone || "";
  document.getElementById("f-hire").value = emp.hire_date;
  document.getElementById("f-position").value = emp.position;
  document.getElementById("f-dept").value = emp.department_id || "";
  document.getElementById("f-salary").value = emp.salary;
  document.getElementById("f-address").value = emp.address || "";
  document.getElementById("f-status").value = emp.status;
}

async function saveEmployee() {
  const editId = document.getElementById("emp-edit-id")?.value;
  const body = {
    employee_id: document.getElementById("f-emp-id").value.trim(),
    first_name: document.getElementById("f-first").value.trim(),
    last_name: document.getElementById("f-last").value.trim(),
    email: document.getElementById("f-email").value.trim(),
    phone: document.getElementById("f-phone").value.trim() || null,
    hire_date: document.getElementById("f-hire").value,
    position: document.getElementById("f-position").value.trim(),
    department_id: document.getElementById("f-dept").value ? parseInt(document.getElementById("f-dept").value) : null,
    salary: parseFloat(document.getElementById("f-salary").value),
    address: document.getElementById("f-address").value.trim() || null,
    status: document.getElementById("f-status").value,
  };

  if (!body.first_name || !body.email || !body.hire_date || !body.position || !body.salary) {
    toast("Please fill all required fields", "warning");
    return;
  }

  try {
    if (editId) {
      await fetchJSON(`${API}/employees/${editId}`, { method: "PUT", body: JSON.stringify(body) });
      toast("Employee updated");
    } else {
      await fetchJSON(`${API}/employees/`, { method: "POST", body: JSON.stringify(body) });
      toast("Employee added");
    }
    closeModal();
    loadEmployees();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function deleteEmployee(id) {
  if (!confirm("Delete this employee? This action cannot be undone.")) return;
  try {
    await fetchJSON(`${API}/employees/${id}`, { method: "DELETE" });
    toast("Employee deleted", "warning");
    loadEmployees();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Departments ────────────────────────────────────────────────────────────

let allDepts = [];

async function loadDepartments() {
  loading("depts-tbody");
  try {
    [allDepts, allEmployees] = await Promise.all([
      fetchJSON(`${API}/departments/`),
      fetchJSON(`${API}/employees/`),
    ]);
    renderDepts(allDepts);
  } catch (e) {
    toast(e.message, "error");
  }
}

function renderDepts(data) {
  const tbody = document.getElementById("depts-tbody");
  if (!data.length) { emptyState("depts-tbody", "🏢", "No departments yet"); return; }
  tbody.innerHTML = data.map((d) => {
    const empCount = allEmployees.filter((e) => e.department_id === d.id).length;
    return `<tr>
      <td><strong>${d.name}</strong></td>
      <td>${d.description || "—"}</td>
      <td><span class="badge badge-info">${empCount} employees</span></td>
      <td>${formatDate(d.created_at)}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditDept(${d.id})">✏️</button>
        <button class="btn btn-danger btn-sm btn-icon" onclick="deleteDept(${d.id})" style="margin-left:4px">🗑</button>
      </td>
    </tr>`;
  }).join("");
}

function openAddDept() {
  document.getElementById("modal-title").textContent = "Add Department";
  document.getElementById("modal-form").innerHTML = `
    <input type="hidden" id="dept-edit-id" value="">
    <div class="form-group">
      <label class="form-label">Department Name *</label>
      <input class="form-control" id="f-dept-name" placeholder="Engineering" required>
    </div>
    <div class="form-group">
      <label class="form-label">Description</label>
      <textarea class="form-control" id="f-dept-desc" rows="3" placeholder="Brief description..."></textarea>
    </div>`;
  openModal("modal-save-btn", saveDept);
}

async function openEditDept(id) {
  openAddDept();
  const dept = allDepts.find((d) => d.id === id);
  if (!dept) return;
  document.getElementById("modal-title").textContent = "Edit Department";
  document.getElementById("dept-edit-id").value = id;
  document.getElementById("f-dept-name").value = dept.name;
  document.getElementById("f-dept-desc").value = dept.description || "";
}

async function saveDept() {
  const editId = document.getElementById("dept-edit-id")?.value;
  const body = {
    name: document.getElementById("f-dept-name").value.trim(),
    description: document.getElementById("f-dept-desc").value.trim() || null,
  };
  if (!body.name) { toast("Department name required", "warning"); return; }
  try {
    if (editId) {
      await fetchJSON(`${API}/departments/${editId}`, { method: "PUT", body: JSON.stringify(body) });
      toast("Department updated");
    } else {
      await fetchJSON(`${API}/departments/`, { method: "POST", body: JSON.stringify(body) });
      toast("Department added");
    }
    closeModal();
    loadDepartments();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function deleteDept(id) {
  if (!confirm("Delete this department?")) return;
  try {
    await fetchJSON(`${API}/departments/${id}`, { method: "DELETE" });
    toast("Department deleted", "warning");
    loadDepartments();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Attendance ──────────────────────────────────────────────────────────────

async function loadAttendance() {
  loading("att-tbody");
  try {
    const today = new Date().toISOString().split("T")[0];
    const [records, emps] = await Promise.all([
      fetchJSON(`${API}/attendance/?date_from=${today}&date_to=${today}`),
      fetchJSON(`${API}/employees/`),
    ]);
    renderAttendance(records, emps);
  } catch (e) {
    toast(e.message, "error");
  }
}

function renderAttendance(records, emps) {
  const tbody = document.getElementById("att-tbody");
  const empMap = Object.fromEntries(emps.map((e) => [e.id, e]));

  if (!records.length) { emptyState("att-tbody", "📋", "No attendance records for today"); return; }

  tbody.innerHTML = records.map((r) => {
    const emp = empMap[r.employee_id] || {};
    return `<tr>
      <td><div class="emp-info">
        <div class="emp-avatar" style="background:${avatarColor(r.employee_id)}">${initials(emp.first_name, emp.last_name)}</div>
        <div><div class="name">${emp.first_name || "?"} ${emp.last_name || ""}</div>
        <div class="email">${emp.employee_id || ""}</div></div>
      </div></td>
      <td>${formatDate(r.date)}</td>
      <td>${r.check_in || "—"}</td>
      <td>${r.check_out || "—"}</td>
      <td>${r.hours_worked || 0}h</td>
      <td>${badge(r.status)}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditAtt(${r.id})">✏️</button>
      </td>
    </tr>`;
  }).join("");
}

async function openMarkAttendance() {
  const emps = await fetchJSON(`${API}/employees/?status=active`);
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("modal-title").textContent = "Mark Attendance";
  document.getElementById("modal-form").innerHTML = `
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Employee *</label>
        <select class="form-control" id="f-att-emp">
          <option value="">— Select Employee —</option>
          ${emps.map((e) => `<option value="${e.id}">${e.first_name} ${e.last_name} (${e.employee_id})</option>`).join("")}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Date *</label>
        <input class="form-control" id="f-att-date" type="date" value="${today}" required>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Check In</label>
        <input class="form-control" id="f-att-in" type="time">
      </div>
      <div class="form-group">
        <label class="form-label">Check Out</label>
        <input class="form-control" id="f-att-out" type="time">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Status</label>
        <select class="form-control" id="f-att-status">
          <option value="present">Present</option>
          <option value="absent">Absent</option>
          <option value="late">Late</option>
          <option value="half_day">Half Day</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Hours Worked</label>
        <input class="form-control" id="f-att-hours" type="number" step="0.5" placeholder="8">
      </div>
    </div>`;
  openModal("modal-save-btn", saveAttendance);
}

async function saveAttendance() {
  const body = {
    employee_id: parseInt(document.getElementById("f-att-emp").value),
    date: document.getElementById("f-att-date").value,
    check_in: document.getElementById("f-att-in").value || null,
    check_out: document.getElementById("f-att-out").value || null,
    status: document.getElementById("f-att-status").value,
    hours_worked: parseFloat(document.getElementById("f-att-hours").value) || 0,
  };
  if (!body.employee_id || !body.date) { toast("Please select employee and date", "warning"); return; }
  try {
    await fetchJSON(`${API}/attendance/`, { method: "POST", body: JSON.stringify(body) });
    toast("Attendance marked");
    closeModal();
    loadAttendance();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Leaves ──────────────────────────────────────────────────────────────────

async function loadLeaves() {
  loading("leaves-tbody");
  try {
    const [leaves, emps] = await Promise.all([
      fetchJSON(`${API}/leaves/`),
      fetchJSON(`${API}/employees/`),
    ]);
    renderLeaves(leaves, emps);
  } catch (e) {
    toast(e.message, "error");
  }
}

function renderLeaves(leaves, emps) {
  const tbody = document.getElementById("leaves-tbody");
  const empMap = Object.fromEntries(emps.map((e) => [e.id, e]));

  if (!leaves.length) { emptyState("leaves-tbody", "🌴", "No leave requests"); return; }

  tbody.innerHTML = leaves.map((l) => {
    const emp = empMap[l.employee_id] || {};
    return `<tr>
      <td><div class="emp-info">
        <div class="emp-avatar" style="background:${avatarColor(l.employee_id)}">${initials(emp.first_name, emp.last_name)}</div>
        <div class="name">${emp.first_name || "?"} ${emp.last_name || ""}</div>
      </div></td>
      <td><span class="badge badge-info">${l.leave_type}</span></td>
      <td>${formatDate(l.start_date)}</td>
      <td>${formatDate(l.end_date)}</td>
      <td>${l.days} days</td>
      <td>${l.reason || "—"}</td>
      <td>${badge(l.status)}</td>
      <td>
        ${l.status === "pending" ? `
          <button class="btn btn-success btn-sm" onclick="approveLeave(${l.id})">✓</button>
          <button class="btn btn-danger btn-sm btn-icon" onclick="rejectLeave(${l.id})" style="margin-left:4px">✕</button>
        ` : ""}
        <button class="btn btn-danger btn-sm btn-icon" onclick="deleteLeave(${l.id})" style="margin-left:4px">🗑</button>
      </td>
    </tr>`;
  }).join("");
}

async function openAddLeave() {
  const emps = await fetchJSON(`${API}/employees/?status=active`);
  document.getElementById("modal-title").textContent = "Request Leave";
  document.getElementById("modal-form").innerHTML = `
    <div class="form-group">
      <label class="form-label">Employee *</label>
      <select class="form-control" id="f-leave-emp">
        <option value="">— Select Employee —</option>
        ${emps.map((e) => `<option value="${e.id}">${e.first_name} ${e.last_name}</option>`).join("")}
      </select>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Leave Type *</label>
        <select class="form-control" id="f-leave-type">
          <option value="annual">Annual</option>
          <option value="sick">Sick</option>
          <option value="maternity">Maternity</option>
          <option value="paternity">Paternity</option>
          <option value="emergency">Emergency</option>
          <option value="unpaid">Unpaid</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Days *</label>
        <input class="form-control" id="f-leave-days" type="number" min="1" placeholder="3">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Start Date *</label>
        <input class="form-control" id="f-leave-start" type="date" required>
      </div>
      <div class="form-group">
        <label class="form-label">End Date *</label>
        <input class="form-control" id="f-leave-end" type="date" required>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Reason</label>
      <textarea class="form-control" id="f-leave-reason" rows="3" placeholder="Brief reason..."></textarea>
    </div>`;
  openModal("modal-save-btn", saveLeave);
}

async function saveLeave() {
  const body = {
    employee_id: parseInt(document.getElementById("f-leave-emp").value),
    leave_type: document.getElementById("f-leave-type").value,
    start_date: document.getElementById("f-leave-start").value,
    end_date: document.getElementById("f-leave-end").value,
    days: parseInt(document.getElementById("f-leave-days").value),
    reason: document.getElementById("f-leave-reason").value.trim() || null,
  };
  if (!body.employee_id || !body.start_date || !body.end_date || !body.days) {
    toast("Please fill all required fields", "warning"); return;
  }
  try {
    await fetchJSON(`${API}/leaves/`, { method: "POST", body: JSON.stringify(body) });
    toast("Leave request submitted");
    closeModal();
    loadLeaves();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function approveLeave(id) {
  try {
    await fetchJSON(`${API}/leaves/${id}/approve`, { method: "PATCH" });
    toast("Leave approved");
    loadLeaves();
    if (document.getElementById("page-dashboard").classList.contains("active")) loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function rejectLeave(id) {
  try {
    await fetchJSON(`${API}/leaves/${id}/reject`, { method: "PATCH" });
    toast("Leave rejected", "warning");
    loadLeaves();
    if (document.getElementById("page-dashboard").classList.contains("active")) loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function deleteLeave(id) {
  if (!confirm("Delete this leave request?")) return;
  try {
    await fetchJSON(`${API}/leaves/${id}`, { method: "DELETE" });
    toast("Leave deleted", "warning");
    loadLeaves();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Payroll ─────────────────────────────────────────────────────────────────

async function loadPayroll() {
  loading("payroll-tbody");
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();
  document.getElementById("payroll-month-sel").value = month;
  document.getElementById("payroll-year-sel").value = year;
  await fetchPayroll(month, year);
}

async function fetchPayroll(month, year) {
  loading("payroll-tbody");
  try {
    const [records, emps, summary] = await Promise.all([
      fetchJSON(`${API}/payroll/?month=${month}&year=${year}`),
      fetchJSON(`${API}/employees/`),
      fetchJSON(`${API}/payroll/summary/${month}/${year}`),
    ]);
    const empMap = Object.fromEntries(emps.map((e) => [e.id, e]));
    renderPayroll(records, empMap);
    renderPayrollSummary(summary);
  } catch (e) {
    toast(e.message, "error");
  }
}

function renderPayroll(records, empMap) {
  const tbody = document.getElementById("payroll-tbody");
  if (!records.length) { emptyState("payroll-tbody", "💰", "No payroll records. Click 'Generate Payroll'."); return; }
  tbody.innerHTML = records.map((p) => {
    const emp = empMap[p.employee_id] || {};
    return `<tr>
      <td><div class="emp-info">
        <div class="emp-avatar" style="background:${avatarColor(p.employee_id)}">${initials(emp.first_name, emp.last_name)}</div>
        <div class="name">${emp.first_name || "?"} ${emp.last_name || ""}</div>
      </div></td>
      <td>${formatCurrency(p.basic_salary)}</td>
      <td>${formatCurrency(p.bonus)}</td>
      <td>${formatCurrency(p.deductions)}</td>
      <td>${formatCurrency(p.tax)}</td>
      <td><strong>${formatCurrency(p.net_salary)}</strong></td>
      <td>${badge(p.payment_status)}</td>
      <td>
        ${p.payment_status === "pending" ? `<button class="btn btn-success btn-sm" onclick="markPaid(${p.id})">Mark Paid</button>` : ""}
        <button class="btn btn-danger btn-sm btn-icon" onclick="deletePayroll(${p.id})" style="margin-left:4px">🗑</button>
      </td>
    </tr>`;
  }).join("");
}

function renderPayrollSummary(s) {
  document.getElementById("payroll-summary").innerHTML = `
    <div class="stats-grid" style="margin-bottom:0">
      <div class="stat-card"><div class="stat-icon blue">👥</div><div class="stat-info"><h3>${s.total_employees}</h3><p>Employees</p></div></div>
      <div class="stat-card"><div class="stat-icon green">💵</div><div class="stat-info"><h3>${formatCurrency(s.total_basic_salary)}</h3><p>Total Basic</p></div></div>
      <div class="stat-card"><div class="stat-icon yellow">🎁</div><div class="stat-info"><h3>${formatCurrency(s.total_bonus)}</h3><p>Total Bonus</p></div></div>
      <div class="stat-card"><div class="stat-icon red">🧾</div><div class="stat-info"><h3>${formatCurrency(s.total_tax)}</h3><p>Total Tax</p></div></div>
      <div class="stat-card"><div class="stat-icon purple">💰</div><div class="stat-info"><h3>${formatCurrency(s.total_net_salary)}</h3><p>Net Payroll</p></div></div>
    </div>`;
}

async function generatePayroll() {
  const month = document.getElementById("payroll-month-sel").value;
  const year = document.getElementById("payroll-year-sel").value;
  if (!confirm(`Generate payroll for ${month}/${year}?`)) return;
  try {
    const res = await fetchJSON(`${API}/payroll/generate/${month}/${year}`, { method: "POST" });
    toast(res.message);
    fetchPayroll(month, year);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function markPaid(id) {
  try {
    const today = new Date().toISOString().split("T")[0];
    await fetchJSON(`${API}/payroll/${id}`, {
      method: "PUT",
      body: JSON.stringify({ payment_status: "paid", payment_date: today }),
    });
    toast("Marked as paid");
    const month = document.getElementById("payroll-month-sel").value;
    const year = document.getElementById("payroll-year-sel").value;
    fetchPayroll(month, year);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function deletePayroll(id) {
  if (!confirm("Delete this payroll record?")) return;
  try {
    await fetchJSON(`${API}/payroll/${id}`, { method: "DELETE" });
    toast("Payroll record deleted", "warning");
    const month = document.getElementById("payroll-month-sel").value;
    const year = document.getElementById("payroll-year-sel").value;
    fetchPayroll(month, year);
  } catch (e) {
    toast(e.message, "error");
  }
}

// ─── Modal ───────────────────────────────────────────────────────────────────

let currentSaveFn = null;

function openModal(saveBtnId, saveFn) {
  currentSaveFn = saveFn;
  document.getElementById("global-modal").classList.add("open");
  const btn = document.getElementById("modal-save-btn");
  btn.onclick = saveFn;
}

function closeModal() {
  document.getElementById("global-modal").classList.remove("open");
  currentSaveFn = null;
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Navigation
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => navigate(item.dataset.page));
  });

  // Modal close
  document.getElementById("global-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Payroll month/year selectors
  const now = new Date();
  const monthSel = document.getElementById("payroll-month-sel");
  const yearSel = document.getElementById("payroll-year-sel");
  if (monthSel) {
    for (let y = now.getFullYear(); y >= now.getFullYear() - 3; y--) {
      yearSel.innerHTML += `<option value="${y}">${y}</option>`;
    }
    monthSel.addEventListener("change", () => fetchPayroll(monthSel.value, yearSel.value));
    yearSel.addEventListener("change", () => fetchPayroll(monthSel.value, yearSel.value));
  }

  // Start on dashboard
  navigate("dashboard");
});
