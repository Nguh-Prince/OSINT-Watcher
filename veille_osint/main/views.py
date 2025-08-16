from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render, redirect

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

from datetime import datetime
import io
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .forms import *
from .models import *
from .utils import send_report_as_email, generate_report_pdf

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
    context = {
        'scans_count': Scan.objects.count(),
        'alerts_count': Alert.objects.filter(resolved=False).count(),
        'false_alerts_count': FalseAlert.objects.count(),
    }
    return render(request, 'main/dashboard.html', context=context)


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
    if request.method == "POST":
        start_date = request.POST.get("report_start_date")
        end_date = request.POST.get("report_end_date")
        recipients_str = request.POST.get("recipients", "")
        name = request.POST.get("name", "Rapport")

        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        scans = Scan.objects.filter(scan_start_date__date__range=[start_date_obj, end_date_obj])
        alerts = Alert.objects.filter(alert_date__date__range=[start_date_obj, end_date_obj])

        # Create report entry
        report = Report.objects.create(
            report_start_date=start_date_obj,
            report_end_date=end_date_obj,
            name=name
        )
        report.scans.set(scans)
        report.alerts.set(alerts)

        # Generate PDF
        generate_report_pdf(report, scans, alerts)

        # Save recipients
        recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
        for email in recipients:
            ReportRecipients.objects.create(report=report, email=email)

        send_report_as_email(report)  # Call the email sending function

        return redirect("reports")  # redirect to your reports list view

    reports = Report.objects.all().order_by('-report_start_date')
    return render(request, 'main/reports.html', {'reports': reports})

@require_POST
@login_required
def delete_report(request, report_id):
    """
    Handle Alert deletion.
    """
    try:
        report = get_object_or_404(Report, id=report_id)
        if report.file:
            report.file.delete()  
            
        report.delete()
        messages.success(request, _("Rapport supprime avec succes!"))
    except Report.DoesNotExist:
        messages.error(request, _("Le rapport n'existe pas."))

    return redirect('reports')


def notifications(request):
    """
    Render the notifications template.
    """
    return render(request, 'main/notifications.html')

def settings(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", '')
        user.last_name = request.POST.get("last_name", '')
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect("settings")

    return render(request, "main/settings.html", {
        "password_form": PasswordChangeForm(user=request.user),
        "open_password_modal": False
        })

@login_required
def change_password(request):
    password_form = PasswordChangeForm(request.user, request.POST)
    if request.method == "POST":
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect("settings")
        else:
            # Return errors to the settings page and trigger modal
            return render(request, "main/settings.html", {
                "password_form": password_form,
                "open_password_modal": True
            })

    return redirect("settings")

def login_view(request):
    """
    Render the login page template.
    """
    return render(request, 'main/login.html')
