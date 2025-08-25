from django.contrib import admin
from .models import (
    UserRegister, Lesson, LessonMedia, Exercise, 
    QuizQuestion, QuizOption, StudentProgress, WritingSubmission
)


# ----------------------------
# User Admin
# ----------------------------
@admin.register(UserRegister)
class UserRegisterAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status', 'gender', 'country')
    search_fields = ('full_name', 'email', 'phone', 'city')
    ordering = ('-created_at',)


# ----------------------------
# Lesson Media Inline
# ----------------------------
class LessonMediaInline(admin.TabularInline):
    model = LessonMedia
    extra = 1


# ----------------------------
# Exercise Inline
# ----------------------------
class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


# ----------------------------
# Lesson Admin
# ----------------------------
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill_level', 'category', 'created_by', 'created_at')
    list_filter = ('skill_level', 'category', 'created_by')
    search_fields = ('title', 'description')
    inlines = [LessonMediaInline, ExerciseInline]


# ----------------------------
# Quiz Option Inline
# ----------------------------
class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 2


# ----------------------------
# Quiz Question Admin
# ----------------------------
@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'exercise', 'question_type')
    list_filter = ('question_type',)
    search_fields = ('question_text',)
    inlines = [QuizOptionInline]


# ----------------------------
# Exercise Admin
# ----------------------------
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'type', 'instructions')
    list_filter = ('type',)
    search_fields = ('instructions',)


# ----------------------------
# Student Progress Admin
# ----------------------------
@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'exercise', 'score', 'completed', 'completed_at')
    list_filter = ('completed', 'lesson', 'exercise')
    search_fields = ('student__full_name', 'lesson__title')


# ----------------------------
# Writing Submission Admin
# ----------------------------
@admin.register(WritingSubmission)
class WritingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'submitted_at')
    list_filter = ('exercise',)
    search_fields = ('user__full_name', 'essay_text')
