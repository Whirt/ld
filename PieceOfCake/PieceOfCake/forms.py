from django import forms
from django.forms import PasswordInput

class SignUpForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=PasswordInput())
    confirm_password = forms.CharField(widget=PasswordInput())
