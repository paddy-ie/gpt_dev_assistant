import os

project_files = {
    "manage.py": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradesmean.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()""",
    "tradesmean___init__.py": """""",
    "tradesmean_settings.py": """import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-secure-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'billing',
    'addons',
    'voice',
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

ROOT_URLCONF = 'tradesmean.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'tradesmean.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'""",
    "tradesmean_urls.py": """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('billing/', include('billing.urls')),
    path('addons/', include('addons.urls')),
    path('voice/', include('voice.urls')),
]""",
    "tradesmean_wsgi.py": """import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradesmean.settings')
application = get_wsgi_application()""",
    "accounts___init__.py": """""",
    "accounts_models.py": """from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add more profile fields as needed

    def __str__(self):
        return self.user.username""",
    "accounts_views.py": """from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})""",
    "accounts_urls.py": """from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
]""",
    "billing___init__.py": """""",
    "billing_models.py": """from django.db import models
from django.contrib.auth.models import User

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice #{self.id} for {self.user.username}"""",
    "billing_views.py": """from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Invoice

@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(user=request.user)
    return render(request, 'billing/invoice_list.html', {'invoices': invoices})""",
    "billing_urls.py": """from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.invoice_list, name='invoice_list'),
]""",
    "addons___init__.py": """""",
    "addons_models.py": """from django.db import models
from django.contrib.auth.models import User

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_billing_addon = models.BooleanField(default=False)
    # Add more addon flags as needed

    def __str__(self):
        return f"Subscription for {self.user.username}"""",
    "addons_views.py": """from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Subscription

@login_required
def addons_dashboard(request):
    subscription, created = Subscription.objects.get_or_create(user=request.user)
    return render(request, 'addons/dashboard.html', {'subscription': subscription})""",
    "addons_urls.py": """from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.addons_dashboard, name='addons_dashboard'),
]""",
    "voice___init__.py": """""",
    "voice_views.py": """from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def voice_upload(request):
    if request.method == 'POST':
        # Placeholder for voice-to-text integration
        transcript = "Transcribed text would go here."
        return render(request, 'voice/result.html', {'transcript': transcript})
    return render(request, 'voice/upload.html')""",
    "voice_urls.py": """from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.voice_upload, name='voice_upload'),
]""",
    "templates_accounts_signup.html": """<!DOCTYPE html>
<html>
<head>
    <title>Sign Up</title>
</head>
<body>
    <h2>Sign Up</h2>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Sign up</button>
    </form>
</body>
</html>""",
    "templates_billing_invoice_list.html": """<!DOCTYPE html>
<html>
<head>
    <title>Your Invoices</title>
</head>
<body>
    <h2>Your Invoices</h2>
    <ul>
        {% for invoice in invoices %}
            <li>
                {{ invoice.amount }} due {{ invoice.due_date }} - 
                {% if invoice.is_paid %}Paid{% else %}Unpaid{% endif %}
            </li>
        {% endfor %}
    </ul>
</body>
</html>""",
    "templates_addons_dashboard.html": """<!DOCTYPE html>
<html>
<head>
    <title>Addons Dashboard</title>
</head>
<body>
    <h2>Your Addons</h2>
    <p>Billing Addon: {{ subscription.has_billing_addon|yesno:"Enabled,Disabled" }}</p>
</body>
</html>""",
    "templates_voice_upload.html": """<!DOCTYPE html>
<html>
<head>
    <title>Upload Voice</title>
</head>
<body>
    <h2>Upload Voice Note</h2>
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <input type="file" name="audio">
        <button type="submit">Upload</button>
    </form>
</body>
</html>""",
    "templates_voice_result.html": """<!DOCTYPE html>
<html>
<head>
    <title>Voice Result</title>
</head>
<body>
    <h2>Transcript</h2>
    <p>{{ transcript }}</p>
</body>
</html>""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')