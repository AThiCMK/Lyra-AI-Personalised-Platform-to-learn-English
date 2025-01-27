from asyncio.windows_events import NULL
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import FacultyProfile, StudentProfile, CustomUser, LearningContent, TestProgress, TestProfile
from .forms import FacultyRegistrationForm, StudentRegistrationForm, LoginForm, LevelSelectionForm, ReadingTestForm

def faculty_register(request):
    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = FacultyRegistrationForm()
    return render(request, 'core/faculty_register.html', {'form': form})

def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            session_id = form.cleaned_data['session_id']
            faculty = FacultyProfile.objects.filter(session_id=session_id).first()

            if not faculty:
                form.add_error('session_id', 'Invalid Session ID')
            elif StudentProfile.objects.filter(session_id=session_id).count() > faculty.students_handling:
                print(StudentProfile.objects.filter(session_id=session_id).count(), faculty.students_handling)
                form.add_error('session_id', 'Session is full')
            else: 
                form.save()
                return redirect('login')

    else:
        form = StudentRegistrationForm()
    return render(request, 'core/student_register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid ID or Password')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login') 

@login_required
def home_view(request):
    user = request.user
    if user.staff_id is not None:
        return redirect('faculty_home')
    elif user.roll_number is not None:
        return redirect('student_dashboard')
    else:
        return redirect('login')

@login_required
def faculty_home(request):
    user = request.user
    user = CustomUser.objects.get(staff_id=user.staff_id)
    faculty = FacultyProfile.objects.get(staff_id=user.staff_id)
    enrolled_students_count = StudentProfile.objects.filter(session_id=faculty.session_id).count()
    return render(request, 'faculty/faculty_home.html', {
        'faculty': user,
        'enrolled_students_count': enrolled_students_count,
    })

@login_required
def enrolled_students(request):
    faculty = FacultyProfile.objects.get(staff_id=request.user.staff_id)
    students = StudentProfile.objects.filter(session_id=faculty.session_id)
    return render(request, 'faculty/enrolled_students.html', {'students': students})

@login_required
def upload_content(request):
    if request.method == 'POST':
        file = request.FILES['file']
        faculty = FacultyProfile.objects.get(staff_id=request.user.staff_id)
        LearningContent.objects.create(faculty=faculty, file=file)
        return redirect('faculty_home')
    return render(request, 'faculty/upload_content.html')

@login_required
def student_dashboard(request):
    user = request.user
    user = CustomUser.objects.get(roll_number=user.roll_number)
    student_profile = StudentProfile.objects.get(roll_number=user.roll_number)

    if student_profile.level is None:
        return redirect('student_level_selection')

    level = student_profile.level
    if level == 'beginner':
        return redirect('beginner_dashboard')
    elif level == 'intermediate':
        return redirect('intermediate_dashboard')
    elif level == 'advanced':
        return redirect('advanced_dashboard')

    return redirect('student_level_selection')

@login_required
def student_level_selection(request):
    student_profile = StudentProfile.objects.get(roll_number=request.user.roll_number)

    if student_profile.level is not None:
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = LevelSelectionForm(request.POST)
        if form.is_valid():
            level = form.cleaned_data['level']
            student_profile.level = level
            student_profile.save()
            create_tests_for_student(student_profile)
            return redirect('student_dashboard')
    else:
        form = LevelSelectionForm()

    return render(request, 'student/student_level_selection.html', {'form': form})

def create_tests_for_student(student_profile):
    category = student_profile.level
    if category == 'beginner':
        test_types = ['reading', 'listening']
        max_levels = 5
    else:
        test_types = ['reading', 'listening', 'speaking']
        max_levels = 5

    for level in range(1, max_levels + 1):
        for test_type in test_types:
            if not TestProgress.objects.filter(
                student=student_profile,
                category=category,
                level=level,
                test_type=test_type
            ).exists():
                TestProgress.objects.create(
                    student=student_profile,
                    category=category,
                    level=level,
                    test_type=test_type,
                )

@login_required
def beginner_dashboard(request):
    student_profile = StudentProfile.objects.get(roll_number=request.user.roll_number)
    reading_tests = TestProgress.objects.filter(student=student_profile, category='beginner', test_type='reading')
    listening_tests = TestProgress.objects.filter(student=student_profile, category='beginner', test_type='listening')

    context = {
        'student': student_profile,
        'reading_tests': reading_tests,
        'listening_tests': listening_tests,
    }
    return render(request, 'student/beginner_dashboard.html', context)

