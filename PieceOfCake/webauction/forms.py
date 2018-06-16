from .models import *
from django import forms

class MakeAuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'image', 'description', 'min_price',
                    'min_bid', 'category']
        widgets = {
                   'category' : forms.Select(choices=CATEGORY_CHOICES),
                   'description' : forms.Textarea(attrs={'rows':20, 'cols':58}),
                  }
