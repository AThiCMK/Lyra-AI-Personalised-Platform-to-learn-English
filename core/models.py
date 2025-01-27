import uuid
import os
import json
from django.db import models, transaction
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now
from datetime import timedelta

audio_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'audio_files'))

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, null=False)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=[('faculty', 'Faculty'), ('student', 'Student')], default='student')
    staff_id = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None)
    roll_number = models.CharField(max_length=50, unique=True, blank=True, null=True, default=None)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class FacultyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='faculty_profile')
    staff_id = models.CharField(max_length=50, unique=True)
    session_id = models.CharField(max_length=50, unique=True)
    students_handling = models.PositiveIntegerField()

    def __str__(self):
        return self.user.username

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=50, unique=True)
    session_id = models.CharField(max_length=100)
    level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.user.username} - {self.level}'

class TestProgress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
    )
    level = models.IntegerField(default=0)
    test_type = models.CharField(
        max_length=20,
        choices=[('reading', 'Reading'), ('listening', 'Listening'), ('speaking', 'Speaking')],
    )
    status = models.CharField(
        max_length=20, 
        choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed')], 
        default='not_started',
    )
    score = models.FloatField(blank=True, null=True)
    max_score = models.FloatField(default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'category', 'level', 'test_type')

    def __str__(self):
        return f"{self.student.user.username} - {self.category} Level {self.level} ({self.test_type})"

class Sentence(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sentence = models.TextField(unique=True) 
    category = models.CharField(max_length=15, choices=LEVEL_CHOICES)
    difficulty = models.CharField(max_length=10)
    level = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id}: {self.category} ({self.level}) - {self.difficulty}"

class TestProfile(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    test_progress = models.ForeignKey(TestProgress, on_delete=models.CASCADE)
    sentences = models.ManyToManyField(Sentence)
    audio_files = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    test_restarted = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def add_audio(self, sentence_uuid, audio_file):
        try:
            filename = f"{sentence_uuid}_{self.student.roll_number}.wav"
            saved_path = audio_storage.save(filename, audio_file)

            with transaction.atomic():
                latest_instance = TestProfile.objects.select_for_update().get(id=self.id)
                audio_data = dict(latest_instance.audio_files or {})

                print("DEBUG: Before update:", audio_data)
                audio_data[sentence_uuid] = saved_path
                latest_instance.audio_files = audio_data
                latest_instance.last_updated = now()
                latest_instance.save(update_fields=['audio_files', 'last_updated'])

            print(f"DEBUG: Audio file saved at {saved_path}")
            latest_data = TestProfile.objects.get(id=self.id).audio_files
            print(f"DEBUG: Final stored audio_files JSON: {latest_data}")

        except Exception as e:
            print(f"DEBUG: Error saving audio file: {e}")
            raise ValueError("Failed to save audio file.")

    def add_result(self, sentence_uuid, result):
        audio_path = self.audio_files.get(sentence_uuid)
        if not audio_path:
            raise ValueError(f"No audio file linked for sentence UUID: {sentence_uuid}")

        self.results[sentence_uuid] = result
        self.save(update_fields=['results'])

        full_path = os.path.join(settings.MEDIA_ROOT, audio_path)
        if os.path.exists(full_path):
            os.remove(full_path)

        del self.audio_files[sentence_uuid]
        self.save(update_fields=['audio_files'])

    def __str__(self):
        return f"TestProfile for {self.student} - {self.test_progress.category} Level {self.test_progress.level}"

class LearningContent(models.Model):
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='learning_contents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file} - {self.faculty.staff_id}"