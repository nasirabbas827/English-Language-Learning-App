from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import UserRegisterForm , LoginForm , UpdateProfileForm , QuizForm
from .models import UserRegister , Quiz 
from django.utils import timezone
from django.db.models import Sum, F, Prefetch



def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash password before saving
            user.password = make_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})



def login(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']

            try:
                user = UserRegister.objects.get(email=email, role=role)
            except UserRegister.DoesNotExist:
                messages.error(request, "Invalid email, password, or role")
                return redirect('login')

            if check_password(password, user.password):
                if user.status == "active":
                    # Store user session
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.full_name
                    request.session['user_role'] = user.role

                    # Redirect strictly to user’s dashboard
                    if user.role == "teacher":
                        return redirect("teacher_dashboard")
                    elif user.role == "student":
                        return redirect("student_dashboard")
                else:
                    messages.error(request, "Your account is inactive. Contact admin.")
            else:
                messages.error(request, "Invalid email, password, or role")

    return render(request, 'login.html', {'form': form})


def logout(request):
    request.session.flush()
    return redirect('index')


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegister, Lesson, Exercise, StudentProgress, WritingSubmission, LiveSession

def teacher_dashboard(request):
    # Security check
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    teacher_id = request.session.get('user_id')
    teacher_name = request.session.get('user_name')

    # Summary counts
    total_lessons = Lesson.objects.filter(created_by_id=teacher_id).count()
    total_exercises = Exercise.objects.filter(lesson__created_by_id=teacher_id).count()
    total_students = UserRegister.objects.filter(role='student').count()
    active_sessions = LiveSession.objects.filter(tutor_id=teacher_id, status='ongoing').count()

    # All students with progress
    students = UserRegister.objects.filter(role='student')
    student_data = []
    for student in students:
        progress = StudentProgress.objects.filter(student=student, lesson__created_by_id=teacher_id)
        # Calculate average score
        total_score = 0
        count = 0
        for prog in progress:
            if prog.score is not None:
                total_score += prog.score
                count += 1
        avg_score = total_score / count if count > 0 else 0
        student_data.append({
            'student': student,
            'progress': progress,
            'avg_score': round(avg_score, 2),  # Round to 2 decimal places
        })

    # Recent submissions (last 5)
    recent_submissions = WritingSubmission.objects.filter(exercise__lesson__created_by_id=teacher_id).order_by('-submitted_at')[:5]

    # All lessons for filter dropdown
    lessons = Lesson.objects.filter(created_by_id=teacher_id)

    context = {
        'full_name': teacher_name,
        'total_lessons': total_lessons,
        'total_exercises': total_exercises,
        'total_students': total_students,
        'active_sessions': active_sessions,
        'student_data': student_data,
        'recent_submissions': recent_submissions,
        'lessons': lessons,
    }
    return render(request, "teacher_dashboard.html", context)

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import WritingSubmission, UserRegister, Lesson
from django.db.models import Q
import csv
from django.http import HttpResponse

def teacher_writing_submissions(request):
    # Security check
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    teacher_id = request.session.get('user_id')
    submissions = WritingSubmission.objects.select_related('user', 'exercise', 'exercise__lesson').filter(
        exercise__lesson__created_by_id=teacher_id
    )

    # Handle filtering
    search_query = request.GET.get('search', '')
    lesson_filter = request.GET.get('lesson', '')
    if search_query:
        submissions = submissions.filter(
            Q(user__full_name__icontains=search_query) |
            Q(essay_text__icontains=search_query)
        )
    if lesson_filter:
        submissions = submissions.filter(exercise__lesson__title__icontains=lesson_filter)

    # Handle feedback submission
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grammar_feedback = request.POST.get('grammar_feedback')
        spelling_feedback = request.POST.get('spelling_feedback')
        try:
            submission = WritingSubmission.objects.get(id=submission_id, exercise__lesson__created_by_id=teacher_id)
            submission.grammar_feedback = grammar_feedback
            submission.spelling_feedback = spelling_feedback
            submission.save()
            messages.success(request, "Feedback submitted successfully!")
            return redirect('teacher_writing_submissions')
        except WritingSubmission.DoesNotExist:
            messages.error(request, "Invalid submission")

    # Handle CSV download
    if 'download_csv' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="writing_submissions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student', 'Lesson', 'Exercise', 'Essay Text', 'Spelling Feedback', 'Grammar Feedback', 'Submitted At'])
        for sub in submissions:
            writer.writerow([
                sub.user.full_name,
                sub.exercise.lesson.title,
                sub.exercise.type,
                sub.essay_text,
                sub.spelling_feedback or '',
                sub.grammar_feedback or '',
                sub.submitted_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response

    # Get lessons for filter dropdown
    lessons = Lesson.objects.filter(created_by_id=teacher_id)

    return render(request, "teacher_writing_submissions.html", {
        'submissions': submissions,
        'lessons': lessons,
        'search_query': search_query,
        'lesson_filter': lesson_filter,
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegister, Lesson, Exercise, StudentProgress, WritingSubmission, StudentBadge
import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import UserRegister, Lesson, Exercise, StudentProgress, WritingSubmission, StudentBadge
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, FrameBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, Line
import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import UserRegister, Lesson, Exercise, StudentProgress, WritingSubmission, StudentBadge
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, Line, Rect
import datetime
import uuid

def student_dashboard(request):
    # Security: only students
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    student_id = request.session.get('user_id')
    student_name = request.session.get('user_name', 'Student')

    # Filters
    category = request.GET.get('category')
    skill_level = request.GET.get('skill_level')
    q = request.GET.get('q', '')

    lessons_qs = Lesson.objects.all().order_by('-created_at')
    if category:
        lessons_qs = lessons_qs.filter(category=category)
    if skill_level:
        lessons_qs = lessons_qs.filter(skill_level=skill_level)
    if q:
        lessons_qs = lessons_qs.filter(title__icontains=q)

    # Build list of (lesson, percent)
    lessons_with_progress = []
    total_lessons = lessons_qs.count()
    completed_lessons = 0
    total_exercises = 0
    completed_exercises = 0

    for lesson in lessons_qs:
        total_ex = lesson.exercises.count()
        total_exercises += total_ex
        if total_ex == 0:
            percent = None
        else:
            completed_count = StudentProgress.objects.filter(
                student_id=student_id,
                lesson=lesson,
                completed=True
            ).values('exercise').distinct().count()
            if completed_count == total_ex and total_ex > 0:
                completed_lessons += 1
            completed_exercises += completed_count
            percent = int((completed_count / total_ex) * 100) if total_ex > 0 else None
        lessons_with_progress.append({
            'lesson': lesson,
            'percent': percent
        })

    # Calculate progress percentages
    lesson_progress_percent = round((completed_lessons / total_lessons * 100), 2) if total_lessons > 0 else 0
    exercise_progress_percent = round((completed_exercises / total_exercises * 100), 2) if total_exercises > 0 else 0

    # Check if all lessons are completed
    all_lessons_completed = total_lessons > 0 and completed_lessons == total_lessons

    # Recent lists
    recent_lessons = Lesson.objects.all().order_by('-created_at')[:5]
    recent_exercises = Exercise.objects.all().order_by('-id')[:5]
    recent_submissions = WritingSubmission.objects.filter(user_id=student_id).order_by('-submitted_at')[:5]

    # Fetch earned badges
    earned_badges = StudentBadge.objects.filter(student_id=student_id).select_related('badge')
    badge_count = earned_badges.count()
    badge_names = ", ".join([sb.badge.name for sb in earned_badges]) or "None"

    # Handle certificate download
    if 'download_certificate' in request.GET and all_lessons_completed:
        student = UserRegister.objects.get(id=student_id)
        completion_date = datetime.date.today().strftime('%B %d, %Y')
        certificate_id = str(uuid.uuid4())[:8]  # Unique certificate ID

        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{student_name}.pdf"'

        # Define styles
        styles = {
            'title': ParagraphStyle(
                name='Title',
                fontName='Times-Bold',
                fontSize=40,
                textColor=colors.HexColor('#00d4b4'),
                alignment=1,  # Center
                spaceAfter=20,
            ),
            'subheader': ParagraphStyle(
                name='Subheader',
                fontName='Times-Roman',
                fontSize=28,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=1,
                spaceAfter=20,
            ),
            'content': ParagraphStyle(
                name='Content',
                fontName='Times-Roman',
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=1,
                leading=24,
                spaceAfter=10,
            ),
            'bold_content': ParagraphStyle(
                name='BoldContent',
                fontName='Times-Bold',
                fontSize=20,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=1,
                spaceAfter=10,
            ),
            'footer': ParagraphStyle(
                name='Footer',
                fontName='Times-Italic',
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                alignment=1,
                spaceBefore=20,
            ),
        }

        # Create PDF document
        doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []

        # Header with gradient effect (simulated with a colored rectangle)
        header_drawing = Drawing(A4[0], 100)
        header_drawing.add(Rect(0, 0, A4[0], 100, fillColor=colors.HexColor('#00d4b4'), strokeColor=None))
        elements.append(header_drawing)
        elements.append(Spacer(1, 0.5*cm))

        # Certificate content
        elements.append(Paragraph("Certificate of Completion", styles['title']))
        elements.append(Paragraph("English Language Learning App", styles['subheader']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Certificate ID: {certificate_id}", styles['content']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("This is to certify that", styles['content']))
        elements.append(Paragraph(f"{student_name}", styles['bold_content']))
        elements.append(Paragraph("has successfully completed all lessons in the", styles['content']))
        elements.append(Paragraph("English Language Learning Course", styles['bold_content']))
        elements.append(Paragraph(f"on {completion_date}.", styles['content']))
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Course Summary:", styles['bold_content']))
        elements.append(Paragraph(f"- Total Lessons Completed: {completed_lessons} / {total_lessons}", styles['content']))
        elements.append(Paragraph(f"- Total Exercises Completed: {completed_exercises} / {total_exercises}", styles['content']))
        elements.append(Paragraph(f"- Badges Earned: {badge_count} ({badge_names})", styles['content']))
        elements.append(Paragraph("Congratulations on your dedication to mastering English!", styles['content']))
        elements.append(Spacer(1, 2*cm))

        # Footer with branding
        elements.append(Paragraph("English Language Learning App - Empowering Language Mastery", styles['footer']))

        # Add border and watermark
        def draw_border_and_watermark(canvas, doc):
            # Double-line border
            canvas.setStrokeColor(colors.HexColor('#00d4b4'))
            canvas.setLineWidth(4)
            canvas.rect(1*cm, 1*cm, A4[0]-2*cm, A4[1]-2*cm)
            canvas.setLineWidth(2)
            canvas.rect(1.5*cm, 1.5*cm, A4[0]-3*cm, A4[1]-3*cm)
            # Watermark
            canvas.setFont('Times-Italic', 50)
            canvas.setFillColor(colors.HexColor('#00d4b4'), alpha=0.1)
            canvas.rotate(45)
            canvas.drawString(8*cm, -2*cm, "ELLA Certified")
            canvas.rotate(-45)

        # Build PDF
        doc.build(elements, onFirstPage=draw_border_and_watermark, onLaterPages=draw_border_and_watermark)
        return response

    context = {
        'full_name': student_name,
        'lessons_with_progress': lessons_with_progress,
        'recent_lessons': recent_lessons,
        'recent_exercises': recent_exercises,
        'recent_submissions': recent_submissions,
        'earned_badges': earned_badges,
        'category_selected': category or '',
        'skill_selected': skill_level or '',
        'q': q,
        'CATEGORY_CHOICES': Lesson.CATEGORIES,
        'SKILL_CHOICES': Lesson.SKILL_LEVELS,
        'all_lessons_completed': all_lessons_completed,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'total_exercises': total_exercises,
        'completed_exercises': completed_exercises,
        'lesson_progress_percent': lesson_progress_percent,
        'exercise_progress_percent': exercise_progress_percent,
    }
    return render(request, 'student_dashboard.html', context)


def leaderboard(request):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    # Prefetch badges with their points
    leaderboard_data = (
        UserRegister.objects.filter(role='student')
        .annotate(
            total_score=Sum('progress__score'),
            completed_exercises=Sum(F('progress__completed'))
        )
        .prefetch_related(
            Prefetch(
                'studentbadge_set',
                queryset=StudentBadge.objects.select_related('badge')
            )
        )
        .order_by('-total_score', '-completed_exercises')
    )

    current_student_id = request.session.get('user_id')

    context = {
        'leaderboard': leaderboard_data,
        'current_student_id': current_student_id,
    }
    return render(request, 'student/leaderboard.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lesson, LessonMedia, Exercise, StudentProgress

def lesson_detail(request, pk):
    # Security: only students
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    lesson = get_object_or_404(Lesson, pk=pk)
    student_id = request.session.get('user_id')

    # Load related media and exercises
    medias = LessonMedia.objects.filter(lesson=lesson)
    exercises = Exercise.objects.filter(lesson=lesson)

    # Calculate progress
    total_exercises = exercises.count()
    completed_exercises = StudentProgress.objects.filter(
        student_id=student_id,
        lesson=lesson,
        completed=True
    ).values('exercise').distinct().count()
    progress_percent = round((completed_exercises / total_exercises * 100), 2) if total_exercises > 0 else None

    context = {
        'lesson': lesson,
        'medias': medias,
        'exercises': exercises,
        'full_name': request.session.get('user_name'),
        'progress_percent': progress_percent,
        'completed_exercises': completed_exercises,
        'total_exercises': total_exercises,
    }
    return render(request, 'student/lesson_detail.html', context)

    
import pyttsx3
import speech_recognition as sr
from difflib import SequenceMatcher
from spellchecker import SpellChecker
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import (
    Exercise, StudentProgress, UserRegister,
    WritingSubmission, Quiz, Badge, StudentBadge, Lesson
)
import string

# ----------------------------
# Badge Assignment Function
# ----------------------------
from django.db.models import Sum

def assign_badges(student):
    """
    Assign badges dynamically based on lesson-based points.
    Total lessons = 100 points max.
    Each completed lesson = (100 / total lessons).
    """
    total_lessons = Lesson.objects.count()
    if total_lessons == 0:
        return

    # Points per completed lesson
    points_per_lesson = 100 / total_lessons

    # Completed lessons by student
    completed_lessons = 0
    lessons = Lesson.objects.all()
    for lesson in lessons:
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

    # Get all badges student is eligible for
    badges = Badge.objects.filter(points_required__lte=earned_points)
    for badge in badges:
        StudentBadge.objects.get_or_create(student=student, badge=badge)

# ----------------------------
# Exercise Attempt View
# ----------------------------
def exercise_attempt(request, exercise_id):
    if request.session.get("user_role") != "student":
        messages.error(request, "Unauthorized access")
        return redirect("login")

    student = get_object_or_404(UserRegister, id=request.session.get("user_id"))
    exercise = get_object_or_404(Exercise, id=exercise_id)

    # ----------------------------
    # Speaking / Listening Exercises
    # ----------------------------
    if exercise.type in ["speaking", "listening"]:
        engine = pyttsx3.init()
        engine.say(exercise.instructions)
        engine.runAndWait()

        spoken_text = ""
        feedback = ""

        if exercise.type == "speaking":
            recognizer = sr.Recognizer()
            mic = sr.Microphone()
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
                try:
                    spoken_text = recognizer.recognize_google(audio)
                except (sr.UnknownValueError, sr.RequestError):
                    spoken_text = ""

        if request.method == "POST":
            if exercise.type == "speaking":
                instructions_text = exercise.instructions.strip().lower()
                spoken_text_clean = request.POST.get("spoken_text", "").strip().lower()
                similarity = SequenceMatcher(None, instructions_text, spoken_text_clean).ratio()
                percentage_score = round(similarity * 100, 1)
                feedback = f"Expected: {exercise.instructions}\nYou said: {spoken_text_clean}"
            else:
                percentage_score = 100
                feedback = "Listening exercise auto-completed."

            progress, _ = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=percentage_score)
            assign_badges(student)  # <-- Automatic badge assignment

            messages.success(request, f"You scored {percentage_score}% for this {exercise.type} exercise.")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": percentage_score,
                "feedback": feedback,
                "spoken_text": spoken_text
            })

        template = "student/exercise_speaking.html" if exercise.type == "speaking" else "student/exercise_listening.html"
        return render(request, template, {"exercise": exercise, "spoken_text": spoken_text})

    # ----------------------------
    # Writing Exercise
    # ----------------------------
    elif exercise.type == "writing":
        if request.method == "POST":
            essay_text = request.POST.get("essay_text", "").strip()
            spell = SpellChecker()
            words = essay_text.split()
            clean_words = [w.strip(string.punctuation).lower() for w in words]
            misspelled = spell.unknown(clean_words)
            spelling_feedback = ", ".join(misspelled) if misspelled else "No spelling mistakes found."

            grammar_feedback = ""
            prev_word = ""
            for w in clean_words:
                if w == prev_word:
                    grammar_feedback += f"Repeated word: {w}\n"
                prev_word = w

            WritingSubmission.objects.create(
                user=student,
                exercise=exercise,
                essay_text=essay_text,
                grammar_feedback=grammar_feedback,
                spelling_feedback=spelling_feedback
            )

            progress, _ = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=100)
            assign_badges(student)  # <-- Automatic badge assignment

            messages.success(request, "Essay submitted successfully with feedback!")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": 100,
                "feedback": f"Grammar Issues:\n{grammar_feedback}\nSpelling Issues:\n{spelling_feedback}",
                "essay_text": essay_text
            })

        return render(request, "student/exercise_writing.html", {"exercise": exercise})

    # ----------------------------
    # Quiz Exercise
    # ----------------------------
    else:
        questions = Quiz.objects.filter(exercise=exercise)
        feedback_list = []

        if request.method == "POST":
            score = 0
            total = questions.count()

            for question in questions:
                selected = request.POST.get(f"question_{question.id}")
                if selected:
                    if question.question_type == "mcq":
                        if selected == question.correct_answer:
                            score += 1
                        else:
                            feedback_list.append(
                                f"Q: {question.question_text} | Your answer: {selected} | Correct: {question.correct_answer}"
                            )
                    else:
                        if selected.strip().lower() == question.correct_answer.strip().lower():
                            score += 1
                        else:
                            feedback_list.append(
                                f"Q: {question.question_text} | Your answer: {selected} | Correct: {question.correct_answer}"
                            )

            percentage = (score / total) * 100 if total > 0 else 0
            progress, _ = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=percentage)
            assign_badges(student)  # <-- Automatic badge assignment

            messages.success(request, f"You scored {score}/{total} ({percentage:.1f}%).")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": percentage,
                "feedback": "\n".join(feedback_list)
            })

        return render(request, "student/exercise_attempt.html", {"exercise": exercise, "questions": questions})


