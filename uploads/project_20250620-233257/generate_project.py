import os

project_files = {
    "bash": """django-admin startproject reactivation_bot
cd reactivation_bot
python manage.py startapp customers""",
    "bash": """pip install twilio""",
    "python": """from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    last_active = models.DateField()
    reactivated = models.BooleanField(default=False)

    def __str__(self):
        return self.name""",
    "python": """from django.core.management.base import BaseCommand
from customers.models import Customer
from django.utils import timezone
from twilio.rest import Client

TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_FROM_NUMBER = 'your_twilio_number'

class Command(BaseCommand):
    help = 'Send reactivation SMS to inactive customers'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        inactive_customers = Customer.objects.filter(
            last_active__lt=today.replace(year=today.year-1),  # Inactive > 1 year
            reactivated=False
        )
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        for customer in inactive_customers:
            message = f"Hi {customer.name}, we miss you! Come back and enjoy our services."
            client.messages.create(
                body=message,
                from_=TWILIO_FROM_NUMBER,
                to=customer.phone_number
            )
            self.stdout.write(self.style.SUCCESS(f"Sent SMS to {customer.name}"))""",
    "bash": """python manage.py reactivate_customers""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')