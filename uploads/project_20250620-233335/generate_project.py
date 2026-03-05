import os

project_files = {
    "requirements.txt": """Django>=4.2
twilio>=8.0""",
    "manage.py": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reactivation_bot.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()""",
    "reactivation_bot/__init__.py": """""",
    "reactivation_bot/settings.py": """import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-secure-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'customers',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reactivation_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'reactivation_bot.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'""",
    "reactivation_bot/urls.py": """from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]""",
    "reactivation_bot/wsgi.py": """import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reactivation_bot.settings')

application = get_wsgi_application()""",
    "customers/__init__.py": """""",
    "customers/admin.py": """from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'last_active', 'reactivated')
    search_fields = ('name', 'phone_number')""",
    "customers/apps.py": """from django.apps import AppConfig

class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'""",
    "customers/models.py": """from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    last_active = models.DateField()
    reactivated = models.BooleanField(default=False)

    def __str__(self):
        return self.name""",
    "customers/management/__init__.py": """""",
    "customers/management/commands/__init__.py": """""",
    "customers/management/commands/reactivate_customers.py": """from django.core.management.base import BaseCommand
from customers.models import Customer
from django.utils import timezone
from twilio.rest import Client
import os

class Command(BaseCommand):
    help = 'Send reactivation SMS to inactive customers'

    def handle(self, *args, **kwargs):
        # Use environment variables for credentials
        TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')

        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
            self.stderr.write(self.style.ERROR('Twilio credentials are not set in environment variables.'))
            return

        today = timezone.now().date()
        # Example: customers inactive for over 180 days
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
                self.stderr.write(self.style.ERROR(f"Failed to send SMS to {customer.name}: {e}"))""",
    "customers/migrations/__init__.py": """""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')