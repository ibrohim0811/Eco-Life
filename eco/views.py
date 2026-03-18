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
from django.http import JsonResponse



class EnteranceTemplateView(TemplateView):
    template_name = 'enterance.html'



class MainTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['banner'] = True
        context['activity_count'] = UserActivities.objects.filter(user=self.request.user).count()  
        
        context['leaderboard'] = Users.objects.order_by('-points')[:10]
        
        return context
    
    
class UserLoginView(FormView):
    form_class = UserLoginForm
    template_name = 'auth/login.html'
    success_url = "main"
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

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(self.request, "Xush kelibsiz ✅")
        return redirect(self.success_url)


import groq
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

client = groq.Groq(api_key="SENING_GROQ_API_KEYING")

@csrf_exempt
def groq_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Yoki o'zing xohlagan model
                messages=[
                    {"role": "system", "content": "Sen ECOLIFE platformasining yordamchisisan. Foydalanuvchilarga tabiatni asrash va ballar to'plashda yordam berasan. Qisqa va aqlli javob ber."},
                    {"role": "user", "content": user_message}
                ],
            )
            ai_response = completion.choices[0].message.content
            return JsonResponse({"response": ai_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def user_out(request):
    logout(request)  
    return redirect('/')

def check_notifications(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return JsonResponse({
            'unread_count': unread_count
        })
    return JsonResponse({'unread_count': 0}, status=403)



def custom_page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_server_error(request):
    return render(request, 'errors/500.html', status=500)

def custom_permission_denied(request, exception):
    return render(request, 'errors/403.html', status=403)

def custom_bad_request(request, exception):
    return render(request, 'errors/400.html', status=400)
    
    