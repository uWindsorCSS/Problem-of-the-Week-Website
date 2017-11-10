from django.shortcuts import render, redirect
from student.models import Student
from problem.models import Problem
from django.db.models import Count
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from helpers import get_or_none
from django.views.decorators.http import require_http_methods
import errorpage
import hashlib
import hmac
import datetime
import re

def index(request):
    problem = Problem.objects.filter(published=True).order_by("-week")[0]
    context = {
        "problem": problem,
    }

    if "submitcode" in request.session:
        context["submitcode"] = request.session["submitcode"]
    return render(request, "student/index.html", context)

def solvers(request):
    # Maybe do this in the database?
    top_users = sorted(Student.objects.all(), key=lambda s: s.solution_count, reverse=True)
    return render(request, "student/solvers.html", {"students" : top_users })

def profile(request, uid):
    student = get_or_none(Student, student_id=uid)
    if student is None:
        return errorpage.views.index(request)

    context = {
        "student":   student,
        "email_md5": hashlib.md5(student.student_id + "@uwindsor.ca").hexdigest(),
        "solutions": student.solution_set.order_by("week")
    }
    return render(request, "student/student.html", context)

def unsubscribe(request, student_id):
    s  = get_or_none(Student, student_id=student_id)
    if s is None:
        return errorpage.views.index(request)

    s.subscribed = False
    s.save()
    return sign_up(request, None, "Successfully unsubscribed!")

def sign_up(request, error=None, success=None):
    context = {
        "error":   error,
        "success": success,
    }
    return render(request, "student/signup.html", context)

'''
Send a verification email to the user.
'''
@require_http_methods(["POST"])
def send_verify(request):
    if 'uwinid' not in request.POST or len(request.POST['uwinid']) == 0:
        return sign_up(request, "Please enter your uWindsor ID", {})

    uwinid_check = re.compile("(\d|[a-zA-Z])+$")
    if uwinid_check.match(request.POST['uwinid']) == None:
        return sign_up(request, "That uWindsor ID is invalid", {})

    u = get_or_none(Student, student_id=request.POST['uwinid'])
    if u is not None:
        return sign_up(request, "That uWindsor ID is already registered", {})

    '''
    Generate a verification hash by concatenating a special EMAIL_SECRET
    string, the users uwindsor ID, and the current hour.  This allows for an
    implicit "time out."  Once the hour changes, the hash will be invalided.
    Now this does mean that if the user submits at 1:59pm and the email comes
    at 2:00pm the code will be invalid, but thats just something we need to
    live with, man.
    '''
    now = datetime.datetime.now()
    verify_hash = hmac.new(settings.EMAIL_SECRET,
            request.POST['uwinid'] + str(now.hour)).hexdigest()

    send_mail("uWindsor POTW - Confirm ID",
            "Click the following link to confirm your uWindsor ID and begin"+\
            " submitting your problem of the week solutions.\n"+\
            settings.SITE_URL+"/student/verify/" + request.POST['uwinid'] + "/"+\
            verify_hash,
            "noreply@potw.cs.uwindsor.ca",
            [request.POST['uwinid'] + "@uwindsor.ca"],
            fail_silently=False)

    return sign_up(request, None, "Email Sent")

'''
Verify a user with a verification hash.
'''
def verify(request, uwinid, verify_hash):
    u = get_or_none(Student, student_id=uwinid)
    if u is not None:
        return redirect("/")

    '''
    Create the expected hash by concatenating the EMAIL_SECRET, uwind id,
    and current hour.  If the hour has changed since the user was sent the email,
    the hash will be invalided.
    '''
    now = datetime.datetime.now()
    check = hmac.new(settings.EMAIL_SECRET,
            uwinid + str(now.hour)).hexdigest()

    '''
    hmac compare_digest is used here instead of == to defend against timing
    attacks.  It always compares all bytes instead of bailing out on the first
    differing one.
    '''
    if hmac.compare_digest(str(check), str(verify_hash)):
        s_code = get_random_string(length=10)
        Student.objects.create(student_id = uwinid,
                submit_code = s_code)
        send_mail("uWindsor POTW - Submission Code",
                "Your submission code is " + s_code + ", keep it safe.",
                "noreply@potw.cs.uwindsor.ca",
                [uwinid + "@uwindsor.ca"],
                fail_silently=False)
        return render(request, "student/verify_success.html", {"code" : s_code})
    else:
        return render(request, "student/verify_success.html", {"error" : "This link is either expiried or invalid"})
