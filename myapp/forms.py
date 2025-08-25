from django import forms
from django.contrib.auth.hashers import make_password
from .models import UserRegister


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    class Meta:
        model = UserRegister
        fields = ['full_name', 'email', 'password', 'role', 'gender', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])  # hash password
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter password'
    }))
    role = forms.ChoiceField(choices=[('teacher', 'Teacher'), ('student', 'Student')],
                             widget=forms.Select(attrs={'class': 'form-control'}))


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = UserRegister
        fields = [
            'full_name', 'email', 'gender', 'dob', 'profile_picture',
            'phone', 'bio', 'country', 'city'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }


from django import forms
from .models import Lesson


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'skill_level', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lesson title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }


from django import forms
from .models import LessonMedia

class LessonMediaForm(forms.ModelForm):
    class Meta:
        model = LessonMedia
        fields = ['lesson', 'media_type', 'media_url']
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-select'}),
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'media_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter Media URL'}),
        }


from django import forms
from .models import Exercise

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['lesson', 'type', 'instructions']
        widgets = {
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'lesson': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
        }


from .models import QuizQuestion, QuizOption

class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ['exercise', 'question_text', 'question_type', 'correct_answer']
        widgets = {
            'exercise': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'correct_answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class QuizOptionForm(forms.ModelForm):
    class Meta:
        model = QuizOption
        fields = ['question', 'option_text', 'is_correct']
        widgets = {
            'question': forms.Select(attrs={'class': 'form-select'}),
            'option_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
