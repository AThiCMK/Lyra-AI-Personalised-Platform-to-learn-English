from django.urls import path
from . import views

urlpatterns = [
    path('faculty/home/', views.faculty_home, name='faculty_home'),
    path('faculty/enrolled_students/', views.enrolled_students, name='enrolled_students'),
    path('faculty/upload_content/', views.upload_content, name='upload_content'),
    path('faculty/register/', views.faculty_register, name='faculty_register'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/reading_test/<str:category>/<int:level>/', views.reading_test_view, name='reading_test_view'),
    path('student/dashboard/beginner/', views.beginner_dashboard, name='beginner_dashboard'),
    path('student/dashboard/intermediate/', views.intermediate_dashboard, name='intermediate_dashboard'),
    path('student/dashboard/advanced/', views.advanced_dashboard, name='advanced_dashboard'),
    path('student/level_selection/', views.student_level_selection, name='student_level_selection'),
    path('student/register/', views.student_register, name='student_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]