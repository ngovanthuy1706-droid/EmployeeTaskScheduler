from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Employee, Task, Assignment
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

def get_week_days(reference_date=None):
    if not reference_date:
        reference_date = datetime.strptime('2025-05-19', '%Y-%m-%d').date()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
    
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    days = []
    day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
    for i in range(6):
        day_date = start_of_week + timedelta(days=i)
        days.append({
            'name': day_names[i],
            'date_str': day_date.strftime('%Y-%m-%d'),
            'display_date': day_date.strftime('%d/%m')
        })
    return days, start_of_week

@main_bp.route('/')
def dashboard():
    today_str = request.args.get('date', '2025-05-19')
    
    employees = Employee.query.all()
    tasks = Task.query.all()
    
    total_employees = len(employees)
    total_tasks = len(tasks)
    total_assignments = Assignment.query.count()
    
    today_assignments = Assignment.query.filter_by(work_date=today_str).all()
    working_today_emp_ids = set(a.employee_id for a in today_assignments)
    today_working_count = len(working_today_emp_ids)
    
    today_task_list = []
    for a in today_assignments:
        today_task_list.append({
            'time': '07:30' if a.shift == 'morning' else '13:00',
            'employee_name': a.employee.name if a.employee else 'NV',
            'task_name': a.task.name if a.task else 'Công việc',
            'shift': 'Sáng' if a.shift == 'morning' else 'Chiều',
            'shift_badge_class': 'badge-morning' if a.shift == 'morning' else 'badge-afternoon'
        })
    today_task_list.sort(key=lambda x: x['time'])

    week_days, start_of_week = get_week_days(today_str)
    week_start_str = week_days[0]['display_date'] + '/2025'
    week_end_str = week_days[-1]['display_date'] + '/2025'

    schedule_matrix = []
    for emp in employees:
        emp_schedule = {
            'employee': emp,
            'days': {}
        }
        for d in week_days:
            date_key = d['date_str']
            morning_assign = Assignment.query.filter_by(employee_id=emp.id, work_date=date_key, shift='morning').first()
            afternoon_assign = Assignment.query.filter_by(employee_id=emp.id, work_date=date_key, shift='afternoon').first()
            
            emp_schedule['days'][date_key] = {
                'morning': morning_assign.task.name if morning_assign and morning_assign.task else 'Dự phòng',
                'morning_id': morning_assign.id if morning_assign else None,
                'afternoon': afternoon_assign.task.name if afternoon_assign and afternoon_assign.task else 'Dự phòng',
                'afternoon_id': afternoon_assign.id if afternoon_assign else None
            }
        schedule_matrix.append(emp_schedule)

    return render_template('dashboard.html',
                           total_employees=total_employees or 25,
                           total_tasks=total_tasks or 18,
                           total_assignments=total_assignments or 62,
                           today_working_count=today_working_count or 12,
                           employees=employees,
                           tasks=tasks,
                           today_str=today_str,
                           today_task_list=today_task_list,
                           week_days=week_days,
                           week_start_str=week_start_str,
                           week_end_str=week_end_str,
                           schedule_matrix=schedule_matrix)

@main_bp.route('/assign', methods=['POST'])
def assign_task():
    employee_id = request.form.get('employee_id', type=int)
    task_id = request.form.get('task_id', type=int)
    work_date = request.form.get('work_date')
    shift = request.form.get('shift')

    if employee_id and task_id and work_date and shift:
        existing = Assignment.query.filter_by(employee_id=employee_id, work_date=work_date, shift=shift).first()
        if existing:
            existing.task_id = task_id
        else:
            new_assign = Assignment(employee_id=employee_id, task_id=task_id, work_date=work_date, shift=shift)
            db.session.add(new_assign)
        db.session.commit()
        flash('Lưu phân công thành công!', 'success')
    else:
        flash('Vui lòng nhập đầy đủ thông tin phân công!', 'danger')
        
    return redirect(url_for('main.dashboard', date=work_date or '2025-05-19'))

@main_bp.route('/employees', methods=['GET', 'POST'])
def employees():
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        if name and department:
            avatar = f"https://ui-avatars.com/api/?name={name}&background=0D6EFD&color=fff"
            new_emp = Employee(name=name, department=department, avatar_url=avatar)
            db.session.add(new_emp)
            db.session.commit()
            flash('Thêm nhân viên thành công!', 'success')
            return redirect(url_for('main.employees'))
            
    emp_list = Employee.query.all()
    return render_template('employees.html', employees=emp_list)

@main_bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        if name:
            new_task = Task(name=name, department=department or 'Chung')
            db.session.add(new_task)
            db.session.commit()
            flash('Thêm công việc thành công!', 'success')
            return redirect(url_for('main.tasks'))
            
    task_list = Task.query.all()
    return render_template('tasks.html', tasks=task_list)

@main_bp.route('/report')
def report():
    employees = Employee.query.all()
    tasks = Task.query.all()
    assignments = Assignment.query.all()
    return render_template('report.html',
                           employees=employees,
                           tasks=tasks,
                           assignments=assignments)
