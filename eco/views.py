from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic import ListView, TemplateView, FormView
from django.contrib import messages
from .forms import UserLoginForm
from accounts.models import Users, UserActivities
from .mixins import NotLoginRequiredMixin



class EnteranceTemplateView(TemplateView):
    template_name = 'enterance.html'



class MainTemplateView(TemplateView):
    pass
    
class UserLoginView(NotLoginRequiredMixin, FormView):
    form_class = UserLoginForm
    template_name = 'auth/login.html'
    success_url = 'main'
    login_url = 'login'

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = Users.objects.filter(username=username).first()

        if not user or not user.check_password(password):
            messages.error(self.request, "Parol yoki Login Xato ❌")
            return self.form_invalid(form)

        login(self.request, user)

        messages.success(self.request, "Xush kelibsiz ✅")
        return redirect(self.success_url)

    
    