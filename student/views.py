from django.shortcuts import render
from student.models import Student
from django.db.models import Count
import errorpage
import hashlib

def index(request):
    # Maybe do this in the database?
    top_users = sorted(Student.objects.all(), key=lambda s: s.solution_count, reverse=True)
    return render(request, "student/index.html",
        {"students" : top_users })

def profile(request, uid):
    try:
        s = Student.objects.get(student_id=uid)
    except:
        return errorpage.views.index(request)
    return render(request, "student/student.html",
            {"student" : s,
             "email_md5" : hashlib.md5(s.student_id + "@uwindsor.ca").hexdigest()
            }
        )
