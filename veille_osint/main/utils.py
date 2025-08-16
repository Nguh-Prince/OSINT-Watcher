import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage

def send_report_as_email(report):
    print(f"Sending report {report.id} as email.")
    subject = f"Report: {report.name}"
    message = f"Report ID: {report.id}\nTitle: {report.name}\n"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [ r.email for r in report.recipients.all() ]
    try:
        email = EmailMessage(subject, message, from_email, recipient_list)
        if report.file:
            email.attach_file(report.file.path)
        email.send()
        print(f"Report email sent for report {report.id}")
    except Exception as e:
        print(f"Failed to send report email for report {report.id}: {e}")


def generate_report_pdf(report, scans, alerts):
    start_date, end_date = report.report_start_date, report.report_end_date
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Report from {start_date} to {end_date}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Scans")
    y -= 20
    p.setFont("Helvetica", 12)
    for scan in scans:
        p.drawString(50, y, f"- {scan.scan_start_date} | {scan.status}")
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Alerts")
    y -= 20
    p.setFont("Helvetica", 12)
    for alert in alerts:
        p.drawString(50, y, f"- {alert.alert_date} | {alert.message}")
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    buffer.seek(0)

    # Save PDF to model
    report.file.save(f"report_{start_date}_{end_date}.pdf", ContentFile(buffer.read()))
    print(f"PDF generated for report {report.id} and saved to {report.file.name}")
    buffer.close()