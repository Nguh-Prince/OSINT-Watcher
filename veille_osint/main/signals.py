from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.timezone import now
import requests
from .models import Scan, ScanResult, Journal, Alert

@receiver(post_save, sender=Scan)
def fetch_news_for_scan(sender, instance, created, **kwargs):
    if not created or not instance.keywords:
        print("Skipping news fetch: Scan not created or no keywords provided.")
        return  # Skip if not a new Scan or no keywords provided
    
    print("Fetching news for scan:", instance.id)

    keywords = instance.keywords.strip().replace(" ", "+").replace(",", "+")  # Format keywords for URL
    api_key = settings.NEWS_API_KEY
    url = f"https://newsapi.org/v2/everything?q={keywords}&apiKey={api_key}"

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
                details=details,
                date_posted=date_posted
            )
            
            # Step 2: Create Journal entry (extending ScanResult)
            Journal.objects.create(
                id=scan_result.id,  # required for multi-table inheritance
                titre=titre,
                auteur=auteur,
                scan=instance,
                source=source,
                details=details,
                date_posted=date_posted
            )
        
        instance.status = "completed"
        instance.save()

    except requests.RequestException as e:
        print(f"[NewsAPI] Error fetching articles for scan {instance.id}: {e}")

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
    matched = []
    alert_level = None

    for level, keywords in THREAT_KEYWORDS.items():
        for word in keywords:
            if word in content:
                matched.append(word)
                alert_level = level if not alert_level or THREAT_LEVEL[alert_level] < THREAT_LEVEL[level] else alert_level 

    if matched:
        Alert.objects.create(
            result=scan_result,
            severity=alert_level,
            message=f"Mots cles detectees: {', '.join(matched)}"
        )

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

def send_alert_as_email(alert):
    subject = f"Alert: {alert.severity.capitalize()} threat detected"
    message = f"Scan Result ID: {alert.result.id}\nSeverity: {alert.severity}\nMessage: {alert.message}\n source: {alert.result.source}\nDetails: {alert.result.details}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = ['nguhprince1@gmail.com']  # Replace with actual recipient list

    try:
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, recipient_list)
        print(f"Alert email sent for alert {alert.id}")
    except Exception as e:
        print(f"Failed to send alert email for alert {alert.id}: {e}")