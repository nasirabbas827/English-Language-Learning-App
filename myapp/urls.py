from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Dashboards
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/writing-submissions/', views.teacher_writing_submissions, name='teacher_writing_submissions'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),

    # Exercise attempt (quiz runner)
    path("exercise/<int:exercise_id>/attempt/", views.exercise_attempt, name="exercise_attempt"),

    # Profile
    path('update-profile/', views.update_profile, name='update_profile'),

    # Lessons CRUD
    path('lessons/', views.lesson_list, name='lesson_list'),
    path('lessons/add/', views.lesson_create, name='lesson_create'),
    path('lessons/<int:pk>/edit/', views.lesson_update, name='lesson_update'),
    path('lessons/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),

    # LessonMedia
    path('lesson-media/', views.lesson_media_list, name='lesson_media_list'),
    path('lesson-media/add/', views.lesson_media_create, name='lesson_media_create'),
    path('lesson-media/edit/<int:pk>/', views.lesson_media_update, name='lesson_media_update'),
    path('lesson-media/delete/<int:pk>/', views.lesson_media_delete, name='lesson_media_delete'),

    # Exercises
    path('exercises/', views.exercise_list, name='exercise_list'),
    path('exercises/add/', views.exercise_create, name='exercise_create'),
    path('exercises/<int:pk>/edit/', views.exercise_update, name='exercise_update'),
    path('exercises/<int:pk>/delete/', views.exercise_delete, name='exercise_delete'),

    # Quiz Questions
    path('quiz/questions/', views.quizquestion_list, name='quizquestion_list'),
    path('quiz/questions/add/', views.quizquestion_create, name='quizquestion_create'),
    path('quiz/questions/<int:pk>/edit/', views.quizquestion_update, name='quizquestion_update'),
    path('quiz/questions/<int:pk>/delete/', views.quizquestion_delete, name='quizquestion_delete'),

    # Quiz Options
    path('quiz/options/', views.quizoption_list, name='quizoption_list'),
    path('quiz/options/add/', views.quizoption_create, name='quizoption_create'),
    path('quiz/options/<int:pk>/edit/', views.quizoption_update, name='quizoption_update'),
    path('quiz/options/<int:pk>/delete/', views.quizoption_delete, name='quizoption_delete'),
]
