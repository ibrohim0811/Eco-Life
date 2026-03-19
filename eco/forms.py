from django.forms import ModelForm, Form, CharField, PasswordInput
from django import forms
from accounts.models import Users

class UserLoginForm(Form):
    username = CharField()
    password = CharField(widget=PasswordInput)



class ProfileSettingsForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'username', 'gmail', 'about', 'avatar']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance') 
        super(ProfileSettingsForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)

        
        if self.cleaned_data.get('avatar'):
            user.image = self.cleaned_data['avatar']

        if hasattr(user, 'subscription') and user.subscription.plan == "Free":
            user.gmail = self.instance.gmail 
        else:
            user.gmail = self.cleaned_data.get('gmail')

        if commit:
            user.save()

        return user