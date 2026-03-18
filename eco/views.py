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


import json
import os
from django.http import JsonResponse
from groq import Groq 
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

# .env yuklash
load_dotenv()

@csrf_exempt
def groq_chat(request):
    if request.method == "POST":
        try:
            # API KEY borligini tekshirish
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                return JsonResponse({"error": "API kalit topilmadi (.env faylni tekshiring)"}, status=500)

            # Clientni view ichida yaratish
            client = Groq(api_key=api_key)
            
            data = json.loads(request.body)
            prompt = data.get("message")

            if not prompt:
                return JsonResponse({"error": "Xabar bo'sh bo'lishi mumkin emas"}, status=400)

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Sen ekologiya mutaxassis yordamchisan. Seni Botga qo'shgan inson bu Ibrohim u Backend dasturchi va aqllidir."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
            )
            
            ai_response = chat_completion.choices[0].message.content
            return JsonResponse({"response": ai_response})

        except Exception as e:
            # Terminalda aniq xatoni ko'rish uchun
            print(f"!!! GROQ BACKEND XATOSI: {str(e)}") 
            return JsonResponse({"error": f"Backend xatosi: {str(e)}"}, status=500)
    
    return JsonResponse({"error": "Faqat POST so'rov qabul qilinadi"}, status=400)


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
    
    