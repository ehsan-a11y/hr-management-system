"""
HR Management System — Vercel Serverless (FastAPI)
All routes prefixed with /api/
SQLite stored in /tmp/ (ephemeral, seeded on cold start)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
import os

# ─── Database ────────────────────────────────────────────────────────────────
DB_PATH = "/tmp/hr_management.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Models ──────────────────────────────────────────────────────────────────
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    hire_date = Column(Date, nullable=False)
    salary = Column(Float, nullable=False)
    status = Column(String(20), default="active")
    address = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)   # stores base64 data-URL
    created_at = Column(DateTime, server_default=func.now())
    department = relationship("Department", back_populates="employees")
    attendance = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")
    payroll = relationship("Payroll", back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(String(10), nullable=True)
    check_out = Column(String(10), nullable=True)
    status = Column(String(20), default="present")
    hours_worked = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="attendance")


class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="leaves")


class Payroll(Base):
    __tablename__ = "payroll"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    bonus = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_status = Column(String(20), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    employee = relationship("Employee", back_populates="payroll")


# ─── Pydantic Schemas ────────────────────────────────────────────────────────
class DeptOut(BaseModel):
    id: int; name: str; description: Optional[str] = None; manager_id: Optional[int] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class DeptCreate(BaseModel):
    name: str; description: Optional[str] = None; manager_id: Optional[int] = None

class EmpOut(BaseModel):
    id: int; employee_id: str; first_name: str; last_name: str; email: str
    phone: Optional[str] = None; position: str; department_id: Optional[int] = None
    hire_date: date; salary: float; status: Optional[str] = "active"
    address: Optional[str] = None; avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    department: Optional[DeptOut] = None
    class Config: from_attributes = True

class EmpCreate(BaseModel):
    employee_id: str; first_name: str; last_name: str; email: str
    phone: Optional[str] = None; position: str; department_id: Optional[int] = None
    hire_date: date; salary: float; status: Optional[str] = "active"
    address: Optional[str] = None; avatar_url: Optional[str] = None

class EmpUpdate(BaseModel):
    first_name: Optional[str] = None; last_name: Optional[str] = None; email: Optional[str] = None
    phone: Optional[str] = None; position: Optional[str] = None; department_id: Optional[int] = None
    salary: Optional[float] = None; status: Optional[str] = None; address: Optional[str] = None
    avatar_url: Optional[str] = None

class AttOut(BaseModel):
    id: int; employee_id: int; date: date; check_in: Optional[str] = None
    check_out: Optional[str] = None; status: Optional[str] = None
    hours_worked: Optional[float] = None; notes: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class AttCreate(BaseModel):
    employee_id: int; date: date; check_in: Optional[str] = None; check_out: Optional[str] = None
    status: Optional[str] = "present"; hours_worked: Optional[float] = 0.0; notes: Optional[str] = None

class AttUpdate(BaseModel):
    check_in: Optional[str] = None; check_out: Optional[str] = None
    status: Optional[str] = None; hours_worked: Optional[float] = None; notes: Optional[str] = None

class LeaveOut(BaseModel):
    id: int; employee_id: int; leave_type: str; start_date: date; end_date: date
    days: int; reason: Optional[str] = None; status: str; approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config: from_attributes = True

class LeaveCreate(BaseModel):
    employee_id: int; leave_type: str; start_date: date; end_date: date
    days: int; reason: Optional[str] = None

class PayrollOut(BaseModel):
    id: int; employee_id: int; month: int; year: int; basic_salary: float
    bonus: float = 0.0; deductions: float = 0.0; tax: float = 0.0; net_salary: float
    payment_date: Optional[date] = None; payment_status: Optional[str] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class PayrollCreate(BaseModel):
    employee_id: int; month: int; year: int; basic_salary: float
    bonus: float = 0.0; deductions: float = 0.0; tax: float = 0.0; net_salary: float
    payment_date: Optional[date] = None; payment_status: Optional[str] = "pending"; notes: Optional[str] = None

class PayrollUpdate(BaseModel):
    bonus: Optional[float] = None; deductions: Optional[float] = None; tax: Optional[float] = None
    net_salary: Optional[float] = None; payment_date: Optional[date] = None
    payment_status: Optional[str] = None; notes: Optional[str] = None


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="HR Management System API", version="1.0.0", redirect_slashes=False)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Create tables + seed data
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        if db.query(Department).count() > 0:
            return
        depts = [
            Department(name="Engineering", description="Software Development"),
            Department(name="Human Resources", description="HR & Recruitment"),
            Department(name="Finance", description="Accounting & Finance"),
            Department(name="Marketing", description="Marketing & Sales"),
            Department(name="Operations", description="Operations & Logistics"),
        ]
        for d in depts:
            db.add(d)
        db.commit()

        today = date.today()
        emps = [
            Employee(employee_id="EMP001", first_name="Alice", last_name="Johnson",
                email="alice@company.com", phone="555-0101", position="Senior Developer",
                department_id=1, hire_date=date(2020, 3, 15), salary=85000, status="active"),
            Employee(employee_id="EMP002", first_name="Bob", last_name="Smith",
                email="bob@company.com", phone="555-0102", position="HR Manager",
                department_id=2, hire_date=date(2019, 7, 1), salary=72000, status="active"),
            Employee(employee_id="EMP003", first_name="Carol", last_name="Williams",
                email="carol@company.com", phone="555-0103", position="Financial Analyst",
                department_id=3, hire_date=date(2021, 1, 10), salary=68000, status="active"),
            Employee(employee_id="EMP004", first_name="David", last_name="Brown",
                email="david@company.com", phone="555-0104", position="Marketing Lead",
                department_id=4, hire_date=date(2022, 5, 20), salary=65000, status="active"),
            Employee(employee_id="EMP005", first_name="Eve", last_name="Davis",
                email="eve@company.com", phone="555-0105", position="Junior Developer",
                department_id=1, hire_date=date(2023, 9, 1), salary=55000, status="active"),
        ]
        for e in emps:
            db.add(e)
        db.commit()

        statuses = ["present", "present", "present", "late", "absent"]
        for i, s in enumerate(statuses, 1):
            db.add(Attendance(
                employee_id=i, date=today,
                check_in="09:00" if s != "absent" else None,
                check_out="18:00" if s == "present" else None,
                status=s, hours_worked=9.0 if s == "present" else 0
            ))
        db.commit()

        db.add(Leave(employee_id=5, leave_type="sick",
            start_date=today, end_date=today + timedelta(days=2), days=3,
            reason="Flu", status="pending"))
        db.add(Leave(employee_id=4, leave_type="annual",
            start_date=today + timedelta(days=5), end_date=today + timedelta(days=9), days=5,
            reason="Vacation", status="approved", approved_by=2))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


seed()

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api")
@app.get("/api/")
def root():
    return {"message": "HR Management System API", "status": "running"}


# Dashboard
@app.get("/api/dashboard/stats")
def dashboard_stats():
    db = SessionLocal()
    try:
        today = date.today()
        return {
            "total_employees": db.query(Employee).count(),
            "active_employees": db.query(Employee).filter(Employee.status == "active").count(),
            "departments": db.query(Department).count(),
            "pending_leaves": db.query(Leave).filter(Leave.status == "pending").count(),
            "present_today": db.query(Attendance).filter(
                Attendance.date == today, Attendance.status == "present").count(),
            "total_payroll_month": round(sum(
                p.net_salary for p in db.query(Payroll).filter(
                    Payroll.month == today.month, Payroll.year == today.year).all()
            ), 2)
        }
    finally:
        db.close()


# ── Departments ──
@app.get("/api/departments/", response_model=List[DeptOut])
def get_departments():
    db = SessionLocal()
    try: return db.query(Department).all()
    finally: db.close()

@app.get("/api/departments/{dept_id}", response_model=DeptOut)
def get_department(dept_id: int):
    db = SessionLocal()
    try:
        d = db.query(Department).filter(Department.id == dept_id).first()
        if not d: raise HTTPException(404, "Not found")
        return d
    finally: db.close()

@app.post("/api/departments/", response_model=DeptOut, status_code=201)
def create_department(dept: DeptCreate):
    db = SessionLocal()
    try:
        if db.query(Department).filter(Department.name == dept.name).first():
            raise HTTPException(400, "Department already exists")
        obj = Department(**dept.dict())
        db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/departments/{dept_id}", response_model=DeptOut)
def update_department(dept_id: int, dept: DeptCreate):
    db = SessionLocal()
    try:
        obj = db.query(Department).filter(Department.id == dept_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in dept.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/departments/{dept_id}")
def delete_department(dept_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Department).filter(Department.id == dept_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Employees ──
@app.get("/api/employees/", response_model=List[EmpOut])
def get_employees(search: Optional[str] = None, department_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Employee).options(joinedload(Employee.department))
        if search:
            q = q.filter(
                (Employee.first_name.ilike(f"%{search}%")) |
                (Employee.last_name.ilike(f"%{search}%")) |
                (Employee.email.ilike(f"%{search}%")) |
                (Employee.employee_id.ilike(f"%{search}%"))
            )
        if department_id: q = q.filter(Employee.department_id == department_id)
        if status: q = q.filter(Employee.status == status)
        result = q.all()
        return [EmpOut.model_validate(e) for e in result]
    finally: db.close()

@app.get("/api/employees/{emp_id}", response_model=EmpOut)
def get_employee(emp_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        return EmpOut.model_validate(obj)
    finally: db.close()

@app.post("/api/employees/", response_model=EmpOut, status_code=201)
def create_employee(emp: EmpCreate):
    db = SessionLocal()
    try:
        if db.query(Employee).filter(Employee.email == emp.email).first():
            raise HTTPException(400, "Email already registered")
        if db.query(Employee).filter(Employee.employee_id == emp.employee_id).first():
            raise HTTPException(400, "Employee ID already exists")
        obj = Employee(**emp.dict()); db.add(obj); db.commit()
        obj = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == obj.id).first()
        return EmpOut.model_validate(obj)
    finally: db.close()

@app.put("/api/employees/{emp_id}", response_model=EmpOut)
def update_employee(emp_id: int, emp: EmpUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Employee).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in emp.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit()
        obj = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == emp_id).first()
        return EmpOut.model_validate(obj)
    finally: db.close()

@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Employee).filter(Employee.id == emp_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Attendance ──
@app.get("/api/attendance/", response_model=List[AttOut])
def get_attendance(employee_id: Optional[int] = None, date_from: Optional[date] = None,
                   date_to: Optional[date] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Attendance)
        if employee_id: q = q.filter(Attendance.employee_id == employee_id)
        if date_from: q = q.filter(Attendance.date >= date_from)
        if date_to: q = q.filter(Attendance.date <= date_to)
        if status: q = q.filter(Attendance.status == status)
        return q.order_by(Attendance.date.desc()).all()
    finally: db.close()

@app.post("/api/attendance/", response_model=AttOut, status_code=201)
def create_attendance(att: AttCreate):
    db = SessionLocal()
    try:
        if db.query(Attendance).filter(
            Attendance.employee_id == att.employee_id, Attendance.date == att.date
        ).first(): raise HTTPException(400, "Attendance already recorded for this date")
        obj = Attendance(**att.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/attendance/{att_id}", response_model=AttOut)
def update_attendance(att_id: int, att: AttUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Attendance).filter(Attendance.id == att_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in att.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/attendance/{att_id}")
def delete_attendance(att_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Attendance).filter(Attendance.id == att_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Leaves ──
@app.get("/api/leaves/", response_model=List[LeaveOut])
def get_leaves(employee_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Leave)
        if employee_id: q = q.filter(Leave.employee_id == employee_id)
        if status: q = q.filter(Leave.status == status)
        return q.order_by(Leave.created_at.desc()).all()
    finally: db.close()

@app.get("/api/leaves/{leave_id}", response_model=LeaveOut)
def get_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        return obj
    finally: db.close()

@app.post("/api/leaves/", response_model=LeaveOut, status_code=201)
def create_leave(leave: LeaveCreate):
    db = SessionLocal()
    try:
        if leave.end_date < leave.start_date: raise HTTPException(400, "End date must be after start date")
        obj = Leave(**leave.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/leaves/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: int, leave: dict):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in leave.items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.patch("/api/leaves/{leave_id}/approve")
def approve_leave(leave_id: int, approved_by: int = 1):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        obj.status = "approved"; obj.approved_by = approved_by
        db.commit(); return {"message": "Leave approved"}
    finally: db.close()

@app.patch("/api/leaves/{leave_id}/reject")
def reject_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        obj.status = "rejected"; db.commit(); return {"message": "Leave rejected"}
    finally: db.close()

@app.delete("/api/leaves/{leave_id}")
def delete_leave(leave_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Leave).filter(Leave.id == leave_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# ── Payroll ──
@app.get("/api/payroll/summary/{month}/{year}")
def payroll_summary(month: int, year: int):
    db = SessionLocal()
    try:
        recs = db.query(Payroll).filter(Payroll.month == month, Payroll.year == year).all()
        return {
            "month": month, "year": year,
            "total_employees": len(recs),
            "total_basic_salary": round(sum(r.basic_salary for r in recs), 2),
            "total_bonus": round(sum(r.bonus for r in recs), 2),
            "total_tax": round(sum(r.tax for r in recs), 2),
            "total_net_salary": round(sum(r.net_salary for r in recs), 2)
        }
    finally: db.close()

@app.get("/api/payroll/", response_model=List[PayrollOut])
def get_payroll(employee_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None):
    db = SessionLocal()
    try:
        q = db.query(Payroll)
        if employee_id: q = q.filter(Payroll.employee_id == employee_id)
        if month: q = q.filter(Payroll.month == month)
        if year: q = q.filter(Payroll.year == year)
        return q.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    finally: db.close()

@app.post("/api/payroll/", response_model=PayrollOut, status_code=201)
def create_payroll(payroll: PayrollCreate):
    db = SessionLocal()
    try:
        if db.query(Payroll).filter(
            Payroll.employee_id == payroll.employee_id,
            Payroll.month == payroll.month,
            Payroll.year == payroll.year
        ).first(): raise HTTPException(400, "Payroll already exists for this period")
        obj = Payroll(**payroll.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/payroll/{payroll_id}", response_model=PayrollOut)
def update_payroll(payroll_id: int, payroll: PayrollUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in payroll.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/payroll/{payroll_id}")
def delete_payroll(payroll_id: int):
    db = SessionLocal()
    try:
        obj = db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()

@app.post("/api/payroll/generate/{month}/{year}")
def generate_payroll(month: int, year: int):
    db = SessionLocal()
    try:
        employees = db.query(Employee).filter(Employee.status == "active").all()
        created = skipped = 0
        for emp in employees:
            if db.query(Payroll).filter(
                Payroll.employee_id == emp.id, Payroll.month == month, Payroll.year == year
            ).first():
                skipped += 1; continue
            tax = emp.salary * 0.1
            db.add(Payroll(
                employee_id=emp.id, month=month, year=year,
                basic_salary=emp.salary, bonus=0.0, deductions=0.0,
                tax=round(tax, 2), net_salary=round(emp.salary - tax, 2),
                payment_status="pending"
            ))
            created += 1
        db.commit()
        return {"message": f"Payroll generated: {created} created, {skipped} skipped"}
    finally: db.close()


# ══════════════════════════════════════════════════════════════════════════════
#  NEW BAYZAT FEATURES
# ══════════════════════════════════════════════════════════════════════════════

# ─── New Models ──────────────────────────────────────────────────────────────

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period = Column(String(50), nullable=False)        # "Q1 2025", "Annual 2025"
    review_date = Column(Date, nullable=False)
    rating = Column(Float, nullable=False)             # 1.0 – 5.0
    goals = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    areas_improvement = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending")     # pending, completed
    created_at = Column(DateTime, server_default=func.now())


class EmployeeDocument(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    doc_type = Column(String(50), nullable=False)      # passport, visa, contract, certificate
    name = Column(String(200), nullable=False)
    file_data = Column(Text, nullable=True)            # base64 data-URL
    expiry_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    year = Column(Integer, nullable=False)
    annual_total = Column(Float, default=21.0)
    annual_used = Column(Float, default=0.0)
    sick_total = Column(Float, default=10.0)
    sick_used = Column(Float, default=0.0)
    emergency_total = Column(Float, default=5.0)
    emergency_used = Column(Float, default=0.0)


class Benefit(Base):
    __tablename__ = "benefits"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    benefit_type = Column(String(100), nullable=False)
    provider = Column(String(100), nullable=True)
    coverage_details = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    cost_monthly = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")   # low, normal, high, urgent
    category = Column(String(50), default="general")  # general, policy, event, alert
    author = Column(String(100), default="HR Team")
    created_at = Column(DateTime, server_default=func.now())


# Create new tables
Base.metadata.create_all(bind=engine)

# ─── New Schemas ─────────────────────────────────────────────────────────────

class ReviewOut(BaseModel):
    id: int; employee_id: int; period: str; review_date: date; rating: float
    goals: Optional[str] = None; achievements: Optional[str] = None
    areas_improvement: Optional[str] = None; reviewer_notes: Optional[str] = None
    status: str; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class ReviewCreate(BaseModel):
    employee_id: int; period: str; review_date: date; rating: float
    goals: Optional[str] = None; achievements: Optional[str] = None
    areas_improvement: Optional[str] = None; reviewer_notes: Optional[str] = None
    status: Optional[str] = "pending"

class ReviewUpdate(BaseModel):
    rating: Optional[float] = None; goals: Optional[str] = None
    achievements: Optional[str] = None; areas_improvement: Optional[str] = None
    reviewer_notes: Optional[str] = None; status: Optional[str] = None

class DocOut(BaseModel):
    id: int; employee_id: int; doc_type: str; name: str
    file_data: Optional[str] = None; expiry_date: Optional[date] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class DocCreate(BaseModel):
    employee_id: int; doc_type: str; name: str
    file_data: Optional[str] = None; expiry_date: Optional[date] = None; notes: Optional[str] = None

class DocUpdate(BaseModel):
    doc_type: Optional[str] = None; name: Optional[str] = None
    file_data: Optional[str] = None; expiry_date: Optional[date] = None; notes: Optional[str] = None

class BalanceOut(BaseModel):
    id: int; employee_id: int; year: int
    annual_total: float; annual_used: float
    sick_total: float; sick_used: float
    emergency_total: float; emergency_used: float
    class Config: from_attributes = True

class BalanceCreate(BaseModel):
    employee_id: int; year: int
    annual_total: float = 21.0; annual_used: float = 0.0
    sick_total: float = 10.0; sick_used: float = 0.0
    emergency_total: float = 5.0; emergency_used: float = 0.0

class BalanceUpdate(BaseModel):
    annual_total: Optional[float] = None; annual_used: Optional[float] = None
    sick_total: Optional[float] = None; sick_used: Optional[float] = None
    emergency_total: Optional[float] = None; emergency_used: Optional[float] = None

class BenefitOut(BaseModel):
    id: int; employee_id: int; benefit_type: str; provider: Optional[str] = None
    coverage_details: Optional[str] = None; start_date: date; end_date: Optional[date] = None
    cost_monthly: float; status: str; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class BenefitCreate(BaseModel):
    employee_id: int; benefit_type: str; provider: Optional[str] = None
    coverage_details: Optional[str] = None; start_date: date; end_date: Optional[date] = None
    cost_monthly: float = 0.0; status: str = "active"

class BenefitUpdate(BaseModel):
    benefit_type: Optional[str] = None; provider: Optional[str] = None
    coverage_details: Optional[str] = None; end_date: Optional[date] = None
    cost_monthly: Optional[float] = None; status: Optional[str] = None

class AnnounceOut(BaseModel):
    id: int; title: str; content: str; priority: str; category: str
    author: str; created_at: Optional[datetime] = None
    class Config: from_attributes = True

class AnnounceCreate(BaseModel):
    title: str; content: str; priority: str = "normal"
    category: str = "general"; author: str = "HR Team"

class AnnounceUpdate(BaseModel):
    title: Optional[str] = None; content: Optional[str] = None
    priority: Optional[str] = None; category: Optional[str] = None


# ─── New Routes ──────────────────────────────────────────────────────────────

# Analytics
@app.get("/api/analytics/")
def get_analytics():
    db = SessionLocal()
    try:
        today = date.today()
        # Employees by department
        depts = db.query(Department).all()
        by_dept = []
        for d in depts:
            count = db.query(Employee).filter(Employee.department_id == d.id, Employee.status == "active").count()
            by_dept.append({"name": d.name, "count": count})

        # Monthly attendance last 6 months
        from datetime import timedelta
        monthly_att = []
        for i in range(5, -1, -1):
            m = (today.month - i - 1) % 12 + 1
            y = today.year - ((today.month - i - 1) // 12)
            present = db.query(Attendance).filter(
                func.strftime('%Y', Attendance.date) == str(y),
                func.strftime('%m', Attendance.date) == f"{m:02d}",
                Attendance.status == "present"
            ).count()
            absent = db.query(Attendance).filter(
                func.strftime('%Y', Attendance.date) == str(y),
                func.strftime('%m', Attendance.date) == f"{m:02d}",
                Attendance.status == "absent"
            ).count()
            monthly_att.append({
                "month": f"{y}-{m:02d}",
                "label": date(y, m, 1).strftime("%b %Y"),
                "present": present, "absent": absent
            })

        # Payroll last 6 months
        monthly_pay = []
        for i in range(5, -1, -1):
            m = (today.month - i - 1) % 12 + 1
            y = today.year - ((today.month - i - 1) // 12)
            recs = db.query(Payroll).filter(Payroll.month == m, Payroll.year == y).all()
            monthly_pay.append({
                "label": date(y, m, 1).strftime("%b %Y"),
                "total": round(sum(r.net_salary for r in recs), 2),
                "count": len(recs)
            })

        # Leave type distribution
        leave_types = {}
        for l in db.query(Leave).all():
            leave_types[l.leave_type] = leave_types.get(l.leave_type, 0) + 1

        # Headcount by status
        statuses = {}
        for e in db.query(Employee).all():
            statuses[e.status] = statuses.get(e.status, 0) + 1

        # Avg rating from performance reviews
        reviews = db.query(PerformanceReview).all()
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 2) if reviews else 0

        return {
            "employees_by_department": by_dept,
            "monthly_attendance": monthly_att,
            "monthly_payroll": monthly_pay,
            "leave_distribution": [{"type": k, "count": v} for k, v in leave_types.items()],
            "headcount_by_status": [{"status": k, "count": v} for k, v in statuses.items()],
            "average_performance_rating": avg_rating,
            "total_reviews": len(reviews),
        }
    finally:
        db.close()


# Org Chart
@app.get("/api/orgchart/")
def get_orgchart():
    db = SessionLocal()
    try:
        depts = db.query(Department).all()
        result = []
        for d in depts:
            emps = db.query(Employee).filter(Employee.department_id == d.id, Employee.status == "active").all()
            result.append({
                "id": d.id, "name": d.name, "description": d.description,
                "manager_id": d.manager_id,
                "employees": [
                    {"id": e.id, "name": f"{e.first_name} {e.last_name}",
                     "position": e.position, "employee_id": e.employee_id,
                     "avatar_url": e.avatar_url}
                    for e in emps
                ]
            })
        return result
    finally:
        db.close()


# Performance Reviews
@app.get("/api/performance/", response_model=List[ReviewOut])
def get_reviews(employee_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(PerformanceReview)
        if employee_id: q = q.filter(PerformanceReview.employee_id == employee_id)
        if status: q = q.filter(PerformanceReview.status == status)
        return q.order_by(PerformanceReview.created_at.desc()).all()
    finally: db.close()

@app.post("/api/performance/", response_model=ReviewOut, status_code=201)
def create_review(r: ReviewCreate):
    db = SessionLocal()
    try:
        obj = PerformanceReview(**r.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/performance/{rid}", response_model=ReviewOut)
def update_review(rid: int, r: ReviewUpdate):
    db = SessionLocal()
    try:
        obj = db.query(PerformanceReview).filter(PerformanceReview.id == rid).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in r.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/performance/{rid}")
def delete_review(rid: int):
    db = SessionLocal()
    try:
        obj = db.query(PerformanceReview).filter(PerformanceReview.id == rid).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# Documents
@app.get("/api/documents/", response_model=List[DocOut])
def get_documents(employee_id: Optional[int] = None, doc_type: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(EmployeeDocument)
        if employee_id: q = q.filter(EmployeeDocument.employee_id == employee_id)
        if doc_type: q = q.filter(EmployeeDocument.doc_type == doc_type)
        return q.order_by(EmployeeDocument.created_at.desc()).all()
    finally: db.close()

@app.post("/api/documents/", response_model=DocOut, status_code=201)
def create_document(doc: DocCreate):
    db = SessionLocal()
    try:
        obj = EmployeeDocument(**doc.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/documents/{did}", response_model=DocOut)
def update_document(did: int, doc: DocUpdate):
    db = SessionLocal()
    try:
        obj = db.query(EmployeeDocument).filter(EmployeeDocument.id == did).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in doc.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/documents/{did}")
def delete_document(did: int):
    db = SessionLocal()
    try:
        obj = db.query(EmployeeDocument).filter(EmployeeDocument.id == did).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# Leave Balances
@app.get("/api/leave-balances/", response_model=List[BalanceOut])
def get_leave_balances(employee_id: Optional[int] = None, year: Optional[int] = None):
    db = SessionLocal()
    try:
        q = db.query(LeaveBalance)
        if employee_id: q = q.filter(LeaveBalance.employee_id == employee_id)
        if year: q = q.filter(LeaveBalance.year == year)
        return q.all()
    finally: db.close()

@app.post("/api/leave-balances/", response_model=BalanceOut, status_code=201)
def create_leave_balance(b: BalanceCreate):
    db = SessionLocal()
    try:
        existing = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == b.employee_id, LeaveBalance.year == b.year
        ).first()
        if existing: raise HTTPException(400, "Balance already exists for this year")
        obj = LeaveBalance(**b.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/leave-balances/{bid}", response_model=BalanceOut)
def update_leave_balance(bid: int, b: BalanceUpdate):
    db = SessionLocal()
    try:
        obj = db.query(LeaveBalance).filter(LeaveBalance.id == bid).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in b.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.post("/api/leave-balances/init/{year}")
def init_leave_balances(year: int):
    """Auto-create leave balances for all active employees for a given year."""
    db = SessionLocal()
    try:
        employees = db.query(Employee).filter(Employee.status == "active").all()
        created = skipped = 0
        for emp in employees:
            if db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == emp.id, LeaveBalance.year == year
            ).first():
                skipped += 1; continue
            db.add(LeaveBalance(employee_id=emp.id, year=year))
            created += 1
        db.commit()
        return {"message": f"Initialized: {created} created, {skipped} skipped"}
    finally: db.close()


# Benefits
@app.get("/api/benefits/", response_model=List[BenefitOut])
def get_benefits(employee_id: Optional[int] = None, status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Benefit)
        if employee_id: q = q.filter(Benefit.employee_id == employee_id)
        if status: q = q.filter(Benefit.status == status)
        return q.order_by(Benefit.created_at.desc()).all()
    finally: db.close()

@app.post("/api/benefits/", response_model=BenefitOut, status_code=201)
def create_benefit(b: BenefitCreate):
    db = SessionLocal()
    try:
        obj = Benefit(**b.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/benefits/{bid}", response_model=BenefitOut)
def update_benefit(bid: int, b: BenefitUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Benefit).filter(Benefit.id == bid).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in b.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/benefits/{bid}")
def delete_benefit(bid: int):
    db = SessionLocal()
    try:
        obj = db.query(Benefit).filter(Benefit.id == bid).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# Announcements
@app.get("/api/announcements/", response_model=List[AnnounceOut])
def get_announcements(priority: Optional[str] = None, category: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Announcement)
        if priority: q = q.filter(Announcement.priority == priority)
        if category: q = q.filter(Announcement.category == category)
        return q.order_by(Announcement.created_at.desc()).all()
    finally: db.close()

@app.post("/api/announcements/", response_model=AnnounceOut, status_code=201)
def create_announcement(a: AnnounceCreate):
    db = SessionLocal()
    try:
        obj = Announcement(**a.dict()); db.add(obj); db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.put("/api/announcements/{aid}", response_model=AnnounceOut)
def update_announcement(aid: int, a: AnnounceUpdate):
    db = SessionLocal()
    try:
        obj = db.query(Announcement).filter(Announcement.id == aid).first()
        if not obj: raise HTTPException(404, "Not found")
        for k, v in a.dict(exclude_unset=True).items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    finally: db.close()

@app.delete("/api/announcements/{aid}")
def delete_announcement(aid: int):
    db = SessionLocal()
    try:
        obj = db.query(Announcement).filter(Announcement.id == aid).first()
        if not obj: raise HTTPException(404, "Not found")
        db.delete(obj); db.commit(); return {"message": "Deleted"}
    finally: db.close()


# Seed new tables
def seed_extended():
    db = SessionLocal()
    try:
        if db.query(Announcement).count() > 0:
            return
        today = date.today()
        # Announcements
        db.add(Announcement(title="Welcome to HR Pro!", content="We've upgraded our HR system with powerful new features. Explore Analytics, Org Chart, Documents, Performance Reviews, and more!", priority="high", category="general", author="HR Team"))
        db.add(Announcement(title="Q1 Performance Reviews Due", content="All managers must complete Q1 performance reviews by end of this month. Log in to the Performance section to get started.", priority="urgent", category="policy", author="Management"))
        db.add(Announcement(title="Health Insurance Renewal", content="Annual health insurance renewals are due. Please review your benefits in the Benefits section and confirm coverage details.", priority="normal", category="event", author="Benefits Team"))
        db.add(Announcement(title="Office Closed on Public Holiday", content="The office will be closed next Monday for the national holiday. Attendance will be marked automatically.", priority="low", category="alert", author="HR Team"))
        db.commit()

        # Leave Balances for current year
        year = today.year
        for emp_id in [1, 2, 3, 4, 5]:
            if db.query(LeaveBalance).filter(LeaveBalance.employee_id == emp_id, LeaveBalance.year == year).first():
                continue
            used = [2.0, 0.0, 1.0, 5.0, 3.0][emp_id - 1]
            sick_used = [1.0, 0.0, 2.0, 0.0, 3.0][emp_id - 1]
            db.add(LeaveBalance(employee_id=emp_id, year=year,
                annual_total=21, annual_used=used,
                sick_total=10, sick_used=sick_used,
                emergency_total=5, emergency_used=0))
        db.commit()

        # Benefits
        benefit_data = [
            (1, "Health Insurance", "AXA Insurance", "Full medical + dental", today.replace(day=1), 450.0),
            (2, "Health Insurance", "AXA Insurance", "Full medical + dental", today.replace(day=1), 450.0),
            (3, "Life Insurance", "MetLife", "$500,000 coverage", today.replace(day=1), 120.0),
            (4, "Health Insurance", "Daman", "Basic medical", today.replace(day=1), 300.0),
            (5, "Health Insurance", "Daman", "Basic medical", today.replace(day=1), 300.0),
            (1, "Life Insurance", "MetLife", "$500,000 coverage", today.replace(day=1), 120.0),
        ]
        for emp_id, btype, provider, coverage, start, cost in benefit_data:
            db.add(Benefit(employee_id=emp_id, benefit_type=btype, provider=provider,
                coverage_details=coverage, start_date=start, cost_monthly=cost, status="active"))
        db.commit()

        # Performance Reviews
        from datetime import timedelta
        reviews = [
            (1, "Q4 2024", today - timedelta(days=30), 4.5, "Deliver new API features", "Completed 3 major APIs on time", "Communication", "Excellent work this quarter", "completed"),
            (2, "Q4 2024", today - timedelta(days=28), 4.0, "Recruit 5 new developers", "Hired 4 developers", "Speed of hiring", "Good performance overall", "completed"),
            (3, "Q4 2024", today - timedelta(days=25), 3.8, "Close quarterly books", "Books closed 2 days early", "Excel skills", "Meeting expectations", "completed"),
            (4, "Q1 2025", today, 0.0, "Launch new campaign", None, None, None, "pending"),
            (5, "Q1 2025", today, 0.0, "Learn React framework", None, None, None, "pending"),
        ]
        for emp_id, period, rdate, rating, goals, achieve, areas, notes, status in reviews:
            db.add(PerformanceReview(employee_id=emp_id, period=period, review_date=rdate,
                rating=rating, goals=goals, achievements=achieve,
                areas_improvement=areas, reviewer_notes=notes, status=status))
        db.commit()

        # Documents
        doc_data = [
            (1, "passport", "Alice Johnson - Passport", today.replace(year=today.year + 5)),
            (1, "contract", "Alice Johnson - Employment Contract", None),
            (2, "passport", "Bob Smith - Passport", today.replace(year=today.year + 3)),
            (2, "visa", "Bob Smith - Work Visa", today + timedelta(days=60)),
            (3, "contract", "Carol Williams - Employment Contract", None),
            (4, "passport", "David Brown - Passport", today.replace(year=today.year + 2)),
            (5, "certificate", "Eve Davis - React Certification", today.replace(year=today.year + 2)),
        ]
        for emp_id, dtype, name, expiry in doc_data:
            db.add(EmployeeDocument(employee_id=emp_id, doc_type=dtype, name=name, expiry_date=expiry))
        db.commit()

        print("✅ Extended seed data created!")
    except Exception as e:
        db.rollback()
        print(f"Extended seed error: {e}")
    finally:
        db.close()


seed_extended()
