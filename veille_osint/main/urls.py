from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('blank/', blank_page, name='blank_page'),
    path('dashboard/', login_required(dashboard), name='dashboard'), 
    path('scans/', login_required(scans), name='scans'),
    path('scans/<int:scan_id>', login_required(scan_detail), name='scan-detail'),
    path('scans/<int:scan_id>/delete/', login_required(delete_scan), name='delete_scan'),
    path('quick-scan/', login_required(quick_scan), name='quick_scan'),
    path('alerts/', login_required(alerts), name='alerts'), 
    path('alerts/<int:alert_id>/delete/', login_required(delete_alert), name='delete_alert'),
    path('alerts/<int:alert_id>/mark-false/', login_required(mark_false_alert), name='mark_false_alert'),
    path('reports/', login_required(reports), name='reports'),
    path('reports/<int:report_id>/delete/', delete_report, name='delete_report'),
    path('notifications/', login_required(notifications), name='notifications'),
    path('settings/', login_required(settings), name='settings'),
    path('settings/change-password', login_required(change_password), name='change_password'),
    path('login/', auth_views.LoginView.as_view(template_name='main/login_modified.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
]