from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render, redirect

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

def quick_scan(request):
    keywords = request.GET.get("keywords")
    results = []

    if keywords:
        # Create a Scan object (no schedule)
        scan = Scan.objects.create(
            name=f"Quick Scan: {keywords}",
            keywords=keywords,
            status="pending"
        )
        results = ScanResult.objects.filter(scan=scan)

        return render(request, "main/quick_scan_results.html", {
            "scan": scan, "results": results
        })

    return render(request, "main/quick_scan_form.html")

@require_POST
def delete_scan(request, scan_id):
    """
    Handle Scan deletion.
    """
    try:
        scan = get_object_or_404(Scan, id=scan_id)
        scan.delete()
        messages.success(request, _("Scan supprime avec succes!"))
    except Scan.DoesNotExist:
        messages.error(request, _("Le scan n'existe pas."))

    return redirect('scans')

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
    alerts = Alert.objects.filter(resolved=False, false_alerts__isnull=True).order_by('-alert_date')
    return render(request, 'main/alerts.html', {'alerts': alerts})

@require_POST
def delete_alert(request, alert_id):
    """
    Handle Alert deletion.
    """
    try:
        alert = get_object_or_404(Alert, id=alert_id)
        alert.delete()
        messages.success(request, _("Alerte supprimee avec succes!"))
    except Alert.DoesNotExist:
        messages.error(request, _("L'alerte n'existe pas."))

    return redirect('alerts')

@require_POST
def mark_false_alert(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)

    # Create the FalseAlert only if it doesn't exist yet
    if not hasattr(alert, 'false_alerts'):
        reason = request.POST.get("reason", "")
        FalseAlert.objects.create(alert=alert, reason=reason)

    return redirect(reverse('alerts'))  # Change to your alerts list view name

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
