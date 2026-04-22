from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_student, name='register'),
    path('attendance/', views.attendance_page, name='attendance'),
    path('mark/', views.mark_attendance, name='mark'),
    path('logout/', views.logout_view, name='logout'),
    path('students/', views.student_list, name='students'),
    path('delete/<int:id>/', views.delete_student, name='delete_student '),
    path('update/<int:id>/', views.update_student, name='update_student'),
    path('history/', views.attendance_history, name='history'),
    path('export/', views.export_csv, name='export'),
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('attendance/', views.attendance_page, name='attendance'),
]