def update_profile(request):
    if not request.session.get('user_id'):
        messages.error(request, "Please login first.")
        return redirect('login')

    user = get_object_or_404(UserRegister, id=request.session['user_id'])

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('update_profile')
    else:
        form = UpdateProfileForm(instance=user)

    return render(request, 'update_profile.html', {'form': form, 'user': user})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lesson, UserRegister
from .forms import LessonForm


def lesson_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')
    lessons = Lesson.objects.filter(created_by_id=request.session['user_id'])
    return render(request, 'lesson/lesson_list.html', {'lessons': lessons})


def lesson_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.created_by_id = request.session['user_id']
            lesson.save()
            messages.success(request, "Lesson created successfully")
            return redirect('lesson_list')
    else:
        form = LessonForm()
    return render(request, 'lesson/lesson_form.html', {'form': form, 'title': 'Add Lesson'})


def lesson_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    lesson = get_object_or_404(Lesson, pk=pk, created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully")
            return redirect('lesson_list')
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'lesson/lesson_form.html', {'form': form, 'title': 'Edit Lesson'})


def lesson_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    lesson = get_object_or_404(Lesson, pk=pk, created_by_id=request.session['user_id'])
    lesson.delete()
    messages.success(request, "Lesson deleted successfully")
    return redirect('lesson_list')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LessonMedia, Lesson
