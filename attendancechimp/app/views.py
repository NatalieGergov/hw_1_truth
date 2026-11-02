"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST # HW 4
from django.contrib.auth.models import User
from .models import StudentProfile, InstructorProfile # HW 4
from django.contrib.auth import authenticate, login
from datetime import datetime
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



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



