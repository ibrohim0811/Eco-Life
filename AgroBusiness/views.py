import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.tasks import send_sms_task  
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, ProductImage

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

    return render(request, 'business/agroe.html') 


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "business/agro_main.html"
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = Product.objects.filter(is_active=True).order_by('-created_at').all()

        return context
    
    def get_queryset(self):
        
        data = super().get_queryset()
        search = self.request.GET.get('search')
        if search is None:
            products = Product.objects.all()
            return products 
        else:
            data = Product.objects.filter(name__icontains=search)
            return data
    
    
from django.utils import timezone

class Addproduct(LoginRequiredMixin, CreateView):
    model = Product
    fields = ['name', 'count', 'price', 'images', 'about']
    success_url = 'agro_main'
    
    def form_valid(self, form):
        bugun = timezone.now().date()
        
        user_limit = Product.objects.filter(user=self.request.user, created_at__date=bugun).count()
        
        if self.request.user.subscription.badge_text == "FREE" and user_limit >= 1:
            messages.error(self.request, "Bugungi limitingiz tugadi !")
            return redirect('agro_main')
        elif self.request.user.subscription.badge_text == "GO" and user_limit >= 3:
            messages.error(self.request, "Bugungi limitingiz tugadi !")
            return redirect('agro_main')
        elif self.request.user.subscription.badge_text == "PRO" and user_limit >= 5:
            messages.error(self.request, "Bugungi limitingiz tugadi !")
            return redirect('agro_main')
        elif self.request.user.subscription.badge_text == "ULTIMA" and user_limit >= 7:
            messages.error(self.request, "Bugungi limitingiz tugadi !")
            return redirect('agro_main')
            
        
        
        product = form.save(commit=False)
        name = form.cleaned_data.get('name')
        count = form.cleaned_data.get('count')
        price = form.cleaned_data.get('price')
        images = self.request.FILES.getlist('images')
        about = form.cleaned_data.get('about')
        
        form.instance.user = self.request.user
        
        if price > 10000000:
            form.add_error('price', "Narx haddan tashqari baland!")
            return self.form_invalid(form)
        
        for i in images:
            ProductImage.objects.create(product=product, image=i)
        
        return super().form_valid(form)
    
    

import groq
import os
import json
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()

def check_image_ai(request):
    if request.method == "POST":
        data = json.loads(request.body)
        base64_image = data.get('image')
        
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Bu rasmda qishloq xo'jaligi mahsuloti bormi? Faqat JSON formatda javob ber: {'is_valid': true/false, 'description': 'nomi', 'reason': 'sababi'}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            ai_res = json.loads(completion.choices[0].message.content)
            return JsonResponse(ai_res)
        except Exception as e:
            return JsonResponse({"is_valid": True, "description": "Xatolik bo'ldi"}) 
        
    
    