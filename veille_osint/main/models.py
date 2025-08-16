from django.db import models
from django.utils.translation import gettext_lazy as _

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()
scheduler.start()

class Sites(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(null=True)

    def __str__(self):
        return self.name
    
class ScanSchedule(models.Model):
    name = models.CharField(max_length=100, null=True)
    sites = models.ManyToManyField(Sites, related_name='scan_schedules')
    schedule_time = models.DateTimeField()
    frequency = models.CharField(max_length=20, choices=[ ('hourly', _('Hourly')), ('daily', _('Daily')), ('weekly', _('Weekly')), ('monthly', _('Monthly')) ] )
    keywords = models.TextField(null=True, blank=True)
    last_scan = models.ForeignKey("Scan", on_delete=models.SET_NULL, null=True)
    next_scan_time = models.DateTimeField("Scan", null=True)

    # def __str__(self):
    #     sites_str = ", ".join([site.name for site in self.sites.all()])
    #     return f"Scan for {sites_str} on {self.scan_start_date.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def create_scan(self):
        """
        Create a new Scan instance based on this schedule.
        """
        print(f"Creating scan for schedule: {self.id} at {datetime.now()}")
        scan = Scan.objects.create(
            name=f"{self.name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            schedule=self,
            scan_start_date=self.schedule_time,
            status='pending',
            keywords=self.keywords
        )
        scan.sites.set(self.sites.all())
        self.last_scan = scan

        delta = None
        if self.frequency == 'hourly':
            delta = timedelta(hours=1)
        if self.frequency == 'daily':
            delta = timedelta(days=1)
        elif self.frequency == 'weekly': 
            delta = timedelta(weeks=1)
        elif self.frequency == 'monthly':
            delta = timedelta(days=30)

        self.next_scan_time = datetime.now() + delta if delta else None

        self.save(update_fields=['last_scan', 'next_scan_time'])
        return scan

    
class Scan(models.Model):
    time_run = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, null=True)
    sites = models.ManyToManyField(Sites, related_name='scans')
    schedule = models.ForeignKey(ScanSchedule, related_name='scans', on_delete=models.SET_NULL, null=True, blank=True)
    scan_start_date = models.DateTimeField(auto_now_add=True)
    scan_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')])
    keywords = models.TextField(null=True, blank=True)

    def __str__(self):
        sites_str = ", ".join([site.name for site in self.sites.all()])
        return f"Scan for {sites_str} on {self.scan_start_date.strftime('%Y-%m-%d %H:%M:%S')}"

    
class ScanResult(models.Model):
    scan = models.ForeignKey(Scan, related_name='results', on_delete=models.CASCADE)
    date_posted = models.DateTimeField()
    source = models.TextField()
    details = models.TextField()

    def __str__(self):
        return f"Result for {self.site.name} - {self.status} on {self.result_date.strftime('%Y-%m-%d %H:%M:%S')}"
    
class ReseauSocial(ScanResult):
    auteur = models.CharField(max_length=100)
    nombre_commentaires = models.IntegerField()
    nombre_partages = models.IntegerField()
    nombre_likes = models.IntegerField()

class Journal(ScanResult):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=100)

class Alert(models.Model):
    result = models.OneToOneField(ScanResult, related_name='alert', on_delete=models.CASCADE)
    alert_date = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    message = models.TextField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    recommendations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Alert on {self.alert_date.strftime('%Y-%m-%d %H:%M:%S')}"

class FalseAlert(models.Model):
    alert = models.OneToOneField(Alert, related_name='false_alerts', on_delete=models.CASCADE)
    date_flagged = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"False Alert for {self.alert.result.name} on {self.date_flagged.strftime('%Y-%m-%d %H:%M:%S')}"
    

class Report(models.Model):
    name = models.CharField(max_length=100, null=True)
    report_start_date = models.DateField()
    report_end_date = models.DateField()
    scans = models.ManyToManyField(Scan, related_name='reports')
    alerts = models.ManyToManyField(Alert, related_name='reports', blank=True)
    file = models.FileField(upload_to='uploads/reports/', null=True, blank=True)

    def __str__(self):
        return f"Report from {self.report_start_date} to {self.report_end_date}"

class ReportRecipients(models.Model):
    report = models.ForeignKey(Report, related_name='recipients', on_delete=models.CASCADE)
    email = models.EmailField()

    def __str__(self):
        return f"Recipient for report {self.report.id} - {self.email}"