from django.forms import ModelForm, Form, CharField, PasswordInput
from django import forms
from accounts.models import Users

class UserLoginForm(Form):
    username = CharField()
    password = CharField(widget=PasswordInput)
    
from django import forms
from .models import Users  # Model nomingiz Users ekanligiga qarab

class ProfileSettingsForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'username', 'gmail', 'about', 'profile_image']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance') 
        super(ProfileSettingsForm, self).init(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)

        
        if self.cleaned_data.get('profile_image'):
            user.avatar = self.cleaned_data['profile_image']

        if hasattr(user, 'subscription') and user.subscription.plan == "Free":
            user.gmail = self.instance.gmail 
        else:
            user.gmail = self.cleaned_data.get('gmail')

        if commit:
            user.save()

        return user