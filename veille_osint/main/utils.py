from django.conf import settings
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