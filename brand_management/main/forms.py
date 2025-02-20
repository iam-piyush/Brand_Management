from django import forms
from .models import Brand, Newsletter, Campaign, Subscriber

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'brand_id', 'email', 'phone', 'address']

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = []

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name"]

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['subscriber_id', 'name', 'email', 'phone']
        widgets = {
            'subscriber_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
        }
