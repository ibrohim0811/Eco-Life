import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class BaseCreatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        



  
class Users(AbstractUser):
    
    class UserRoleChoices(models.TextChoices):
        OPERATOR = 'Operator', 'operator'
        ADMIN = 'Admin', 'admin'
        USER = 'User', 'user'
    
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    about = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=50, unique=True)
    language = models.CharField(max_length=15)
    tg_id = models.BigIntegerField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    image = models.ImageField(upload_to='users/', blank=True, null=True)
    balance = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=10, choices=UserRoleChoices.choices, default=UserRoleChoices.USER)
    points = models.IntegerField(default=0, db_index=True)
    gmail = models.EmailField(default="none@gmail.com", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    @property
    def rank_info(self):
        p = self.points
        if p < 100:
            return {"name": "Nihol", "badge": "🌱", "next": 100}
        elif p < 500:
            return {"name": "Kurtak", "badge": "🌿", "next": 500}
        elif p < 2000:
            return {"name": "Barg", "badge": "🍃", "next": 2000}
        elif p < 5000:
            return {"name": "Daraxt", "badge": "🌳", "next": 5000}
        elif p < 10000:
            return {"name": "O'rmon qo'riqchisi", "badge": "🛡️", "next": 10000}
        elif p < 25000:
            return {"name": "Ekosistema Bunyodkori", "badge": "🏗️", "next": 25000}
        elif p < 50000:
            return {"name": "Sayyora Najotkori", "badge": "🌍", "next": 50000}
        else:
            return {"name": "Yashil Afsona", "badge": "👑", "next": None}

    @property
    def progress_percent(self):
        info = self.rank_info
        if info["next"] is None: return 100
        return min(int((self.points / info["next"]) * 100), 100)
    
    @property
    def global_rank(self):
        return Users.objects.filter(points__gt=self.points).count() + 1
    
    def __str__(self):
        return self.first_name
    


class BalanceHistory(BaseCreatedModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Tushum'
        EXPENSE = 'EXPENSE', 'Chiqim'

    user = models.ForeignKey(
        Users, 
        on_delete=models.CASCADE, 
        related_name='balance_history'
    )
    
    amount = models.BigIntegerField() 
    
    transaction_type = models.CharField(
        max_length=10, 
        choices=TransactionType.choices
    )
    
    description = models.CharField(max_length=255, blank=True, null=True) 
   
    def __str__(self):
        return f"{self.user.first_name} - {self.amount} ({self.transaction_type})"

    class Meta:
        ordering = ['-created_at'] 
       
        
            
class UserActivities(BaseCreatedModel):
    
    class ProccesStatus(models.TextChoices):
        CHECKING = "kutilmoqda", "Kutilmoqda"
        ACCEPTED = "qabul qilindi", "Qabul qilindi"
        REJECTED = "qabul qilinmadi", "Qabul qilinmadi"
        EXISTS = "bajarilgan", "Bajarilgan"
    
    
    status = models.CharField(max_length=20, choices=ProccesStatus.choices, default=ProccesStatus.CHECKING)
    amount = models.IntegerField(default=1500)
    video_file_id = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    user = models.ForeignKey(
        Users, 
        to_field='phone',  
        on_delete=models.CASCADE, 
        related_name='phone_act',
        db_column='user_phone' 
    )

    def __str__(self):
        return self.user.phone
    
    

class Notification(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

    def __str__(self):
        return f"{self.user.username} - {self.message}"
    


class Subscription(models.Model):
    class PlanChoices(models.TextChoices):
        FREE = "Free", "free"
        PRO = "Pro", "pro"
        GO = "Go", 'go'
        ULTIMA = "Ultima", "ultima"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(max_length=10, choices=PlanChoices.choices, default=PlanChoices.FREE)
    expires_at = models.DateTimeField(db_index=True, blank=True, null=True)
    is_lifetime = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self) -> bool:
        if self.plan == self.PlanChoices.FREE:
            return True
        if self.is_lifetime:
            return True
        return bool(self.expires_at and self.expires_at > timezone.now())

    def badge_text(self) -> str:
        if not self.is_active(): 
            return "FREE"
        if self.plan == self.PlanChoices.FREE:
            return "FREE"
        return self.plan.upper()
    
    def check_subscription_status(self):
        if self.plan != self.PlanChoices.FREE and not self.is_lifetime:
            if self.expires_at and self.expires_at < timezone.now():
                self.plan = self.PlanChoices.FREE
                self.save() 
                
    def __str__(self):
        return self.user.username
    
    
class Banner(BaseCreatedModel):
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="banners/")
    link_url = models.CharField(max_length=255, blank=True)  
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0) 

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        
    def __str__(self):
        return self.title
        


class Sale(models.Model):
    ALL = "all"
    SELECTED = "selected"
    RANDOM = "random"
    MODE_CHOICES = [
        (ALL, "All products"),
        (SELECTED, "Selected products"),
        (RANDOM, "Random products"),
    ]

    tag = models.CharField(max_length=30)  
    title = models.CharField(max_length=120, blank=True)

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=ALL)

    percent = models.PositiveIntegerField(default=0)  
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    random_count = models.PositiveIntegerField(default=0) 

    is_active = models.BooleanField(default=True)

    products = models.ManyToManyField("AgroBusiness.Product", blank=True, related_name="sale_events")

    def is_live(self):
        now = timezone.now()
        return self.is_active and self.start_at <= now <= self.end_at
    
    

