import os
import json
import datetime
import random
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_employee_task_scheduler'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

EMP_FILE = os.path.join(DATA_DIR, 'employees.json')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.json')
SCH_FILE = os.path.join(DATA_DIR, 'schedule.json')
LEAVE_FILE = os.path.join(DATA_DIR, 'leaves.json')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)


# HÀM BỐC NGẪU NHIÊN 1 CÔNG VIỆC TRONG CHUỖI NHIỀU CÔNG VIỆC
def pick_one_task(task_string):
    if not task_string or str(task_string).strip() in ['nan', 'None', '']:
        return 'Làm việc'
    
    task_str = str(task_string).strip()
    if ',' in task_str:
        tasks = [t.strip() for t in task_str.split(',') if t.strip()]
        if tasks:
            return random.choice(tasks) # Bốc tùy ý 1 công việc
    return task_str


def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi đọc file {file_path}: {e}")
            return []
    return []

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '123456':
            session['user'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Tài khoản hoặc mật khẩu không đúng!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# 1. TRANG DASHBOARD - THỜI KHÓA BIỂU (TỰ ĐỘNG CHỌN 1 CÔNG VIỆC TỪ DANH SÁCH ĐỂ HIỂN THỊ)
@app.route('/')
@app.route('/dashboard')
def dashboard():
    employees = load_data(EMP_FILE)
    schedule = load_data(SCH_FILE)

    week_offset = request.args.get('week_offset', 0, type=int)
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=week_offset)
    
    week_days = []
    day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ Nhật']
    for i in range(7):
        d = start_of_week + datetime.timedelta(days=i)
        week_days.append({
            'date_str': d.strftime('%Y-%m-%d'),
            'display_date': d.strftime('%d/%m'),
            'day_name': day_names[i]
        })

    end_of_week = start_of_week + datetime.timedelta(days=6)

    tkb_grid = {
        'Sáng': {day['date_str']: [] for day in week_days},
        'Chiều': {day['date_str']: [] for day in week_days}
    }

    filtered_count = 0
    for s in schedule:
        try:
            item_date = s['date']
            shift_raw = str(s.get('shift', '')).strip().lower()
            shift_key = 'Chiều' if any(k in shift_raw for k in ['chiều', 'chieu', 'ca 2', 'ca2', '2']) else 'Sáng'
            
            # CHỈ KHI HIỂN THỊ LÊN BẢNG TKB MỚI CHỌN 1 CÔNG VIỆC TÙY Ý
            raw_task = str(s.get('task_name', 'Làm việc'))
            display_item = dict(s)
            display_item['task_name'] = pick_one_task(raw_task)

            if item_date in tkb_grid[shift_key]:
                tkb_grid[shift_key][item_date].append(display_item)
                filtered_count += 1
        except Exception as e:
            print(f"Lỗi TKB: {e}")

    return render_template(
        'dashboard.html',
        employees=employees, schedule=schedule,
        tkb_grid=tkb_grid, week_days=week_days, filtered_count=filtered_count,
        start_of_week=start_of_week.strftime('%d/%m/%Y'),
        end_of_week=end_of_week.strftime('%d/%m/%Y'),
        week_offset=week_offset, today_date=today.strftime('%Y-%m-%d')
    )


