from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import UserRegisterForm , LoginForm , UpdateProfileForm , QuizQuestionForm, QuizOptionForm
from .models import UserRegister , QuizQuestion , QuizOption
from django.utils import timezone



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
from .models import UserRegister, Lesson, Exercise, StudentProgress, WritingSubmission

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

    # All students with progress
    students = UserRegister.objects.filter(role='student')
    student_data = []
    for student in students:
        progress = StudentProgress.objects.filter(student=student, lesson__created_by_id=teacher_id)
        student_data.append({
            'student': student,
            'progress': progress,
        })

    context = {
        'full_name': teacher_name,
        'total_lessons': total_lessons,
        'total_exercises': total_exercises,
        'total_students': total_students,
        'student_data': student_data,
    }
    return render(request, "teacher_dashboard.html", context)

def teacher_writing_submissions(request):
    # Security check
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    submissions = WritingSubmission.objects.select_related('user', 'exercise', 'exercise__lesson').all()

    return render(request, "teacher_writing_submissions.html", {
        'submissions': submissions
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lesson, Exercise, LessonMedia , StudentProgress

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Lesson, Exercise, LessonMedia, StudentProgress

def student_dashboard(request):
    # Security: only students
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    student_id = request.session.get('user_id')
    student_name = request.session.get('user_name', 'Student')

    # filters
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

    # build list of (lesson, percent)
    lessons_with_progress = []
    for lesson in lessons_qs:
        total_ex = lesson.exercises.count()
        if total_ex == 0:
            percent = None
        else:
            completed_count = StudentProgress.objects.filter(
                student_id=student_id,
                lesson=lesson,
                completed=True
            ).values('exercise').distinct().count()
            percent = int((completed_count / total_ex) * 100)
        lessons_with_progress.append({
            'lesson': lesson,
            'percent': percent
        })

    # recent lists
    recent_lessons = Lesson.objects.all().order_by('-created_at')[:5]
    recent_exercises = Exercise.objects.all().order_by('-id')[:5]

    context = {
        'full_name': student_name,
        'lessons_with_progress': lessons_with_progress,
        'recent_lessons': recent_lessons,
        'recent_exercises': recent_exercises,
        'category_selected': category or '',
        'skill_selected': skill_level or '',
        'q': q,
        'CATEGORY_CHOICES': Lesson.CATEGORIES,
        'SKILL_CHOICES': Lesson.SKILL_LEVELS,
    }
    return render(request, 'student_dashboard.html', context)




def lesson_detail(request, pk):
    # Student must be logged in as student (teachers could also view but we check student)
    if request.session.get('user_role') != 'student':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    lesson = get_object_or_404(Lesson, pk=pk)
    # load related media and exercises
    medias = LessonMedia.objects.filter(lesson=lesson)
    exercises = Exercise.objects.filter(lesson=lesson)

    context = {
        'lesson': lesson,
        'medias': medias,
        'exercises': exercises,
        'full_name': request.session.get('user_name'),
    }
    return render(request, 'student/lesson_detail.html', context)

import pyttsx3
import speech_recognition as sr
from difflib import SequenceMatcher
from spellchecker import SpellChecker
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import (
    Exercise, QuizQuestion, QuizOption, StudentProgress,
    UserRegister, WritingSubmission
)
import string

def exercise_attempt(request, exercise_id):
    # Security check
    if request.session.get("user_role") != "student":
        messages.error(request, "Unauthorized access")
        return redirect("login")

    student = get_object_or_404(UserRegister, id=request.session.get("user_id"))
    exercise = get_object_or_404(Exercise, id=exercise_id)

    # ----------------------------
    # Speaking / Listening Exercises
    # ----------------------------
    if exercise.type in ["speaking", "listening"]:
        # Speak instructions via TTS
        engine = pyttsx3.init()
        engine.say(exercise.instructions)
        engine.runAndWait()

        spoken_text = ""
        feedback = ""
        if exercise.type == "speaking":
            # Record microphone input
            recognizer = sr.Recognizer()
            mic = sr.Microphone()
            print("Please speak the sentence shown in instructions:")
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
                try:
                    spoken_text = recognizer.recognize_google(audio)
                    print("You said:", spoken_text)
                except sr.UnknownValueError:
                    spoken_text = ""
                    print("Could not understand audio")
                except sr.RequestError:
                    spoken_text = ""
                    print("Could not request results; check your connection")

        if request.method == "POST":
            if exercise.type == "speaking":
                # Compare spoken text with instructions
                instructions_text = exercise.instructions.strip().lower()
                spoken_text_clean = request.POST.get("spoken_text", "").strip().lower()
                similarity = SequenceMatcher(None, instructions_text, spoken_text_clean).ratio()
                percentage_score = round(similarity * 100, 1)
                feedback = f"Expected: {exercise.instructions}\nYou said: {spoken_text_clean}"
            else:  # Listening
                percentage_score = 100
                feedback = "Listening exercise auto-completed."

            # Save progress
            progress, created = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=percentage_score)

            messages.success(request, f"You scored {percentage_score}% for this {exercise.type} exercise.")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": percentage_score,
                "feedback": feedback,
                "spoken_text": spoken_text
            })

        # Render template
        template = "student/exercise_speaking.html" if exercise.type == "speaking" else "student/exercise_listening.html"
        return render(request, template, {
            "exercise": exercise,
            "spoken_text": spoken_text,
        })

    # ----------------------------
    # Writing Exercise
    # ----------------------------
    elif exercise.type == "writing":
        if request.method == "POST":
            essay_text = request.POST.get("essay_text", "").strip()

            # Spell check using PySpellChecker
            spell = SpellChecker()
            words = essay_text.split()
            clean_words = [w.strip(string.punctuation).lower() for w in words]
            misspelled = spell.unknown(clean_words)
            spelling_feedback = ", ".join(misspelled) if misspelled else "No spelling mistakes found."

            # Optional: basic grammar feedback (like repeated words)
            grammar_feedback = ""
            prev_word = ""
            for w in clean_words:
                if w == prev_word:
                    grammar_feedback += f"Repeated word: {w}\n"
                prev_word = w

            # Save submission
            submission = WritingSubmission.objects.create(
                user=student,
                exercise=exercise,
                essay_text=essay_text,
                grammar_feedback=grammar_feedback,
                spelling_feedback=spelling_feedback
            )

            # Mark progress
            progress, created = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=100)

            messages.success(request, "Essay submitted successfully with feedback!")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": 100,
                "feedback": f"Grammar Issues:\n{grammar_feedback}\nSpelling Issues:\n{spelling_feedback}",
                "essay_text": essay_text
            })

        return render(request, "student/exercise_writing.html", {
            "exercise": exercise
        })

    # ----------------------------
    # Quiz Exercise
    # ----------------------------
    else:
        questions = exercise.questions.prefetch_related("options").all()
        feedback_list = []
        if request.method == "POST":
            score = 0
            total = questions.count()
            for question in questions:
                selected = request.POST.get(f"question_{question.id}")
                if selected:
                    if question.question_type == "mcq":
                        option = QuizOption.objects.filter(id=selected, question=question).first()
                        if option and option.is_correct:
                            score += 1
                        else:
                            feedback_list.append(f"Q: {question.question_text} | Your answer: {option.option_text if option else 'None'} | Correct: {question.correct_answer}")
                    else:
                        if selected.strip().lower() == question.correct_answer.strip().lower():
                            score += 1
                        else:
                            feedback_list.append(f"Q: {question.question_text} | Your answer: {selected} | Correct: {question.correct_answer}")

            percentage = (score / total) * 100 if total > 0 else 0
            progress, created = StudentProgress.objects.get_or_create(
                student=student, lesson=exercise.lesson, exercise=exercise
            )
            progress.mark_complete(score=percentage)

            messages.success(request, f"You scored {score}/{total} ({percentage:.1f}%).")
            return render(request, "student/exercise_feedback.html", {
                "exercise": exercise,
                "score": percentage,
                "feedback": "\n".join(feedback_list)
            })

        return render(request, "student/exercise_attempt.html", {
            "exercise": exercise,
            "questions": questions,
        })




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



