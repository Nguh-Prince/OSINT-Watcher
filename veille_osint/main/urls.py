from django.urls import path

from .views import *

urlpatterns = [
    path('blank/', blank_page, name='blank_page'),
    path('dashboard/', dashboard, name='dashboard'), 
    path('scans/', scans, name='scans'),
    path('alerts/', alerts, name='alerts'), 
    path('reports/', reports, name='reports'),
    path('notifications/', notifications, name='notifications'),
    path('settings/', settings, name='settings'),
    path('login/', login_view, name='login'),  
]