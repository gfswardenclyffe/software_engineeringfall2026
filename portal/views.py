from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import GalielRegistrationForm, UserProfileForm


def home(request):
    return render(request, "portal/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = GalielRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            request.session["registered_username"] = form.cleaned_data["username"]
            return redirect("registration_complete")
    else:
        form = GalielRegistrationForm()

    return render(request, "portal/register.html", {"form": form})


def registration_complete(request):
    username = request.session.pop("registered_username", "")
    return render(request, "portal/registration_complete.html", {"registered_username": username})


@login_required
def dashboard(request):
    return render(request, "portal/dashboard.html")


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            profile = request.user.profile
            profile.phone = request.POST.get("phone", "").strip()
            profile.company = request.POST.get("company", "").strip()
            profile.address = request.POST.get("address", "").strip()
            profile.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "portal/profile_edit.html", {"form": form})
