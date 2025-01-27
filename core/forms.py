import random
from django import forms
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from .models import CustomUser, FacultyProfile, StudentProfile, Sentence, TestProfile

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="User ID")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

class FacultyRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    students_handling = forms.IntegerField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'staff_id', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.session_id = f"SESSION-{user.staff_id}"
        user.set_password(self.cleaned_data['password'])
        user.role = 'faculty'
        if commit:
            user.save()
            FacultyProfile.objects.create(user=user, staff_id = user.staff_id, session_id = user.session_id, students_handling=self.cleaned_data['students_handling'])
        return user

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    session_id = forms.CharField(max_length=50)

    class Meta:
        model = CustomUser
        fields = ['username', 'roll_number', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'
        if commit:
            user.save()
            StudentProfile.objects.create(user=user, roll_number= self.cleaned_data['roll_number'], session_id=self.cleaned_data['session_id'])
        return user

class LevelSelectionForm(forms.Form):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    level = forms.ChoiceField(choices=LEVEL_CHOICES, label="Select your level")

    def clean_level(self):
        level = self.cleaned_data.get('level')
        if not level:
            raise forms.ValidationError("Please select a level")
        return level

class ReadingTestForm(forms.Form):
    TIMEOUT_MINUTES = 5

    def __init__(self, *args, **kwargs):
        student_profile = kwargs.pop('student_profile')
        test_progress = kwargs.pop('test_progress')
        super().__init__(*args, **kwargs)

        test_profile, created = TestProfile.objects.get_or_create(
            student=student_profile,
            test_progress=test_progress,
        )

        if not created:
            time_since_last_update = now() - test_profile.last_updated

            if time_since_last_update > timedelta(minutes=self.TIMEOUT_MINUTES):
                test_profile.test_restarted = True

        if test_profile.test_restarted:
            test_profile.sentences.clear()
            test_profile.audio_files.clear()
            test_profile.results.clear()
            test_profile.test_restarted = False
            test_profile.save()

        self.test_profile = test_profile

        sentences_easy = Sentence.objects.filter(
            category=test_progress.category,
            level=test_progress.level,
            difficulty='easy'
        )
        sentences_medium = Sentence.objects.filter(
            category=test_progress.category,
            level=test_progress.level,
            difficulty='medium'
        )
        sentences_hard = Sentence.objects.filter(
            category=test_progress.category,
            level=test_progress.level,
            difficulty='hard'
        )

        difficulty_pattern = {
            1: {'easy': 2, 'medium': 2, 'hard': 1},
            2: {'easy': 2, 'medium': 2, 'hard': 1},
            3: {'easy': 1, 'medium': 2, 'hard': 2},
            4: {'easy': 1, 'medium': 2, 'hard': 2},
            5: {'easy': 0, 'medium': 2, 'hard': 3},
        }

        pattern = difficulty_pattern.get(test_progress.level, {'easy': 2, 'medium': 2, 'hard': 1})

        selected_sentences = []
        for difficulty, count in pattern.items():
            sentence_pool = locals()[f"sentences_{difficulty}"]
            if sentence_pool.count() < count:
                raise ValueError(f"Not enough {difficulty} sentences available for the selected test.")
            selected_sentences.extend(random.sample(list(sentence_pool), count))

        if not test_profile.sentences.exists():
            test_profile.sentences.set(selected_sentences)
            test_profile.test_restarted = False
            test_profile.save()

    def get_test_profile(self):
        return self.test_profile
