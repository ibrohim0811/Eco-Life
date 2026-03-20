import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.tasks import send_sms_task  
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, ProductImage
from django.urls import reverse_lazy

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
            return redirect('agro_main')
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
from django.db import transaction

class Addproduct(LoginRequiredMixin, CreateView):
    model = Product
    template_name = "business/agro_add.html"
    fields = ['name', 'count', 'price', 'about'] 
    success_url = reverse_lazy('agro_main')

    def form_valid(self, form):
        user = self.request.user
        
        # 1. Obuna va Limitni tekshirish (Xavfsiz usulda)
        try:
            sub_text = user.subscription.badge_text
        except AttributeError:
            messages.error(self.request, "Sizda faol obuna topilmadi!")
            return redirect('agro_main')

        bugun = timezone.now().date()
        user_limit = Product.objects.filter(user=user, created_at__date=bugun).count()
        
        limit_map = {"FREE": 1, "GO": 3, "PRO": 5, "ULTIMA": 7}
        current_max = limit_map.get(sub_text, 0)

        if user_limit >= current_max:
            messages.error(self.request, f"Bugungi limitingiz ({current_max} ta) tugadi!")
            return redirect('agro_main')

        # 2. Narxni tekshirish
        if form.cleaned_data.get('price') > 10000000:
            form.add_error('price', "Narx haddan tashqari baland!")
            return self.form_invalid(form)

        # 3. Tranzaksiya bilan saqlash (Agar rasm yuklanmasa, mahsulot ham saqlanmaydi)
        try:
            with transaction.atomic():
                form.instance.user = user
                # Avval mahsulotni bazaga saqlaymiz (ID olish uchun)
                self.object = form.save() 
                
                # Endi rasmlarni saqlaymiz
                images = self.request.FILES.getlist('images')
                if images:
                    for img in images:
                        ProductImage.objects.create(product=self.object, image=img)
                
                messages.success(self.request, "Mahsulot muvaffaqiyatli qo'shildi!")
                return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f"Xatolik yuz berdi: {str(e)}")
            return self.form_invalid(form)

import json
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def check_image_ai(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            base64_image = data.get('image')
            api_key = os.getenv("GEMINI_AI") 

            # 1-QADAM: Sening kaliting uchun ruxsat berilgan modellarni olish
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            models_resp = requests.get(list_url).json()
            
            # Rasm tahlil qila oladigan modelni topamiz
            target_model = None
            if "models" in models_resp:
                for m in models_resp["models"]:
                    # generateContent funksiyasi bor modelni qidiramiz
                    if "generateContent" in m["supportedGenerationMethods"]:
                        target_model = m["name"] # Masalan: "models/gemini-1.5-flash-latest"
                        break
            
            if not target_model:
                target_model = "models/gemini-1.5-flash" # Default variant

            # 2-QADAM: Topilgan model bilan tahlil qilish
            url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Bu rasmda qishloq xo'jaligi mahsuloti bormi? Faqat JSON: {'is_valid': bool, 'description': str, 'reason': str}"},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
                    ]
                }]
            }

            response = requests.post(url, json=payload)
            res_json = response.json()

            if "error" in res_json:
                return JsonResponse({"is_valid": False, "reason": f"Model: {target_model}. Xato: {res_json['error']['message']}"})

            ai_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # JSONni tozalash
            if "```" in ai_text:
                ai_text = ai_text.split("```")[1].replace("json", "").strip()

            return JsonResponse(json.loads(ai_text))

        except Exception as e:
            return JsonResponse({"is_valid": False, "reason": f"Tizim xatosi: {str(e)}"})