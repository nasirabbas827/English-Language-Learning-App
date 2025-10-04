from django.contrib import admin
from .models import (
    UserRegister, Lesson, LessonMedia, Exercise, Quiz,
    Badge, StudentBadge, StudentProgress, WritingSubmission,
    LiveSession, DiscussionThread, DiscussionPost, PeerChat
)

@admin.register(UserRegister)
class UserRegisterAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('full_name', 'email')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill_level', 'category', 'created_by', 'created_at')
    list_filter = ('skill_level', 'category')
    search_fields = ('title', 'description')


@admin.register(LessonMedia)
class LessonMediaAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'media_type', 'media_url')
    list_filter = ('media_type',)
    search_fields = ('lesson__title',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'type', 'instructions')
    list_filter = ('type',)
    search_fields = ('lesson__title',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'question_type', 'exercise', 'created_at')
    list_filter = ('question_type',)
    search_fields = ('question_text',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_required', 'milestone_name')
    search_fields = ('name', 'milestone_name')


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_at')
    list_filter = ('badge',)
    search_fields = ('student__full_name', 'badge__name')


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'exercise', 'score', 'completed', 'completed_at')
    list_filter = ('completed',)
    search_fields = ('student__full_name', 'lesson__title')


@admin.register(WritingSubmission)
class WritingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'submitted_at')
    search_fields = ('user__full_name',)


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'tutor', 'start_time', 'end_time', 'status')
    list_filter = ('status',)
    search_fields = ('title', 'tutor__full_name')


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title', 'created_by__full_name')


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'created_at')
    search_fields = ('thread__title', 'author__full_name', 'content')


@admin.register(PeerChat)
class PeerChatAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message', 'sent_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__full_name', 'receiver__full_name', 'message')
