from django.db import models
import uuid
from django.conf import settings
from django.http import JsonResponse
import os, json
from django.utils.timezone import now
from django.core.files.storage import default_storage
import datetime

class Brand(models.Model):
    name = models.CharField(max_length=255)
    brand_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    subscription_link = models.CharField(max_length=500, unique=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.subscription_link:
            self.subscription_link = settings.SUBSCRIPTION_LINK()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Campaign(models.Model):
    brand = models.ForeignKey("Brand", on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=255)
    campaign_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Newsletter(models.Model):
    name = models.CharField(max_length=200, null=True)
    newsletter_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    template_content = models.TextField(null=True, blank=True)
    placeholders = models.TextField(null=True, blank=True)  # Will store campaign IDs as comma-separated string
    is_frozen = models.BooleanField(default=False)

    def get_placeholders(self):
        """Returns list of campaign IDs"""
        return self.placeholders.split(',') if self.placeholders else []

    def is_complete(self):
        return bool(self.placeholders and self.placeholders.strip())
    

class Subscriber(models.Model):
    subscriber_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    group = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")], null=True, blank=True)

    def __str__(self):
        return f"{self.subscriber_id} - {self.name}"

class Coupon(models.Model):
    COUPON_TYPES = [
        ("Flat Discount", "Flat Discount"),
        ("Percentage Discount", "Percentage Discount"),
        ("Bundle Offer", "Bundle Offer"),
        ("Buy X Get Y", "Buy X Get Y"),
        ("Custom", "Custom"),
    ]

    DAYS_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
        ("All Days", "All Days"),
    ]

    coupon_id = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(default=now)
    coupon_type = models.CharField(max_length=50, choices=COUPON_TYPES)
    custom_coupon_type = models.CharField(max_length=100, blank=True, null=True)
    flat_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    percentage_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    bill_count = models.IntegerField(default=0)
    campaign = models.ForeignKey(
        "Campaign", 
        on_delete=models.CASCADE, 
        related_name="coupons", 
        null=True,
        blank=True
    )
    coupon_days = models.CharField(max_length=100, default="All Days")
    expiration_date = models.DateField(blank=True, null=True)
    template_file = models.FileField(upload_to="coupons/templates/", blank=True, null=True)
    buy_x = models.IntegerField(blank=True, null=True)
    get_y = models.IntegerField(blank=True, null=True)

    def is_expired(self):
        return self.expiration_date and self.expiration_date < datetime.date.today()

    def is_valid_today(self):
        today = now().strftime("%A")
        return "All Days" in self.coupon_days or today in self.coupon_days

    def __str__(self):
        return self.coupon_id

class TrackingLink(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=12)
    tracking_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # New field

    def __str__(self):
        return f"{self.unique_id} - {self.coupon.coupon_id} - {'Redeemed' if self.redeemed else 'Not Redeemed'}"
