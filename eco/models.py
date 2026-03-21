from django.db import models

class BaseCreatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Banner(BaseCreatedModel):
    class ThemeChoices(models.TextChoices):
        SPRING = "bahor", "Bahor"
        SUMMER = "yoz", "Yoz"
        WINTER = "qish", "Qish"
        AUTUMN = "kuz", "Kuz" 
        
    title = models.CharField(max_length=120, blank=True)
    theme = models.CharField(max_length=10, choices=ThemeChoices.choices, default=ThemeChoices.SPRING)
    link_url = models.CharField(max_length=255, blank=True)  
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0) 
    lifetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Banner"
        verbose_name_plural = "Bannerlar"
        
    def __str__(self):
        return self.title or f"Banner {self.id}"

class BannerImage(BaseCreatedModel):
    banner = models.ForeignKey(Banner, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="banners/") 
    alt_text = models.CharField(max_length=100, blank=True) 

    class Meta:
        verbose_name = "Banner rasmi"
        verbose_name_plural = "Banner rasmlari"
    
    
class Event(BaseCreatedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField() # Tadbir boshlanishi
    end_date = models.DateTimeField()   # Tadbir tugashi (Countdown shu vaqtgacha ishlaydi)
    
    event_type = models.CharField(max_length=50, choices=[
        ('ramadan', 'Ramazon'),
        ('navruz', 'Navro‘z'),
        ('new_year', 'Yangi yil'),
        ('anniversary', 'Ekologiya kuni'),
    ])
    
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="events/")

    def is_running(self):
        from django.utils import timezone
        return self.start_date <= timezone.now() <= self.end_date

    def __str__(self):
        return self.title
    
    
#21.03.2026 anniversary eco life
    
