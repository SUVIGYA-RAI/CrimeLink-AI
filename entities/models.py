"""
Entities app models.
Defines all entity types: Person, Vehicle, Organization, Location, PhoneRecord.
These entities are the key elements connected with investigation cases.
"""

from django.db import models
from cases.models import Case


class Person(models.Model):
    """Represents a person of interest in an investigation."""

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ]

    full_name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True, help_text="Physical description, background, known associates, etc.")
    # A person can be linked to multiple cases
    related_cases = models.ManyToManyField(Case, blank=True, related_name='persons')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']
        verbose_name_plural = 'Persons'

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    """Represents a vehicle connected to an investigation."""

    VEHICLE_TYPE_CHOICES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('van', 'Van'),
        ('other', 'Other'),
    ]

    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='car')
    model_name = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    # Vehicle owner is a person
    owner = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    # Related case
    related_case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.registration_number} - {self.model_name}"


class Organization(models.Model):
    """Represents an organization connected to an investigation."""

    ORG_TYPE_CHOICES = [
        ('company', 'Company'),
        ('ngo', 'NGO'),
        ('gang', 'Gang'),
        ('political', 'Political Party'),
        ('criminal_network', 'Criminal Network'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    organization_type = models.CharField(max_length=30, choices=ORG_TYPE_CHOICES, default='other')
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    # Organization can be linked to multiple cases
    related_cases = models.ManyToManyField(Case, blank=True, related_name='organizations')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return self.name


class Location(models.Model):
    """Represents a location relevant to an investigation."""

    location_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    # Location can be linked to multiple cases
    related_cases = models.ManyToManyField(Case, blank=True, related_name='locations')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.location_name}, {self.city}"


class PhoneRecord(models.Model):
    """Represents a phone call record related to a case."""

    caller_number = models.CharField(max_length=15)
    receiver_number = models.CharField(max_length=15)
    call_date = models.DateField()
    call_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    # Phone record must be linked to a case
    related_case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='phone_records')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-call_date', '-call_time']

    def __str__(self):
        return f"{self.caller_number} → {self.receiver_number} ({self.call_date})"

    def get_duration_display(self):
        """Convert seconds to minutes and seconds format."""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}m {seconds}s"