# ----------------------------
# Quiz Questions
# ----------------------------
def quizquestion_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    questions = QuizQuestion.objects.filter(exercise__lesson__created_by_id=request.session['user_id'])
    return render(request, 'quiz/quizquestion_list.html', {'questions': questions})


def quizquestion_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            if question.exercise.lesson.created_by_id != request.session['user_id']:
                messages.error(request, "You can only add questions to your own exercises.")
                return redirect('quizquestion_list')
            question.save()
            messages.success(request, "Question created successfully")
            return redirect('quizquestion_list')
    else:
        form = QuizQuestionForm()
    return render(request, 'quiz/quizquestion_form.html', {'form': form, 'title': 'Add Quiz Question'})


def quizquestion_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    question = get_object_or_404(QuizQuestion, pk=pk, exercise__lesson__created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = QuizQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully")
            return redirect('quizquestion_list')
    else:
        form = QuizQuestionForm(instance=question)
    return render(request, 'quiz/quizquestion_form.html', {'form': form, 'title': 'Edit Quiz Question'})


def quizquestion_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    question = get_object_or_404(QuizQuestion, pk=pk, exercise__lesson__created_by_id=request.session['user_id'])
    question.delete()
    messages.success(request, "Question deleted successfully")
    return redirect('quizquestion_list')



def quizoption_list(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    options = QuizOption.objects.filter(question__exercise__lesson__created_by_id=request.session['user_id'])
    return render(request, 'quiz/quizoption_list.html', {'options': options})


def quizoption_create(request):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    if request.method == "POST":
        form = QuizOptionForm(request.POST)
        if form.is_valid():
            option = form.save(commit=False)
            if option.question.exercise.lesson.created_by_id != request.session['user_id']:
                messages.error(request, "You can only add options to your own questions.")
                return redirect('quizoption_list')
            option.save()
            messages.success(request, "Option created successfully")
            return redirect('quizoption_list')
    else:
        form = QuizOptionForm()
    return render(request, 'quiz/quizoption_form.html', {'form': form, 'title': 'Add Quiz Option'})


def quizoption_update(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    option = get_object_or_404(QuizOption, pk=pk, question__exercise__lesson__created_by_id=request.session['user_id'])
    if request.method == "POST":
        form = QuizOptionForm(request.POST, instance=option)
        if form.is_valid():
            form.save()
            messages.success(request, "Option updated successfully")
            return redirect('quizoption_list')
    else:
        form = QuizOptionForm(instance=option)
    return render(request, 'quiz/quizoption_form.html', {'form': form, 'title': 'Edit Quiz Option'})


def quizoption_delete(request, pk):
    if request.session.get('user_role') != 'teacher':
        messages.error(request, "Unauthorized access")
        return redirect('login')

    option = get_object_or_404(QuizOption, pk=pk, question__exercise__lesson__created_by_id=request.session['user_id'])
    option.delete()
    messages.success(request, "Option deleted successfully")
    return redirect('quizoption_list')
