from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.timezone import now
import requests
from .models import Scan, ScanResult, Journal

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

    except requests.RequestException as e:
        print(f"[NewsAPI] Error fetching articles for scan {instance.id}: {e}")
