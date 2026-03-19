import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.tasks import send_sms_task  
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

@login_required
def otp_verify_view(request):
    if getattr(request.user, 'is_verified', False):
        return redirect('agro_main')

    if 'otp_code' not in request.session:
        generated_code = str(random.randint(100000, 999999))
        request.session['otp_code'] = generated_code
        request.session.set_expiry(300)  
        
        send_sms_task.delay(request.user.phone, f"EcoLife platformasiga kirish uchun tasdiqlash kodi: {generated_code}. Kodni hech kimga bermang.")

    if request.method == 'POST':
        user_input = request.POST.get('otp')
        correct_code = request.session.get('otp_code')

        if user_input == correct_code:
            user = request.user
            user.is_verified = True
            user.save()
            
            del request.session['otp_code']
            
            messages.success(request, "Tabriklaymiz, hisobingiz tasdiqlandi!")
            return redirect('dashboard')
        else:
            messages.error(request, "Xato kod kiritdingiz. Qaytadan urinib ko'ring.")

    return render(request, 'auth/otp_page.html') 

class ProductListView(LoginRequiredMixin, TemplateView):
    template_name = "business/agroe.html"