from django.shortcuts import render
import random

def index(request):
    return render(request, "errorpage/404.html", {"quote" : random_quote()})

def random_quote():
    return random.choice([
        "Proof to me this page does not exist",

        "Well its really quite simple you know, this page does not exist",

        "Class, are you with me?  This page does not exist!",

        "I have gained an immense amount of knowledge in my time, and I can safely "
        + "conclude that this page in fact does not exist",
    ])
