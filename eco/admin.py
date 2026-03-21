from django.contrib import admin
from .models import Banner, BannerImage, Event

admin.site.register(BannerImage)
admin.site.register(Banner)
admin.site.register(Event)
