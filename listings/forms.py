from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(required=False, label="Nombre")
    last_name = forms.CharField(required=False, label="Apellidos")
    email = forms.EmailField(required=False, label="Email")

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")
