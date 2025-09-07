from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.timezone import now
import requests

from .models import *
from .utils import get_recommendations_from_ai

from .ai_model import AlertClassifier

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()


@receiver(post_save, sender=Scan)
def fetch_news_for_scan(sender, instance, created, **kwargs):
    if not created or not instance.keywords:
        print("Skipping news fetch: Scan not created or no keywords provided.")
        return  # Skip if not a new Scan or no keywords provided
    
    print("Fetching news for scan:", instance.id)

    keywords = instance.keywords.strip().replace(" ", "+").replace(",", "+")  # Format keywords for URL
    api_key = settings.NEWS_API_KEY
    url = f"https://newsapi.org/v2/everything?q={keywords}&apiKey={api_key}"

    if instance.schedule and instance.schedule.last_scan:
        instance.scan_start_date = instance.schedule.last_scan.time_run if not instance.scan_start_date else instance.scan_start_date
        instance.scan_end_date = now() if not instance.scan_end_date else instance.scan_end_date
        url += f"&from={instance.scan_start_date.isoformat()}&to={instance.scan_end_date.isoformat()}"  # Filter by last scan time

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        articles = data.get('articles', [])
        print(f"Fetched {len(articles)} articles for scan {instance.id}")

        for article in articles:
            # Extract safe values
            source = article.get('url', 'No URL')
            details = article.get('description', 'No description')
            date_posted = article.get('publishedAt') or now()
            titre = article.get('title', 'No Title')
            auteur = article.get('author', 'Unknown')
            auteur = auteur if auteur else 'Unknown'

            # Convert ISO 8601 string to datetime if necessary
            if isinstance(date_posted, str):
                from dateutil import parser
                date_posted = parser.parse(date_posted)

            # Step 1: Create ScanResult
            scan_result = ScanResult.objects.create(
                scan=instance,
                source=source,
                details=details if details else 'No details available',
                date_posted=date_posted
            )
            
            # Step 2: Create Journal entry (extending ScanResult)
            Journal.objects.create(
                id=scan_result.id,  # required for multi-table inheritance
                titre=titre[:200],
                auteur=auteur[:100],
                scan=instance,
                source=source,
                details=details if details else 'No details available',
                date_posted=date_posted
            )
        
        instance.status = "completed"
        instance.save()

    except requests.RequestException as e:
        print(f"[NewsAPI] Error fetching articles for scan {instance.id}: {e}")

@receiver(post_save, sender=ScanSchedule)
def schedule_scan(sender, instance, created, **kwargs):
    """
    Add or update jobs when a ScanSchedule is saved.
    """
    # Remove any existing jobs for this schedule
    try:
        scheduler.remove_job(f"scan_{instance.id}")
    except:
        pass

    try:
        scheduler.remove_job(f"scan_{instance.id}_repeat")
    except:
        pass

    # One-time first run
    scheduler.add_job(
        instance.create_scan,
        "date",
        run_date=instance.schedule_time,
        id=f"scan_{instance.id}",
        replace_existing=True,
    )

    # Recurring jobs
    if instance.frequency == "hourly":
        trigger_args = {"hours": 1}
    if instance.frequency == "daily":
        trigger_args = {"days": 1}
    elif instance.frequency == "weekly":
        trigger_args = {"weeks": 1}
    elif instance.frequency == "monthly":
        trigger_args = {"days": 30}
    else:
        trigger_args = None

    if trigger_args:
        scheduler.add_job(
            instance.create_scan,
            "interval",
            id=f"scan_{instance.id}_repeat",
            replace_existing=True,
            **trigger_args
        )
    print(f"📅 Scheduled scan {instance.id}")

@receiver(post_delete, sender=ScanSchedule)
def unschedule_scan(sender, instance, **kwargs):
    """
    Remove jobs when a ScanSchedule is deleted.
    """
    for job_id in [f"scan_{instance.id}", f"scan_{instance.id}_repeat"]:
        try:
            scheduler.remove_job(job_id)
            print(f"🗑️ Removed job {job_id}")
        except:
            pass

THREAT_KEYWORDS = {
    'high': ['ransomware', 'breach', 'leak', 'hacked'],
    'medium': ['phishing', 'compromise', 'exposed'],
    'low': ['vulnerability', 'downtime', 'incident']
}

THREAT_LEVEL = {
    'high': 3, 'medium': 2, 'low': 1
}

def check_result_for_alerts(scan_result):
    content = f"{scan_result.details} {getattr(scan_result, 'titre', '')}".lower()
    classifier = AlertClassifier()

    try:
        result = classifier.predict(content)

        matched = []

        for level, keywords in THREAT_KEYWORDS.items():
            for word in keywords:
                if word in content:
                    matched.append(word)
        
        alert_level = result.get('severity', None)
        
        if alert_level.lower() != 'none':
            Alert.objects.create(
                result=scan_result,
                severity=alert_level,
                message=f"Mots detectees: {', '.join(matched)}",
                recommendations=result.get('recommendations', '')
            )
    except Exception as e:
        print(f"Error classifying scan result {scan_result.id}: {e}")
        
@receiver(post_save, sender=ScanResult)
def create_alerts_for_scan_result(sender, instance, created, **kwargs):
    if created:
        print(f"Creating alerts for scan result {instance.id}")
        check_result_for_alerts(instance)
    else:
        print(f"Scan result {instance.id} updated, checking for alerts.")
        check_result_for_alerts(instance)

    

@receiver(post_save, sender=Alert)
def send_alert_email(sender, instance, created, **kwargs):
    if created and instance.severity == 'high':
        print(f"High alert created for scan result {instance.result.id}: {instance.message}")
        send_alert_as_email(instance)
    else:
        print(f"Alert {instance.id} updated, no email sent.")

def send_alert_as_email(alert, recipients=None):
    subject = f"Alert: {alert.severity.capitalize()} threat detected"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [settings.ALERT_TARGET_EMAIL] if not recipients else recipients

    # Plain text fallback
    text_message = (
        f"Scan Result ID: {alert.result.id}\n"
        f"Severity: {alert.severity}\n"
        f"Message: {alert.message}\n"
        f"Source: {alert.result.source}\n"
        f"Details: {alert.result.details}\n"
        f"Recommendations: {alert.recommendations}"
    )

    # HTML version with bold field names
    html_message = f"""
    <html>
      <body>
        <p><h4>Scan Result ID:</h4> {alert.result.id}</p>
        <p><h4>Severity:</h4> {alert.severity}</p>
        <p><h4>Message:</h4> {alert.message}</p>
        <p><h4>Source:</h4> {alert.result.source}</p>
        <p><h4>Details:</h4> {alert.result.details}</p>
        <p><h4>Recommendations:</h4> {alert.recommendations}</p>
      </body>
    </html>
    """

    try:
        email = EmailMultiAlternatives(subject, text_message, from_email, recipient_list)
        email.attach_alternative(html_message, "text/html")
        email.send()
        print(f"✅ Alert email sent for alert {alert.id}")
    except Exception as e:
        print(f"❌ Failed to send alert email for alert {alert.id}: {e}")

@receiver(pre_delete, sender=Report)
def delete_report_file(sender, instance, **kwargs):
    """
    Delete the report file when the Report instance is deleted.
    """
    if instance.file:
        instance.file.delete(save=False)
        print(f"Deleted file for report {instance.id}")
    else:
        print(f"No file to delete for report {instance.id}")