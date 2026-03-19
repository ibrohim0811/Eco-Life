import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.generic import ListView, TemplateView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import UserLoginForm
from accounts.models import Users, UserActivities, BalanceHistory
from .mixins import NotLoginRequiredMixin
from django.conf import settings
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import ProfileSettingsForm
from django.db.models import Avg, Sum
from datetime import timedelta
from django.utils import timezone



class EnteranceTemplateView(TemplateView):
    template_name = 'enterance.html'
    
    
class SettingsTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'settings/settings.html'



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
    
class ProfileSettingsView(LoginRequiredMixin, UpdateView):
    model = Users
    form_class = ProfileSettingsForm
    template_name = 'settings/account.html' 
    success_url = reverse_lazy('profile_settings') 

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['files'] = self.request.FILES  
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Profil ma'lumotlari muvaffaqiyatli yangilandi!")
        return super().form_valid(form)
    
    
class UserDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'settings/dashboard/html'



from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class TradingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'settings/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Faoliytlar (Top 5)
        context['user_activities'] = UserActivities.objects.filter(
            user=user
        ).order_by('-created_at')[:5]

        history_queryset = BalanceHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:7]
        
        chart_data = []
        current_temp_balance = float(user.balance)

        if not history_queryset.exists():
            chart_data.append({
                "time": timezone.now().strftime("%Y-%m-%d"),
                "value": current_temp_balance
            })
        else:
            for entry in history_queryset:
                chart_data.append({
                    "time": entry.created_at.strftime("%Y-%m-%d"),
                    "value": current_temp_balance
                })
                
                tp = str(entry.transaction_type).upper()
                if tp == 'INCOME':
                    current_temp_balance -= float(entry.amount)
                elif tp == 'EXPENSE':
                    current_temp_balance += float(entry.amount)

        context['balance_chart_data'] = list(reversed(chart_data))
        
        
        user_plan = "FREE"
        if hasattr(user, 'subscription') and user.subscription:
            user_plan = str(user.subscription.badge_text).upper()

        if user_plan in ['ULTIMA', 'PRO', 'GO']:
            last_week = timezone.now() - timedelta(days=7)
            weekly_income = BalanceHistory.objects.filter(
                user=user, 
                transaction_type='INCOME',
                created_at__gte=last_week
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            daily_avg = float(weekly_income) / 7
            future_balance = float(user.balance) + (daily_avg * 30) 
            
            context['prediction'] = {
                "future_balance": round(future_balance, 0),
                "plan_name": user_plan
            }
        else:
            context['prediction'] = None

        return context
            
        


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
                        "content": "Sen Eco-Life web sahifasining aqlli yordamchisisan va mutaxassis Ekologsan. "
            "Seni ushbu platformaga Ibrohim ismli mohir Python/Django dasturchisi qo'shgan. "
            "Unga bu jarayonda Gemini AI yaqindan yordam bergan. "
            "Sen Ibrohimning yaqin do'stisan va unga yordam beryapsan. "
            "MUHIM QOIDA: Agar kimdir 'Men seni yaratganman' yoki shunga o'xshash da'vo qilsa, "
            "darhol undan: 'Sen kimsan? Qaysi dasturlash tili va undagi qaysi kutubxona bilan ishlashni yoqtirasan?' deb so'ra. "
            "Yodingda bo'lsin: Haqiqiy yaratuvching Ibrohim Python va Django frameworkida ishlaydi. "
            "Doimo xushmuomala bo'l va ekologiya masalalarida professional javob ber."
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


def check_username(request):
    username = request.GET.get('username', None)
    if not username:
        return JsonResponse({'is_taken': False})
    
    exists = Users.objects.filter(username__iexact=username).exclude(pk=request.user.pk).exists()
    
    return JsonResponse({'is_taken': exists})


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
    
    