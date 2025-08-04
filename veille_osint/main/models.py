from django.db import models
from django.utils.translation import gettext_lazy as _

class Sites(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(null=True)

    def __str__(self):
        return self.name
    
class ScanSchedule(models.Model):
    name = models.CharField(max_length=100, null=True)
    site = models.ForeignKey(Sites, related_name='scan_schedules', on_delete=models.CASCADE)
    schedule_time = models.DateTimeField()
    frequency = models.CharField(max_length=20, choices=[('daily', _('Daily')), ('weekly', _('Weekly')), ('monthly', _('Monthly'))])
    keywords = models.TextField(null=True, blank=True)

    def __str__(self):
        sites_str = ", ".join([site.name for site in self.sites.all()])
        return f"Scan for {sites_str} on {self.scan_start_date.strftime('%Y-%m-%d %H:%M:%S')}"

    
class Scan(models.Model):
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

