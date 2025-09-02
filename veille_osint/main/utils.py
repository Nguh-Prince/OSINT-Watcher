import io
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

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
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"<b>Report from {start_date} to {end_date}</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    # ==========================
    # Scans Table
    # ==========================
    scan_data = [["Name", "Sites", "Number of Results"]]
    for scan in scans:
        sites = ", ".join([site.name for site in scan.sites.all()])
        result_count = scan.results.count()
        scan_data.append([scan.name or "N/A", sites, str(result_count)])

    scan_table = Table(scan_data, hAlign='LEFT')
    scan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(Paragraph("<b>Scans</b>", styles['Heading2']))
    elements.append(scan_table)
    elements.append(Spacer(1, 20))

    # ==========================
    # Alerts Table
    # ==========================
    alert_data = [["Source", "Message", "Severity", "Recommendations"]]
    for alert in alerts:
        source_link = f'<a href="{alert.result.source}">{alert.result.source}</a>' if alert.result.source else "N/A"
        message = alert.message or "N/A"
        severity = alert.severity.capitalize() if alert.severity else "N/A"
        recommendations = alert.recommendations or "N/A"
        alert_data.append([source_link, message, severity, recommendations])

    alert_table = Table(alert_data, hAlign='LEFT', colWidths=[120, 150, 60, 120])
    alert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(Paragraph("<b>Alerts</b>", styles['Heading2']))
    elements.append(alert_table)

    # Build PDF
    doc.build(elements)

    # Save PDF to model
    buffer.seek(0)
    filename = f"report_{start_date}_{end_date}.pdf"
    report.file.save(filename, ContentFile(buffer.read()))
    buffer.close()
    print(f"PDF generated for report {report.id} and saved to {report.file.name}")
    
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

                            These security recommendations should be short and be maximum of 5 and minimum of 2. They should be listed in markdown format and each recommendation should be on a new line. Each recommendation should have the format: 'recommendation: application' e.g. 'Strengthen passwords: change old passwords to stronger ones and validate password strength henceforth'

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