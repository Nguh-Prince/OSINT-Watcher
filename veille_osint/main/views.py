from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect

from .forms import *
from .models import *

# Create your views here.
def blank_page(request):
    """
    Render a blank page template.
    """
    return render(request, 'main/blank_page.html')

def index(request):
    return redirect('dashboard')

def dashboard(request):
    """
    Render the dashboard template.
    """
    return render(request, 'main/dashboard.html')


def scans(request):
    """
    Handle Scan creation via GET and POST.
    """
    scans = Scan.objects.all()

    if request.method == 'POST':
        form = ScanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Scan cree avec succes!"))
            return redirect('scans')  
    else:
        form = ScanForm()

    return render(request, 'main/scans.html', {'form': form, 'scans': scans})

def scan_detail(request, scan_id):
    """
    Render the detail page for a specific Scan.
    """
    scan = Scan.objects.get(id=scan_id)
    scan_results = ScanResult.objects.filter(scan=scan)

    return render(request, 'main/scan_detail.html', {'scan': scan, 'scan_results': scan_results})


def alerts(request):
    """
    Render the alerts template.
    """
    return render(request, 'main/alerts.html')

def reports(request):
    """
    Render the reports template.
    """
    return render(request, 'main/reports.html')

def notifications(request):
    """
    Render the notifications template.
    """
    return render(request, 'main/notifications.html')

def settings(request):
    """
    Render the settings template.
    """
    return render(request, 'main/settings.html')

def login_view(request):
    """
    Render the login page template.
    """
    return render(request, 'main/login.html')