# 2. UPLOAD EXCEL LỊCH PHÂN CÔNG (GÁN CÔNG VIỆC TỪ BẢNG NHÂN VIÊN SANG)
@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    week_offset = request.form.get('week_offset', 0)
    if 'excel_file' in request.files:
        file = request.files['excel_file']
        if file and file.filename != '' and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            try:
                df = pd.read_excel(file, engine='openpyxl')
                df.columns = df.columns.astype(str).str.strip().str.upper()

                column_mapping = {
                    'TÊN': 'emp_name', 'HO TÊN': 'emp_name', 'HỌ TÊN': 'emp_name', 'NHÂN VIÊN': 'emp_name',
                    'CA LÀM': 'shift', 'CA': 'shift', 'BUỔI': 'shift',
                    'THỜI GIAN': 'date', 'NGÀY LÀM': 'date', 'NGÀY': 'date',
                    'CÔNG VIỆC': 'task_name', 'NHIỆM VỤ': 'task_name'
                }
                df = df.rename(columns=column_mapping)

                def clean_shift(val):
                    v = str(val).strip().lower()
                    return 'Chiều' if any(k in v for k in ['chiều', 'chieu', '2', 'ca2', 'ca 2']) else 'Sáng'

                if 'shift' in df.columns:
                    df['shift'] = df['shift'].apply(clean_shift)

                # Lấy đầy đủ chuỗi công việc từ Nhân viên
                employees = load_data(EMP_FILE)
                emp_task_map = {}
                for e in employees:
                    if isinstance(e, dict):
                        t = e.get('task') or e.get('role') or 'Làm việc'
                        emp_task_map[str(e.get('name', '')).strip().lower()] = t

                if 'task_name' not in df.columns:
                    df['task_name'] = df['emp_name'].apply(lambda x: emp_task_map.get(str(x).strip().lower(), 'Làm việc'))

                required_cols = ['emp_name', 'shift', 'date', 'task_name']
                if 'emp_name' in df.columns and 'date' in df.columns:
                    def parse_vietnam_date(val):
                        if pd.isna(val): return None
                        val_str = str(val).strip()
                        if ' ' in val_str: val_str = val_str.split(' ')[0]
                        parts = val_str.replace('/', '-').split('-')
                        if len(parts) == 3:
                            if len(parts[0]) == 4:
                                year, month, day = parts[0], parts[1], parts[2]
                                if int(month) <= 12 and int(day) <= 12:
                                    return f"{year}-{int(day):02d}-{int(month):02d}"
                                return f"{year}-{int(month):02d}-{int(day):02d}"
                            else:
                                day, month, year = parts[0], parts[1], parts[2]
                                return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                        return None

                    df['date'] = df['date'].apply(parse_vietnam_date)
                    df = df.dropna(subset=['date'])

                    new_schedule = df[required_cols].to_dict(orient='records')
                    save_data(SCH_FILE, new_schedule)

            except Exception as e:
                print(f"Lỗi quét Excel Lịch: {e}")

    return redirect(url_for('dashboard', week_offset=week_offset))


@app.route('/delete_schedule_item', methods=['POST'])
def delete_schedule_item():
    week_offset = request.form.get('week_offset', 0)
    emp_name = request.form.get('emp_name')
    date = request.form.get('date')
    task_name = request.form.get('task_name')

    schedule = load_data(SCH_FILE)
    new_schedule = [s for s in schedule if not (s.get('emp_name') == emp_name and s.get('date') == date and s.get('task_name') == task_name)]
    save_data(SCH_FILE, new_schedule)

    return redirect(url_for('dashboard', week_offset=week_offset))


# 3. QUẢN LÝ NHÂN VIÊN (GIỮ NGUYÊN TẤT CẢ CÔNG VIỆC TRONG EXCEL, KHÔNG BỎ NÓI CẢ)
@app.route('/employees')
def employees():
    return render_template('employees.html', employees=load_data(EMP_FILE))

