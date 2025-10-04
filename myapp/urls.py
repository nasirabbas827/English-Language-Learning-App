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
# Quiz URLs
path('quiz/questions/', views.quiz_list, name='quiz_list'),
path('quiz/questions/add/', views.quiz_create, name='quiz_create'),
path('quiz/questions/<int:pk>/edit/', views.quiz_update, name='quiz_update'),
path('quiz/questions/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
path('leaderboard/', views.leaderboard, name='leaderboard'),

path('sessions/', views.session_list, name='session_list'),
path('sessions/create/', views.session_create, name='session_create'),
path('sessions/<int:pk>/edit/', views.session_update, name='session_update'),
path('sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),
path('student/sessions/', views.student_sessions, name='student_sessions'),

path('threads/', views.thread_list, name='thread_list'),
path('threads/create/', views.thread_create, name='thread_create'),
path('threads/<int:pk>/delete/', views.thread_delete, name='thread_delete'),
path('threads/<int:pk>/', views.thread_detail, name='thread_detail'),
path('threads/<int:thread_id>/post/create/', views.post_create, name='post_create'),
path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
path('chat/', views.peer_chat, name='peer_chat'),
path('chat/<int:user_id>/', views.peer_chat, name='peer_chat'),


]
