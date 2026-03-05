from django.core.management.base import BaseCommand
from customers.models import Customer
from django.utils import timezone
from twilio.rest import Client
import os

class Command(BaseCommand):
    help = 'Send reactivation SMS to inactive customers'

    def handle(self, *args, **kwargs):
        TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')

        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
            self.stderr.write(self.style.ERROR('Twilio credentials are not set in environment variables.'))
            return

        today = timezone.now().date()
        threshold_date = today - timezone.timedelta(days=180)
        inactive_customers = Customer.objects.filter(
            last_active__lt=threshold_date,
            reactivated=False
        )

        if not inactive_customers.exists():
            self.stdout.write(self.style.SUCCESS('No inactive customers to contact.'))
            return

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        for customer in inactive_customers:
            message = f"Hi {customer.name}, we miss you! Come back and enjoy our services."
            try:
                client.messages.create(
                    body=message,
                    from_=TWILIO_FROM_NUMBER,
                    to=customer.phone_number
                )
                self.stdout.write(self.style.SUCCESS(f"Sent SMS to {customer.name} ({customer.phone_number})"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to send SMS to {customer.name}: {e}"))