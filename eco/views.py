import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.generic import ListView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import UserLoginForm
from accounts.models import Users, UserActivities
from .mixins import NotLoginRequiredMixin
from django.conf import settings



class EnteranceTemplateView(TemplateView):
    template_name = 'enterance.html'



class MainTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'main.html'
    
    
class UserLoginView(FormView):
    form_class = UserLoginForm
    template_name = 'auth/login.html'

    def form_valid(self, form):
        
        token = self.request.POST.get('cf-turnstile-response')
        
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': settings.TURNSTILE_SECRET_KEY,
                'response': token,
            }
        )
        result = response.json()

        if not result.get('success'):
            messages.error(self.request, "Xavfsizlik tekshiruvidan o'tolmadingiz. Iltimos qaytadan urinib ko'ring.")
            return self.form_invalid(form)
        
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = Users.objects.filter(username=username).first()

        if not user or not user.check_password(password):
            messages.error(self.request, "Parol yoki Login Xato ❌")
            return self.form_invalid(form)

        login(self.request, user)

        messages.success(self.request, "Xush kelibsiz ✅")
        return redirect(self.success_url)


def user_out(request):
    logout(request)  
    return redirect('/')
    
    