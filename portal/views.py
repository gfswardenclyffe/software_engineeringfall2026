from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile


def home(request):
    return render(request, "portal/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "portal/register.html", {"form": form})


@login_required
def dashboard(request):
    Profile.objects.get_or_create(user=request.user)
    return render(request, "portal/dashboard.html")


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    return render(
        request,
        "portal/profile.html",
        {"profile": profile},
    )


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(
        request,
        "portal/edit_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