@app.route('/upload_employees_excel', methods=['POST'])
def upload_employees_excel():
    if 'excel_file' in request.files:
        file = request.files['excel_file']
        if file and file.filename != '' and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            try:
                df = pd.read_excel(file, engine='openpyxl')
                df.columns = df.columns.astype(str).str.strip().str.upper()
                column_mapping = {
                    'TÊN': 'name', 'HO TÊN': 'name', 'HỌ TÊN': 'name', 'NHÂN VIÊN': 'name',
                    'CÔNG VIỆC': 'task', 'CHỨC VỤ': 'task', 'NHIỆM VỤ': 'task',
                    'MỨC LƯƠNG': 'salary', 'LƯƠNG': 'salary', 'PHỤ CẤP': 'bonus',
                    'HÌNH ẢNH': 'image', 'URL ẢNH': 'image'
                }
                df = df.rename(columns=column_mapping)

                new_employees = []
                for idx, row in df.iterrows():
                    name_val = str(row.get('name', 'N/A')).strip()
                    if name_val and name_val != 'nan':
                        # GIỮ NGUYÊN CHUỖI CÔNG VIỆC (VD: "1,2,3")
                        task_val = str(row.get('task', 'Làm việc')).strip()
                        if not task_val or task_val == 'nan':
                            task_val = 'Làm việc'

                        image_val = str(row.get('image', '')).strip()
                        if not image_val or image_val == 'nan':
                            image_val = f"https://i.pravatar.cc/100?img={(idx % 70) + 1}"

                        try: salary_val = int(row.get('salary', 17500000))
                        except Exception: salary_val = 17500000

                        try: bonus_val = int(row.get('bonus', 1500000))
                        except Exception: bonus_val = 1500000

                        new_employees.append({
                            'name': name_val,
                            'task': task_val,  # Lưu đầy đủ chuỗi công việc "1,2,3"
                            'role': task_val,
                            'image': image_val,
                            'salary': salary_val,
                            'bonus': bonus_val
                        })

                if new_employees:
                    save_data(EMP_FILE, new_employees)

            except Exception as e:
                print(f"Lỗi quét Excel Nhân viên: {e}")

    return redirect(url_for('employees'))

@app.route('/delete_employee/<int:index>')
def delete_employee(index):
    emps = load_data(EMP_FILE)
    if 0 <= index < len(emps):
        emps.pop(index)
        save_data(EMP_FILE, emps)
    return redirect(url_for('employees'))


# 4. ĐƠN XIN NGHỈ, BẢNG LƯƠNG, CÀI ĐẶT
@app.route('/leaves')
def leaves():
    leave_requests = load_data(LEAVE_FILE)
    employees = load_data(EMP_FILE)
    return render_template('leaves.html', leaves=leave_requests, employees=employees)

@app.route('/add_leave', methods=['POST'])
def add_leave():
    leaves_list = load_data(LEAVE_FILE)
    leaves_list.append({
        'emp_name': request.form.get('emp_name'),
        'reason': request.form.get('reason'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
        'status': 'Chờ duyệt'
    })
    save_data(LEAVE_FILE, leaves_list)
    return redirect(url_for('leaves'))

@app.route('/update_leave_status/<int:index>/<string:status>')
def update_leave_status(index, status):
    leaves_list = load_data(LEAVE_FILE)
    if 0 <= index < len(leaves_list):
        if status in ['approved', 'rejected']:
            leaves_list[index]['status'] = 'Đã duyệt' if status == 'approved' else 'Từ chối'
            save_data(LEAVE_FILE, leaves_list)
    return redirect(url_for('leaves'))

@app.route('/delete_leave/<int:index>')
def delete_leave(index):
    leaves_list = load_data(LEAVE_FILE)
    if 0 <= index < len(leaves_list):
        leaves_list.pop(index)
        save_data(LEAVE_FILE, leaves_list)
    return redirect(url_for('leaves'))

@app.route('/salary')
def salary():
    return render_template('salary.html', employees=load_data(EMP_FILE))

@app.route('/update_salary/<int:index>', methods=['POST'])
def update_salary(index):
    employees = load_data(EMP_FILE)
    if 0 <= index < len(employees):
        try:
            employees[index]['salary'] = int(request.form.get('salary', 17500000))
            employees[index]['bonus'] = int(request.form.get('bonus', 1500000))
            save_data(EMP_FILE, employees)
        except Exception: pass
    return redirect(url_for('salary'))

@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)