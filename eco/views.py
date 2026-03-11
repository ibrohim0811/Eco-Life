from django.shortcuts import render
from django.views.generic import ListView, TemplateView

class MainListView(TemplateView):
    template_name = 'main.html'
    