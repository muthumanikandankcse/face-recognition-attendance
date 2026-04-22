import base64
import json
import numpy as np
import cv2

from datetime import date

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Student, Attendance
from .forms import StudentForm
from .utils import recognize_face

from django.contrib.auth.decorators import login_required


# -------------------------------
# LOGIN
# -------------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------------------
# DASHBOARD
# -------------------------------
def dashboard(request):
    total_students = Student.objects.count()
    today = date.today()

    present_students = Attendance.objects.filter(date=today).count()
    absent_students = total_students - present_students

    context = {
        'total': total_students,
        'present': present_students,
        'absent': absent_students,
    }

    return render(request, 'dashboard.html', context)


# -------------------------------
# REGISTER STUDENT
# -------------------------------
def register_student(request):
    form = StudentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'register.html', {'form': form})


# -------------------------------
# ATTENDANCE PAGE
# -------------------------------
def attendance_page(request):
    return render(request, 'attendance.html')


# -------------------------------
# REAL-TIME ATTENDANCE API
# -------------------------------
@csrf_exempt
def mark_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            image_data = data.get('image')

            if not image_data:
                return JsonResponse({'message': 'No image received'})

            # Remove base64 header if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            img_bytes = base64.b64decode(image_data)

            # Convert to OpenCV format
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            if frame is None:
                return JsonResponse({'message': 'Invalid image format'})
            

            # 🔥 ADD THIS BLOCK HERE
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # -------------------------------
            # 🔥 FIX IMAGE FORMAT (IMPORTANT)
            # -------------------------------
            if len(frame.shape) == 2:
                # grayscale → RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            elif len(frame.shape) == 3:
                if frame.shape[2] == 4:
                    # RGBA → RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                elif frame.shape[2] == 3:
                    # BGR → RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # -------------------------------
            # FACE RECOGNITION
            # -------------------------------
            from .utils import get_known_faces

            known_faces = get_known_faces()

            if not known_faces:
                return JsonResponse({'message': 'No registered faces'})

            recognized_students = recognize_face(frame, known_faces, tol=0.6)

            if not recognized_students:
                return JsonResponse({'message': 'Face not recognized'})

            messages = []

            for student in recognized_students:
                already_marked = Attendance.objects.filter(
                    student=student,
                    date=date.today()
                ).exists()

                if not already_marked:
                    Attendance.objects.create(student=student)
                    messages.append(f"{student.name} marked present")
                else:
                    messages.append(f"{student.name} already marked")

            return JsonResponse({
                'message': ', '.join(messages)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'message': str(e)})

    return JsonResponse({'message': 'Invalid request'})


    from django.contrib.auth.decorators import login_required
from django.db.models import Count


# -------------------------------
# STUDENT LIST
# -------------------------------
@login_required
def student_list(request):
    students = Student.objects.all()
    return render(request, 'students.html', {'students': students})


# -------------------------------
# DELETE STUDENT
# -------------------------------
@login_required
def delete_student(request, id):
    student = Student.objects.get(id=id)
    student.delete()
    return redirect('students')


# -------------------------------
# UPDATE STUDENT
# -------------------------------
@login_required
def update_student(request, id):
    student = Student.objects.get(id=id)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)

    if form.is_valid():
        form.save()
        return redirect('students')

    return render(request, 'register.html', {'form': form})


# -------------------------------
# DASHBOARD (UPDATED)
# -------------------------------
@login_required
def dashboard(request):
    total_students = Student.objects.count()
    today = date.today()

    present_students = Attendance.objects.filter(date=today).count()
    absent_students = total_students - present_students

    # Pie chart data
    attendance_percent = int((present_students / total_students) * 100) if total_students else 0

    context = {
        'total': total_students,
        'present': present_students,
        'absent': absent_students,
        'attendance_percent': attendance_percent,
        'today': today,
        'user': request.user
    }

    return render(request, 'dashboard.html', context)


import csv
from django.http import HttpResponse
from django.utils import timezone


# -------------------------------
# ATTENDANCE HISTORY
# -------------------------------
@login_required
def attendance_history(request):
    records = Attendance.objects.select_related('student').all().order_by('-date')

    return render(request, 'attendance_history.html', {
        'records': records
    })




# -------------------------------
# EXPORT CSV
# -------------------------------
@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Roll', 'Department', 'Date', 'Time'])

    records = Attendance.objects.select_related('student').all()

    for r in records:
        writer.writerow([
            r.student.name,
            r.student.roll_number,
            r.student.department,
            r.date,
            r.time
        ])

    

    # 🔍 APPLY SAME FILTERS
    query = request.GET.get('q')
    if query:
        records = records.filter(
            Q(student__name__icontains=query) |
            Q(student__roll_number__icontains=query)
        )

    date_filter = request.GET.get('date')
    if date_filter:
        records = records.filter(date=date_filter)

    for r in records:
        writer.writerow([
            r.student.name,
            r.student.roll_number,
            r.student.department,
            r.date,
            r.time
        ])

    return response

   




# -------------------------------
# LIVE DASHBOARD DATA (AJAX)
# -------------------------------
@login_required
def dashboard_data(request):
    today = date.today()
    total = Student.objects.count()
    present = Attendance.objects.filter(date=today).count()
    absent = total - present

    return JsonResponse({
        'total': total,
        'present': present,
        'absent': absent
    })



from django.contrib.auth.models import User
from django.contrib import messages

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully")
            return redirect('login')

    return render(request, 'register_user.html')


from django.contrib.auth.models import User
from django.contrib import messages

# -------------------------------
# REGISTER USER
# -------------------------------
def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully")
            return redirect('login')

    return render(request, 'register_user.html')


# -------------------------------
# FORGOT PASSWORD
# -------------------------------
from django.contrib.auth.models import User
from django.contrib import messages

def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        new_password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()

            messages.success(request, "Password reset successful! Please login.")
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "User not found")

    return render(request, 'forgot_password.html')

from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime

def attendance_history(request):
    records = Attendance.objects.select_related('student').all().order_by('-date')

    # 🔍 SEARCH
    query = request.GET.get('q')
    if query:
        records = records.filter(
            Q(student__name__icontains=query) |
            Q(student__roll_number__icontains=query)
        )

    # 📅 DATE FILTER
    date_filter = request.GET.get('date')
    if date_filter:
        records = records.filter(date=date_filter)

    # 📄 PAGINATION
    paginator = Paginator(records, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'attendance_history.html', {
        'page_obj': page_obj,
        'query': query,
        'date_filter': date_filter
    })