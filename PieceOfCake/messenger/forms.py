from django import forms
from .models import *

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['sender','receiver','message']
