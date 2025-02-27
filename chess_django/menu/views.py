from datetime import datetime, timezone

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import IntegrityError

from table.models import Game
from django.db.models import Q

from .models import User

# Create your views here.
def index(request):
    return render(request, "menu/index.html")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("menu_index"))
        else:
            return render(request, "menu/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "menu/login.html")
    

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("menu_index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure username is enough length
        if len(username) <= 5:
            return render(request, "menu/register.html", {
                "message": "Username is too short."
            })
        
        # Ensure username is not too long
        if len(password) >= 20:
            return render(request, "menu/register.html", {
                "message": "Username is too long."
            })
        
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "menu/register.html", {
                "message": "Passwords must match."
            })
        
        # Ensure password is enough length
        if (len(password) <= 5):
            return render(request, "menu/register.html", {
                "message": "Passwords is too short."
            })
        
        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "menu/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("menu_index"))
    else:
        return render(request, "menu/register.html")
    
def user(request):
    user = request.user
    userGames = list(Game.objects.filter((Q(white=user) | Q (black=user)) & Q(finished_at__isnull=False)).order_by('-finished_at'))
    for i in range(len(userGames)):
        userGames[i].finished_at = int(userGames[i].finished_at.timestamp() * 1000)

        if userGames[i].winner == "w":
            userGames[i].winner = "w" if user == userGames[i].white else "l"
        if userGames[i].winner == "b":
            userGames[i].winner = "l" if user == userGames[i].white else "w"
        
    games = {'games': userGames}
    return render(request, "menu/user.html", games)

def change_password(request):
    if request.method == "POST":
        # Check current password
        current_password = request.POST["currect_password"]
        if not request.user.check_password(current_password):
            return render(request, "menu/changepassword.html", {
                "message": "Invalid current password."
            })
        
        # Ensure password matches confirmation
        new_password = request.POST["new_password"]
        new_confirmation = request.POST["new_confirmation"]
        if new_password != new_confirmation:
            return render(request, "menu/changepassword.html", {
                "message": "Passwords must match."
            })
        
        # Ensure current password doesnt match new password
        if new_password == current_password:
            return render(request, "menu/changepassword.html", {
                "message": "New password cannot be the same as the current password."
            })
        
        # Ensure password is enough length
        if (len(new_password) <= 5):
            return render(request, "menu/changepassword.html", {
                "message": "Passwords is too short."
            })
        
        # Change the password
        request.user.set_password(new_password)
        request.user.save()

        # Update session to prevent logout after password change
        update_session_auth_hash(request, request.user)

        return HttpResponseRedirect(reverse("user"))
    else:
        return render(request, "menu/changepassword.html")