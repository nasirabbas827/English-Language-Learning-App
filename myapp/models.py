from django.db import models
from django.utils import timezone



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


# ----------------------------
# Quiz Questions & Options
# ----------------------------
class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('match', 'Matching'),
    ]
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    correct_answer = models.TextField()

    def __str__(self):
        return f"Q: {self.question_text[:50]}..."
    
    


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text




class StudentProgress(models.Model):
    student = models.ForeignKey(UserRegister, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)   # numeric score for the attempt
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'lesson', 'exercise')  # prevent exact duplicate records

    def mark_complete(self, score=None):
        self.completed = True
        if score is not None:
            self.score = score
        self.completed_at = timezone.now()
        self.save()

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
