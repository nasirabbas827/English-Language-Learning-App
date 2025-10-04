from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# ----------------------------
# User Registration (Custom Table)
# ----------------------------
class UserRegister(models.Model):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # store hashed password
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.role})"


# ----------------------------
# Lessons
# ----------------------------
class Lesson(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    CATEGORIES = [
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
        ('listening', 'Listening'),
        ('speaking', 'Speaking'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField()
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    created_by = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.skill_level})"


# ----------------------------
# Lesson Multimedia
# ----------------------------
class LessonMedia(models.Model):
    MEDIA_TYPES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('flashcard', 'Flashcard'),
        ('document', 'Document'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    media_url = models.URLField()

    def __str__(self):
        return f"{self.lesson.title} - {self.media_type}"


# ----------------------------
# Exercises
# ----------------------------
class Exercise(models.Model):
    TYPES = [
        ('quiz', 'Quiz'),
        ('speaking', 'Speaking'),
        ('writing', 'Writing'),
        ('listening', 'Listening'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercises")
    type = models.CharField(max_length=20, choices=TYPES)
    instructions = models.TextField()

    def __str__(self):
        return f"{self.lesson.title} - {self.type}"


class Quiz(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('match', 'Matching'),
    ]

    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    
    correct_answer = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q: {self.question_text[:50]}..."


# ----------------------------
# Badges
# ----------------------------
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/', null=True, blank=True)
    points_required = models.PositiveIntegerField(default=0)
    milestone_name = models.CharField(max_length=150, null=True, blank=True, 
                                      help_text="Optional milestone achievement name")

    def __str__(self):
        return self.name


class StudentBadge(models.Model):
    student = models.ForeignKey(UserRegister, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')

    def __str__(self):
        return f"{self.student.full_name} - {self.badge.name}"


# ----------------------------
# Student Progress
# ----------------------------
from django.utils import timezone
from django.db.models import Count

class StudentProgress(models.Model):
    student = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'lesson', 'exercise')

    def mark_complete(self, score=None):
        self.completed = True
        if score is not None:
            self.score = score
        self.completed_at = timezone.now()
        self.save()
        self.assign_badges()  # Updated logic

    def assign_badges(self):
        """
        Assign badges dynamically based on lesson completion points.
        Total points = 100.
        Each lesson gets equal share.
        """
        student = self.student
        total_lessons = Lesson.objects.count()
        if total_lessons == 0:
            return

        points_per_lesson = 100 / total_lessons

        # Count fully completed lessons
        completed_lessons = 0
        for lesson in Lesson.objects.all():
            total_exercises = lesson.exercises.count()
            if total_exercises == 0:
                continue
            completed_exercises = StudentProgress.objects.filter(
                student=student,
                lesson=lesson,
                completed=True
            ).count()
            if completed_exercises == total_exercises:
                completed_lessons += 1

        # Total earned points
        earned_points = completed_lessons * points_per_lesson

        # Award badges where points_required <= earned points
        eligible_badges = Badge.objects.filter(points_required__lte=earned_points)
        for badge in eligible_badges:
            StudentBadge.objects.get_or_create(student=student, badge=badge)

    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.title} ({'done' if self.completed else 'pending'})"


# ----------------------------
# Writing Submissions
# ----------------------------
class WritingSubmission(models.Model):
    user = models.ForeignKey(UserRegister, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    essay_text = models.TextField()
    grammar_feedback = models.TextField(null=True, blank=True)
    spelling_feedback = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - Writing Submission"


# Live Sessions
class LiveSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    title = models.CharField(max_length=150)
    tutor = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='tutor_sessions'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    session_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        return f"{self.title} - {self.start_time}"

from django.db import models
from django.utils import timezone
from .models import UserRegister  # Use your existing student/teacher model


# ------------------------------------
# 1) Discussion Thread / Topic Model
# ------------------------------------
class DiscussionThread(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ------------------------------------
# 2) Posts/Replies under a Thread
# ------------------------------------
class DiscussionPost(models.Model):
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='discussion_posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.full_name} - {self.thread.title}"


# Peer Chat
class PeerChat(models.Model):
    sender = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='sent_chats')
    receiver = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='received_chats')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.full_name} to {self.receiver.full_name}"