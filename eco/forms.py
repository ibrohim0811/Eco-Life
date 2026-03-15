from django.forms import ModelForm, Form, CharField, PasswordInput
from django import forms

class UserLoginForm(Form):
    username = CharField()
    password = CharField(widget=PasswordInput)