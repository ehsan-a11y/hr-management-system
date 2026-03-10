"""
HR Management System - Main FastAPI Application
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

from database import engine, Base, SessionLocal
import models
from routers import departments, employees, attendance, leaves, payroll
from schemas import DashboardStats

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HR Management System",
    description="Complete HR Management API with Employees, Attendance, Leaves & Payroll",
    version="1.0.0"
)

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(payroll.router)


@app.get("/")
def root():
    return {"message": "HR Management System API is running", "docs": "/docs"}


@app.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats():
    """Get key stats for the dashboard."""
    db: Session = SessionLocal()
    try:
        today = date.today()
        total_employees = db.query(models.Employee).count()
        active_employees = db.query(models.Employee).filter(models.Employee.status == "active").count()
        departments = db.query(models.Department).count()
        pending_leaves = db.query(models.Leave).filter(models.Leave.status == "pending").count()
        present_today = db.query(models.Attendance).filter(
            models.Attendance.date == today,
            models.Attendance.status == "present"
        ).count()

        # Current month payroll total
        current_month = today.month
        current_year = today.year
        payroll_records = db.query(models.Payroll).filter(
            models.Payroll.month == current_month,
            models.Payroll.year == current_year
        ).all()
        total_payroll = sum(p.net_salary for p in payroll_records)

        return DashboardStats(
            total_employees=total_employees,
            active_employees=active_employees,
            departments=departments,
            pending_leaves=pending_leaves,
            present_today=present_today,
            total_payroll_month=round(total_payroll, 2)
        )
    finally:
        db.close()


@app.on_event("startup")
def seed_sample_data():
    """Seed database with sample data on first run."""
    db: Session = SessionLocal()
    try:
        # Only seed if empty
        if db.query(models.Department).count() > 0:
            return

        # Create departments
        depts = [
            models.Department(name="Engineering", description="Software Development Team"),
            models.Department(name="Human Resources", description="HR & Recruitment"),
            models.Department(name="Finance", description="Accounting & Finance"),
            models.Department(name="Marketing", description="Marketing & Sales"),
            models.Department(name="Operations", description="Operations & Logistics"),
        ]
        for d in depts:
            db.add(d)
        db.commit()

        # Create sample employees
        from datetime import date as dt
        employees_data = [
            models.Employee(employee_id="EMP001", first_name="Alice", last_name="Johnson",
                email="alice@company.com", phone="555-0101", position="Senior Developer",
                department_id=1, hire_date=dt(2020, 3, 15), salary=85000, status="active"),
            models.Employee(employee_id="EMP002", first_name="Bob", last_name="Smith",
                email="bob@company.com", phone="555-0102", position="HR Manager",
                department_id=2, hire_date=dt(2019, 7, 1), salary=72000, status="active"),
            models.Employee(employee_id="EMP003", first_name="Carol", last_name="Williams",
                email="carol@company.com", phone="555-0103", position="Financial Analyst",
                department_id=3, hire_date=dt(2021, 1, 10), salary=68000, status="active"),
            models.Employee(employee_id="EMP004", first_name="David", last_name="Brown",
                email="david@company.com", phone="555-0104", position="Marketing Lead",
                department_id=4, hire_date=dt(2022, 5, 20), salary=65000, status="active"),
            models.Employee(employee_id="EMP005", first_name="Eve", last_name="Davis",
                email="eve@company.com", phone="555-0105", position="Junior Developer",
                department_id=1, hire_date=dt(2023, 9, 1), salary=55000, status="active"),
        ]
        for e in employees_data:
            db.add(e)
        db.commit()

        # Attendance today
        today = dt.today()
        for i, emp_id in enumerate([1, 2, 3, 4, 5], 1):
            statuses = ["present", "present", "present", "late", "absent"]
            db.add(models.Attendance(
                employee_id=emp_id,
                date=today,
                check_in="09:00" if statuses[i-1] != "absent" else None,
                check_out="18:00" if statuses[i-1] == "present" else None,
                status=statuses[i-1],
                hours_worked=9.0 if statuses[i-1] == "present" else 0
            ))
        db.commit()

        # Sample leave requests
        from datetime import timedelta
        db.add(models.Leave(employee_id=5, leave_type="sick",
            start_date=today, end_date=today + timedelta(days=2), days=3,
            reason="Flu", status="pending"))
        db.add(models.Leave(employee_id=4, leave_type="annual",
            start_date=today + timedelta(days=5), end_date=today + timedelta(days=9), days=5,
            reason="Family vacation", status="approved", approved_by=2))
        db.commit()

        print("✅ Sample data seeded successfully!")
    except Exception as e:
        print(f"Seed error (ignored): {e}")
    finally:
        db.close()
