from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class ExtraPlan(models.Model):
    class VersionChoices(models.TextChoices):
        GO = "Go", "go"
        PRO = "Pro", "pro"
        ULTIMA = "Ultima", "ultima"

    class DurationChoices(models.TextChoices):
        WEEKLY = "weekly", "Haftalik"
        MONTHLY = "monthly", "Oylik"  
        YEARLY = "yearly", "Yillik"

    version = models.CharField(max_length=10, choices=VersionChoices.choices)
    duration_type = models.CharField(max_length=10, choices=DurationChoices.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    
    class Meta:
        unique_together = ('version', 'duration_type')

    def __str__(self):
        return f"{self.version} - {self.get_duration_type_display()} ({self.price} UZS)"

class ExtendedPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_info = models.ForeignKey(ExtraPlan, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def activate_subscription(self):
        from accounts.models import Subscription as MainSub
        
        main_sub, _ = MainSub.objects.get_or_create(user=self.user)
        
        durations = {
            ExtraPlan.DurationChoices.WEEKLY: 7,
            ExtraPlan.DurationChoices.MONTHLY: 30,
            ExtraPlan.DurationChoices.YEARLY: 365,
        }
        days = durations.get(self.plan_info.duration_type, 30)
        
        now = timezone.now()
        if main_sub.plan == self.plan_info.version and main_sub.expires_at and main_sub.expires_at > now:
            start_point = main_sub.expires_at
        else:
            start_point = now
        
        main_sub.plan = self.plan_info.version
        main_sub.expires_at = start_point + timedelta(days=days)
        main_sub.is_lifetime = False
        main_sub.save()