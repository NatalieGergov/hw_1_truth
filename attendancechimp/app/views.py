"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.models import User
from .models import StudentProfile, InstructorProfile, Course, Lecture, QRCodeUpload
from django.contrib.auth import authenticate, login
from datetime import datetime
from django.utils import timezone
import uuid
import zoneinfo
import json
import io

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""

    # Adding for HW4!!
    current_time = datetime.now(CDT).strftime("%H:%M")
    context = {
        "current_time": current_time,
        "user": request.user, # Not sure if it's necessary to explicitly pass the username
    }

    # context = {}
    return render(request, 'app/index.html', context)

def time_view(request):
    curr_time = datetime.now(CDT)
    return HttpResponse(curr_time.strftime("%H:%M"), content_type="text/plain")

def sum_view(request):
    n1 = float(request.GET.get("n1", 0))
    n2 = float(request.GET.get("n2", 0))
    # return JsonResponse({"sum": n1 + n2})
    return HttpResponse(f"<p>{n1 + n2}</p>", content_type="text/html")


# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

@csrf_exempt
@require_GET
def new_user(request):
    # uses require_GET to guarantee accepting only GET requests
    # POST requests would return an HTTP 405 (method not allowed)
    # could also have used and if/else situation
    return render(request, 'app/new.html')

@csrf_exempt
@require_POST
def createUser(request):

    email = request.POST.get("email")
    user_name = request.POST.get("user_name")
    password = request.POST.get("password")
    is_student = request.POST.get("is_student")

    # All the fields are submitted; otherwise return an error to remind them
    if not email:
        return HttpResponseBadRequest("Missing/invalid email")
    if not user_name:
        return HttpResponseBadRequest("Missing/invalid username")
    if not password:
        return HttpResponseBadRequest("Missing/invalid password")
    if is_student not in ["1", "0"]:
        return HttpResponseBadRequest("Missing/invalid user type")

    # See if the email or the user is already registered
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("Email already exists\n")

    if User.objects.filter(username=user_name).exists():
        return HttpResponseBadRequest("Username already taken\n")

    # Create the user
    user = User.objects.create_user(
        username=user_name,
        email=email,
        password=password
    )

    # Create the appropriate profile
    if is_student == "1":
        StudentProfile.objects.create(user=user)
    else:
        InstructorProfile.objects.create(user=user)

    # Log the newly created user in
    login (request, user)

    return HttpResponse("User created successfully\n", status=200)



# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------

def new_course(request):
    return render(request, 'app/new_course.html')

def new_lecture(request):
    context = { 'courses': Course.objects.all()}
    return render(request, 'app/new_lecture.html', context)

def new_qr_upload(request):
    return render(request, 'app/new_qr_upload.html')

@csrf_exempt
@require_POST
def createCourse(request):

    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse(status=401)

    course_name = request.POST.get('course-name')
    start_time = request.POST.get('start-time')
    end_time = request.POST.get('end-time')

    days= [
        ("day-mon", "Monday"),
        ("day-tue", "Tuesday"),
        ("day-wed", "Wednesday"),
        ("day-thu", "Thursday"),
        ("day-fri", "Friday")
    ]

    meeting_days = []

    for field, day in days:
        if request.POST.get(field):
            meeting_days.append(day)

    if not course_name or not start_time or not end_time or not meeting_days:
        return HttpResponseBadRequest("Missing course information")

    # Ensuring no duplicates because course name is unique (not sure if this is necessary)
    if Course.objects.filter(name=course_name).exists():
        return HttpResponseBadRequest("Course name already exists")

    Course.objects.create(
        name=course_name,
        instructor=request.user.instructorprofile,
        meeting_schedule=f"{', '.join(meeting_days)}: {start_time} to {end_time}"
    )

    return HttpResponse("Course created successfully", status=201)

@csrf_exempt
@require_POST
def createLecture(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse(status=401)

    course_name = request.POST.get('choice')
    if not course_name:
        return HttpResponseBadRequest("Missing course name")

    try:
        course = Course.objects.get(name=course_name)
    except Course.DoesNotExist:
        return HttpResponseBadRequest("Course not found")

    Lecture.objects.create(
        course=course,
        lecture_date=timezone.now(),
        qr=uuid.uuid4().hex
    )

    return HttpResponse("Lecture created successfully", status=201)


@csrf_exempt
@require_POST
def createQRCodeUpload(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    if not hasattr(request.user, 'studentprofile'):
        return HttpResponse(status=401)

    image_file = request.FILES.get('imageUpload')
    if not image_file:
        return HttpResponseBadRequest("No image provided")

    QRCodeUpload.objects.create(
        student=request.user.studentprofile,
        image=image_file
    )
    
    return HttpResponse("QR upload successful", status=201)


@require_GET
def dumpUploads(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    if not hasattr(request.user, 'instructorprofile'):
        return HttpResponse(status=401)

    uploads = QRCodeUpload.objects.select_related('student').all()
    data = []

    for upload in uploads:
        data.append({
            "username": upload.student.user.username,
            "upload_time": timezone.localtime(upload.upload_time).strftime("%Y-%m-%d %H:%M:%S")
        })

    return JsonResponse(data, safe=False)


# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



