from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import DriverProfile, User

_CONTROL = (
    "w-full rounded-xl border border-white/30 bg-white/50 px-4 py-3 "
    "text-slate-900 outline-none transition focus:ring-2 focus:ring-violet-500/40 "
    "dark:border-slate-600 dark:bg-slate-900/50 dark:text-white placeholder:text-slate-400"
)


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self)
        self.fields["username"].widget.attrs.setdefault("placeholder", "Username")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Password")


def _style_fields(form):
    for field in form.fields.values():
        w = field.widget
        classes = w.attrs.get("class", "")
        w.attrs["class"] = f"{_CONTROL} {classes}".strip()
        w.attrs.setdefault(
            "placeholder",
            field.label if field.label != "Password" else "••••••••",
        )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self)
        self.fields["password1"].widget.attrs["placeholder"] = "Create a strong password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_driver = False
        if commit:
            user.save()
        return user


class DriverRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    vehicle_number = forms.CharField(max_length=32, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self)
        self.fields["password1"].widget.attrs["placeholder"] = "Create a strong password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"
        self.fields["vehicle_number"].widget.attrs["placeholder"] = "e.g. KA01AB1234"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_driver = True
        if commit:
            user.save()
            DriverProfile.objects.create(
                user=user,
                vehicle_number=self.cleaned_data["vehicle_number"].upper(),
                is_available=True,
            )
        return user
