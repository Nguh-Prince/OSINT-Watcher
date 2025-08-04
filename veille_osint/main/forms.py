from django import forms
from .models import Scan, ScanSchedule, Sites

class ScanForm(forms.ModelForm):
    # Fields for ScanSchedule
    schedule_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Start Time"
    )
    frequency = forms.ChoiceField(
        choices=ScanSchedule._meta.get_field('frequency').choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Frequency"
    )

    class Meta:
        model = Scan
        fields = ['name', 'sites', 'keywords']
        widgets = {
            'sites': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter scan name'}),
            'keywords': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter keywords (optional)', 'rows': 3}),
        }

    def save(self, commit=True):
        scan = super().save(commit=False)

        # Check if both schedule fields are present
        schedule_time = self.cleaned_data.get('schedule_time')
        frequency = self.cleaned_data.get('frequency')
        keywords = self.cleaned_data.get('keywords')
        
        # If both fields are provided, create a ScanSchedule
        if schedule_time and frequency:
            # Create and assign a ScanSchedule
            schedule = ScanSchedule.objects.create(
                site=self.cleaned_data['sites'][0],  # or allow user to choose
                schedule_time=schedule_time,
                frequency=frequency,
                keywords=keywords if keywords else None
            )
            scan.schedule = schedule

        if commit:
            scan.save()
            self.save_m2m()  # for ManyToMany 'sites'
        return scan
