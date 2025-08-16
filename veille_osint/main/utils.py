import io
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests

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

def get_recommendations_from_ai(alert):
    """
    Call an AI service to get recommendations based on the alert details.
    This is a placeholder function and should be replaced with actual AI service integration.
    """
    # Example API call to an AI service (replace with actual implementation)
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""
                            You are a cybersecurity professional working in an African bacnk. The following was picked up from a site, 
                            provide security recommendations for it {alert.result.details} considering it was for the bank and to be implemented in the bank's system.

                            Also, give the alert's severity level based on the content of the alert and how applicable it is to the bank's system. The output should be in JSON format with the following structure:
                            {{
                                "severity": "low" | "medium" | "high",
                                "recommendations": ["Recommendation 1", "Recommendation 2", ...]
                            }}

                            Please respond in the following language: {settings.LANGUAGE_CODE}
                        """ 
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": settings.GEMINI_API_KEY
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        # recommendations = response.json().get('recommendations', 'No recommendations available.')
        json_response = response.json()

        try:
            ai_answer = json_response['candidates'][0]
            text = ai_answer['content']['parts'][0]['text']
            json_text =  re.sub(f'(\n|```|json)', '', text)
            return json.loads(json_text)

        except (KeyError, IndexError):
            print("Unexpected response format from AI service.")
            return json_response
        
    except requests.RequestException as e:
        print(f"Failed to get recommendations: {e}")
        return "No recommendations available."
    
"""
from main.models import Alert
from main.utils import get_recommendations_from_ai

a = Alert.objects.first()
rec = get_recommendations_from_ai(a)
"""