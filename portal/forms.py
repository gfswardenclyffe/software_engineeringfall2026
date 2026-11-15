from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )

    def clean(self):
        identifier = (self.data.get("username") or "").strip()
        if identifier and "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                data = self.data.copy()
                data["username"] = user.username
                self.data = data
        return super().clean()


class GalielRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="First name")
    last_name = forms.CharField(max_length=150, required=True, label="Last name")
    email = forms.EmailField(max_length=150, required=True, label="Email")
    phone = forms.CharField(max_length=40, required=False, label="Phone (optional)")
    company = forms.CharField(max_length=180, required=False, label="Company / legal name")
    tax_id = forms.CharField(max_length=80, required=False, label="RFC / Tax ID")
    address = forms.CharField(
        max_length=300,
        required=False,
        label="Address (optional)",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    country = forms.CharField(max_length=100, required=False, label="Country (optional)")
    preferred_language = forms.ChoiceField(
        choices=(("en", "English"), ("es", "Español"), ("fr", "Français")),
        initial="en",
        label="Preferred language",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "tax_id",
            "address",
            "country",
            "preferred_language",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].lower().strip()
        user.username = user.email
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data["phone"].strip()
            profile.company = self.cleaned_data["company"].strip()
            profile.tax_id = self.cleaned_data["tax_id"].strip()
            profile.address = self.cleaned_data["address"].strip()
            profile.country = self.cleaned_data["country"].strip()
            profile.preferred_language = self.cleaned_data["preferred_language"]
            profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(max_length=40, required=False)
    company = forms.CharField(max_length=180, required=False, label="Company / legal name")
    tax_id = forms.CharField(max_length=80, required=False, label="RFC / Tax ID")
    address = forms.CharField(max_length=300, required=True, widget=forms.Textarea(attrs={"rows": 3}))
    country = forms.CharField(max_length=100, required=True)
    preferred_language = forms.ChoiceField(
        choices=(("en", "English"), ("es", "Español"), ("fr", "Français")),
        label="Preferred language",
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = getattr(self.instance, "profile", None)
        if profile:
            self.fields["phone"].initial = profile.phone
            self.fields["company"].initial = profile.company
            self.fields["tax_id"].initial = profile.tax_id
            self.fields["address"].initial = profile.address
            self.fields["country"].initial = profile.country
            self.fields["preferred_language"].initial = profile.preferred_language

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            profile.phone = self.cleaned_data["phone"].strip()
            profile.company = self.cleaned_data["company"].strip()
            profile.tax_id = self.cleaned_data["tax_id"].strip()
            profile.address = self.cleaned_data["address"].strip()
            profile.country = self.cleaned_data["country"].strip()
            profile.preferred_language = self.cleaned_data["preferred_language"]
            profile.save()
        return user
