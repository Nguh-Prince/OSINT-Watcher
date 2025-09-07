from django.db import migrations, models

def rename_severities(apps, schema_editor):
    Alert = apps.get_model("main", "Alert")
    severity_mapping = {
        "faible": "low",
        "moyen": "medium",
        "moyenne": "medium",
        "élevé": "high",
        "élevée": "high",
    }

    alerts_to_update = Alert.objects.filter(severity__in=severity_mapping.keys())
    print(f"Updating {alerts_to_update.count()} alerts' severities...")
    alerts_to_update.update(
        severity=models.Case(
            *[models.When(severity=old, then=models.Value(new)) for old, new in severity_mapping.items()],
            default=models.F('severity'),
            output_field=models.CharField(),
        )
    )

class Migration(migrations.Migration):

    dependencies = [
        ("main", "0012_alert_recommendations_alter_scanschedule_frequency"),
    ]

    operations = [
        migrations.RunPython(rename_severities),
    ]