@login_required
def intermediate_dashboard(request):
    student_profile = StudentProfile.objects.get(roll_number=request.user.roll_number)
    reading_tests = TestProgress.objects.filter(student=student_profile, category='intermediate', test_type='reading')
    listening_tests = TestProgress.objects.filter(student=student_profile, category='intermediate', test_type='listening')
    speaking_tests = TestProgress.objects.filter(student=student_profile, category='intermediate', test_type='speaking')

    context = {
        'student': student_profile,
        'reading_tests': reading_tests,
        'listening_tests': listening_tests,
        'speaking_tests': speaking_tests,
    }
    return render(request, 'student/intermediate_dashboard.html', context)

@login_required
def advanced_dashboard(request):
    student_profile = StudentProfile.objects.get(roll_number=request.user.roll_number)
    reading_tests = TestProgress.objects.filter(student=student_profile, category='advanced', test_type='reading')
    listening_tests = TestProgress.objects.filter(student=student_profile, category='advanced', test_type='listening')
    speaking_tests = TestProgress.objects.filter(student=student_profile, category='advanced', test_type='speaking')

    context = {
        'student': student_profile,
        'reading_tests': reading_tests,
        'listening_tests': listening_tests,
        'speaking_tests': speaking_tests,
    }
    return render(request, 'student/advanced_dashboard.html', context)

@csrf_exempt
@login_required
def reading_test_view(request, category, level):
    student_profile = get_object_or_404(StudentProfile, roll_number=request.user.roll_number)
    test_progress = get_object_or_404(
        TestProgress,
        student=student_profile,
        category=category,
        level=level,
        test_type='reading',
    )

    if test_progress.status == "completed":
        messages.info(request, "You have already completed this test.")
        return redirect(reverse(f'{category}_dashboard'))

    form = ReadingTestForm(student_profile=student_profile, test_progress=test_progress)
    test_profile = form.get_test_profile()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            print("DEBUG: Request method:", request.method)
            print("DEBUG: Headers:", request.headers)
            print("DEBUG: Request POST Data:", request.POST)
            print("DEBUG: Request FILES Data:", request.FILES)
            sentence_uuid = request.POST.get('sentence_uuid')
            print(f'audio_{sentence_uuid}')
            audio_file = request.FILES.get(f'audio_{sentence_uuid}')

            print("DEBUG: Received Sentence UUID:", sentence_uuid)
            print("DEBUG: Received Audio File:", audio_file)

            if not sentence_uuid or not audio_file:
                return JsonResponse({'status': 'error', 'message': 'Invalid data received.'}, status=400)

            with transaction.atomic():
                test_profile.add_audio(sentence_uuid, audio_file)
            test_profile = TestProfile.objects.get(id=test_profile.id)
            completed_count = len(test_profile.audio_files)
            print("DEBUG: New completed count:", completed_count)

            if completed_count >= 5:
                with transaction.atomic():
                    test_progress.status = "completed"
                    test_progress.save()
                    messages.success(request, "Test completed successfully.")
                    print("DEBUG: Test marked as completed")
                    return JsonResponse({'status': 'completed'})

            all_sentences = list(test_profile.sentences.all())
            next_sentence = all_sentences[completed_count]
            return JsonResponse({
                'status': 'next',
                'sentence_uuid': next_sentence.id,
                'sentence_text': next_sentence.sentence,
            })

        except Exception as e:
            print("DEBUG: Error occurred during POST:", e)
            return JsonResponse({'status': 'error', 'message': 'Unexpected server error occurred.'}, status=500)

    elif request.method == 'GET':
        if len(test_profile.sentences.all()) < 5:
            messages.error(request, "Failed to create a valid test. Please try again.")
            test_profile.delete()
            return redirect(reverse(f'{category}_dashboard'))

        sentences = list(test_profile.sentences.all())
        current_sentence_index = len(test_profile.audio_files)
        current_sentence = sentences[current_sentence_index] if current_sentence_index < 5 else None

        if not current_sentence:
            messages.error(request, "Unexpected error. Please restart the test.")
            test_profile.delete()
            return redirect(reverse(f'{category}_dashboard'))

        return render(request, 'student/reading_test_platform.html', {
            'test_profile': test_profile,
            'current_sentence': current_sentence,
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request type.'}, status=400)