from .forms import LessonMediaForm

def lesson_media_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    medias = LessonMedia.objects.filter(lesson__created_by_id=request.session['user_id'])
    return render(request, 'lesson_media/lesson_media_list.html', {'medias': medias})


def lesson_media_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = LessonMediaForm(request.POST)
        if form.is_valid():
            lesson_media = form.save(commit=False)
            # Ensure teacher only links to their own lesson
            if lesson_media.lesson.created_by_id != request.session['user_id']:
                messages.error(request, "You can only add media to your own lessons.")
                return redirect('lesson_media_list')
            lesson_media.save()
            messages.success(request, "Lesson media added successfully")
            return redirect('lesson_media_list')
    else:
        # Limit lesson dropdown to current teacher’s lessons
        form = LessonMediaForm()
        form.fields['lesson'].queryset = Lesson.objects.filter(created_by_id=request.session['user_id'])

    return render(request, 'lesson_media/lesson_media_form.html', {'form': form, 'title': 'Add Lesson Media'})


def lesson_media_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    media = get_object_or_404(LessonMedia, pk=pk, lesson__created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = LessonMediaForm(request.POST, instance=media)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson media updated successfully")
            return redirect('lesson_media_list')
    else:
        form = LessonMediaForm(instance=media)
        form.fields['lesson'].queryset = Lesson.objects.filter(created_by_id=request.session['user_id'])

    return render(request, 'lesson_media/lesson_media_form.html', {'form': form, 'title': 'Edit Lesson Media'})


def lesson_media_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    media = get_object_or_404(LessonMedia, pk=pk, lesson__created_by_id=request.session['user_id'])
    media.delete()
    messages.success(request, "Lesson media deleted successfully")
    return redirect('lesson_media_list')





from .models import Exercise
from .forms import ExerciseForm


def exercise_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    exercises = Exercise.objects.filter(lesson__created_by_id=request.session['user_id'])
    return render(request, 'exercise/exercise_list.html', {'exercises': exercises})


def exercise_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            # ensure only teacher’s lesson can be linked
            if exercise.lesson.created_by_id != request.session['user_id']:
                messages.error(request, "You cannot add exercises to lessons you don’t own.")
                return redirect('exercise_list')
            exercise.save()
            messages.success(request, "Exercise created successfully")
            return redirect('exercise_list')
    else:
        form = ExerciseForm()
    return render(request, 'exercise/exercise_form.html', {'form': form, 'title': 'Add Exercise'})


def exercise_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    exercise = get_object_or_404(Exercise, pk=pk, lesson__created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated successfully")
            return redirect('exercise_list')
    else:
        form = ExerciseForm(instance=exercise)
    return render(request, 'exercise/exercise_form.html', {'form': form, 'title': 'Edit Exercise'})


def exercise_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    exercise = get_object_or_404(Exercise, pk=pk, lesson__created_by_id=request.session['user_id'])
    exercise.delete()
    messages.success(request, "Exercise deleted successfully")
    return redirect('exercise_list')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Quiz
from .forms import QuizForm

# ----------------------------
# Quiz Questions
# ----------------------------

def quiz_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    # Fetch quizzes for lessons created by the logged-in teacher
    questions = Quiz.objects.filter(exercise__lesson__created_by_id=request.session['user_id'])
    return render(request, 'quiz/quiz_list.html', {'questions': questions})


def quiz_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            if question.exercise.lesson.created_by_id != request.session['user_id']:
                messages.error(request, "You can only add questions to your own exercises.")
                return redirect('quiz_list')
            question.save()
            messages.success(request, "Question created successfully")
            return redirect('quiz_list')
    else:
        form = QuizForm()
    return render(request, 'quiz/quiz_form.html', {'form': form, 'title': 'Add Quiz Question'})


def quiz_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    question = get_object_or_404(Quiz, pk=pk, exercise__lesson__created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = QuizForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully")
            return redirect('quiz_list')
    else:
        form = QuizForm(instance=question)
    return render(request, 'quiz/quiz_form.html', {'form': form, 'title': 'Edit Quiz Question'})


def quiz_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    question = get_object_or_404(Quiz, pk=pk, exercise__lesson__created_by_id=request.session['user_id'])
    question.delete()
    messages.success(request, "Question deleted successfully")
    return redirect('quiz_list')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LiveSession
from .forms import LiveSessionForm

# ----------------------------
# Live Session CRUD
# ----------------------------

def session_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    sessions = LiveSession.objects.filter(tutor_id=request.session['user_id'])
    return render(request, 'session/session_list.html', {'sessions': sessions})


def session_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = LiveSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.tutor_id = request.session['user_id']
            session.save()
            messages.success(request, "Live session created successfully")
            return redirect('session_list')
    else:
        form = LiveSessionForm()
    return render(request, 'session/session_form.html', {'form': form, 'title': 'Add Live Session'})


def session_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    session = get_object_or_404(LiveSession, pk=pk, tutor_id=request.session['user_id'])
    if request.method == "POST":
        form = LiveSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully")
            return redirect('session_list')
    else:
        form = LiveSessionForm(instance=session)
    return render(request, 'session/session_form.html', {'form': form, 'title': 'Edit Live Session'})


def session_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    session = get_object_or_404(LiveSession, pk=pk, tutor_id=request.session['user_id'])
    session.delete()
    messages.success(request, "Session deleted successfully")
    return redirect('session_list')


from django.shortcuts import render
from .models import LiveSession
from django.db.models import Q

def student_sessions(request):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    sessions = LiveSession.objects.all()

    # Search by title
    if search_query:
        sessions = sessions.filter(title__icontains=search_query)

    # Filter by status
    if status_filter:
        sessions = sessions.filter(status=status_filter)

    context = {
        'sessions': sessions,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'student/session_list.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import DiscussionThread, DiscussionPost
from .forms import DiscussionThreadForm, DiscussionPostForm

from django.db.models import Q

def thread_list(request):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    query = request.GET.get('q', '').strip()

    threads = DiscussionThread.objects.all().order_by('-created_at')

    if query:
        threads = threads.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(created_by__username__icontains=query)
        )

    return render(request, 'forum/thread_list.html', {'threads': threads})


#  Create thread
def thread_create(request):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == 'POST':
        form = DiscussionThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by_id = request.session['user_id']
            thread.save()
            messages.success(request, "Thread created successfully.")
            return redirect('thread_list')
    else:
        form = DiscussionThreadForm()

    return render(request, 'forum/thread_form.html', {'form': form, 'title': 'Create Thread'})


#  Delete thread (only by owner)
def thread_delete(request, pk):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    thread = get_object_or_404(DiscussionThread, pk=pk, created_by_id=request.session['user_id'])
    thread.delete()
    messages.success(request, "Thread deleted successfully.")
    return redirect('thread_list')


from django.db.models import Q

def thread_detail(request, pk):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    thread = get_object_or_404(DiscussionThread, pk=pk)

    # Handle search
    query = request.GET.get('q', '')
    posts = thread.posts.all().order_by('created_at')

    if query:
        posts = posts.filter(
            Q(content__icontains=query) | 
            Q(author__full_name__icontains=query)
        )

    post_form = DiscussionPostForm()

    return render(request, 'forum/thread_detail.html', {
        'thread': thread,
        'posts': posts,
        'post_form': post_form,
        'query': query,
    })



#  Create a post
def post_create(request, thread_id):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    thread = get_object_or_404(DiscussionThread, pk=thread_id)

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author_id = request.session['user_id']
            post.save()
            messages.success(request, "Reply added!")
    return redirect('thread_detail', pk=thread_id)


# Delete post (only by owner)
def post_delete(request, pk):
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    post = get_object_or_404(DiscussionPost, pk=pk, author_id=request.session['user_id'])
    thread_id = post.thread.pk
    post.delete()
    messages.success(request, "Post deleted successfully.")
    return redirect('thread_detail', pk=thread_id)


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import UserRegister, PeerChat

def peer_chat(request, user_id=None):
    if not request.session.get('user_id'):
            messages.error(request, "Please login first.")
            return redirect('login')


    current_user = get_object_or_404(UserRegister, id=request.session.get('user_id'))
    users = UserRegister.objects.exclude(id=current_user.id)

    selected_user = None
    messages = None

    if user_id:
        selected_user = get_object_or_404(UserRegister, id=user_id)

        messages = PeerChat.objects.filter(
            Q(sender=current_user, receiver=selected_user) |
            Q(sender=selected_user, receiver=current_user)
        ).order_by('sent_at')

        PeerChat.objects.filter(sender=selected_user, receiver=current_user).update(is_read=True)

        if request.method == "POST":
            content = request.POST.get('message')
            if content:
                PeerChat.objects.create(
                    sender=current_user,
                    receiver=selected_user,
                    message=content
                )
            return redirect('peer_chat', user_id=selected_user.id)

    return render(request, 'chat/peer_chat.html', {
        'users': users,
        'selected_user': selected_user,
        'messages': messages,
    })
