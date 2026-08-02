from app import create_app, db
from app.models import Employee, Task, Assignment

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    print("[INFO] Dang khoi tao du lieu mau...")

    # 1. Danh sách nhân viên (25 nhân viên)
    employees_data = [
        ("Nguyễn Văn A", "Kỹ thuật"),
        ("Trần Thị B", "Kinh doanh"),
        ("Lê Văn C", "Kế toán"),
        ("Phạm Thị D", "Hành chính"),
        ("Hoàng Văn E", "IT Support"),
        ("Vũ Văn F", "Kỹ thuật"),
        ("Đặng Thị G", "Kinh doanh"),
        ("Bùi Văn H", "Kế toán"),
        ("Nô Văn I", "Hành chính"),
        ("Đỗ Thị K", "IT Support"),
        ("Hồ Văn L", "Kỹ thuật"),
        ("Nghô Thị M", "Kinh doanh"),
        ("Dương Văn N", "Kế toán"),
        ("Lý Thị O", "Hành chính"),
        ("Phan Văn P", "IT Support"),
        ("Trịnh Thị Q", "Kỹ thuật"),
        ("Đào Văn R", "Kinh doanh"),
        ("Cao Thị S", "Kế toán"),
        ("Võ Văn T", "Hành chính"),
        ("Tô Thị U", "IT Support"),
        ("Đinh Văn V", "Kỹ thuật"),
        ("Trương Thị X", "Kinh doanh"),
        ("Hà Văn Y", "Kế toán"),
        ("Lâm Thị Z", "Hành chính"),
        ("Nguyễn Văn An", "Kỹ thuật")
    ]

    emp_objects = []
    for name, dept in employees_data:
        avatar = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=0F52BA&color=fff&size=128"
        emp = Employee(name=name, department=dept, avatar_url=avatar)
        db.session.add(emp)
        emp_objects.append(emp)
    
    db.session.commit()

    # 2. Danh sách công việc (18 công việc)
    tasks_data = [
        ("Kiểm tra thiết bị", "Kỹ thuật"),
        ("Sửa chữa", "Kỹ thuật"),
        ("Bảo trì máy móc", "Kỹ thuật"),
        ("Nâng cấp hệ thống", "Kỹ thuật"),
        ("Báo cáo kỹ thuật", "Kỹ thuật"),
        ("Tư vấn KH", "Kinh doanh"),
        ("Báo giá", "Kinh doanh"),
        ("Chăm sóc KH", "Kinh doanh"),
        ("Báo cáo KD", "Kinh doanh"),
        ("Nhập liệu", "Kế toán"),
        ("Lập hóa đơn", "Kế toán"),
        ("Đối chiếu", "Kế toán"),
        ("Báo cáo", "Kế toán"),
        ("Văn thư", "Hành chính"),
        ("Tuyển dụng", "Hành chính"),
        ("Họp nội bộ", "Hành chính"),
        ("Báo cáo HC", "Hành chính"),
        ("Hỗ trợ IT", "IT Support"),
        ("Bảo trì server", "IT Support"),
        ("Quản trị mạng", "IT Support"),
        ("Backup dữ liệu", "IT Support"),
        ("Báo cáo IT", "IT Support")
    ]

    task_objects = {}
    for tname, tdept in tasks_data:
        t = Task(name=tname, department=tdept)
        db.session.add(t)
        task_objects[tname] = t

    db.session.commit()

    # 3. Lịch phân công tuần mẫu (Mon 19/05 -> Sat 24/05)
    dates = ["2025-05-19", "2025-05-20", "2025-05-21", "2025-05-22", "2025-05-23", "2025-05-24"]

    empA_schedule = [
        ("Kiểm tra thiết bị", "Bảo trì máy móc"),
        ("Sửa chữa", "Bảo trì máy móc"),
        ("Kiểm tra thiết bị", "Nâng cấp hệ thống"),
        ("Sửa chữa", "Bảo trì máy móc"),
        ("Kiểm tra thiết bị", "Báo cáo kỹ thuật"),
        (None, None)
    ]

    empB_schedule = [
        ("Tư vấn KH", "Chăm sóc KH"),
        ("Tư vấn KH", "Báo giá"),
        ("Tư vấn KH", "Chăm sóc KH"),
        ("Báo giá", "Chăm sóc KH"),
        ("Tư vấn KH", "Báo cáo KD"),
        (None, None)
    ]

    empC_schedule = [
        ("Nhập liệu", "Đối chiếu"),
        ("Lập hóa đơn", "Nhập liệu"),
        ("Nhập liệu", "Đối chiếu"),
        ("Lập hóa đơn", "Nhập liệu"),
        ("Báo cáo", "Đối chiếu"),
        (None, None)
    ]

    empD_schedule = [
        ("Văn thư", "Hành chính"),
        ("Tuyển dụng", "Văn thư"),
        ("Họp nội bộ", "Hành chính"),
        ("Tuyển dụng", "Văn thư"),
        ("Họp nội bộ", "Báo cáo HC"),
        (None, None)
    ]

    empE_schedule = [
        ("Hỗ trợ IT", "Quản trị mạng"),
        ("Bảo trì server", "Backup dữ liệu"),
        ("Hỗ trợ IT", "Quản trị mạng"),
        ("Bảo trì server", "Backup dữ liệu"),
        ("Hỗ trợ IT", "Báo cáo IT"),
        (None, None)
    ]

    schedules = [
        (emp_objects[0], empA_schedule),
        (emp_objects[1], empB_schedule),
        (emp_objects[2], empC_schedule),
        (emp_objects[3], empD_schedule),
        (emp_objects[4], empE_schedule),
    ]

    for emp, sched in schedules:
        for idx, (m_task_name, a_task_name) in enumerate(sched):
            wdate = dates[idx]
            if m_task_name and m_task_name in task_objects:
                a1 = Assignment(employee_id=emp.id, task_id=task_objects[m_task_name].id, work_date=wdate, shift='morning')
                db.session.add(a1)
            if a_task_name and a_task_name in task_objects:
                a2 = Assignment(employee_id=emp.id, task_id=task_objects[a_task_name].id, work_date=wdate, shift='afternoon')
                db.session.add(a2)

    db.session.commit()
    print("[SUCCESS] Da khoi tao 25 nhan vien, 22 cong viec va du lieu phan cong mau thanh cong!")
