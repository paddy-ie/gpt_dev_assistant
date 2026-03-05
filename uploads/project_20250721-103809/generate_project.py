import os

project_files = {
    "bash": """django-admin startproject tradesmean
cd tradesmean
python manage.py startapp core""",
    "python": """# In core/views.py
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    # Your dashboard logic
    pass""",
    "python": """from django.contrib.auth.models import User
from django.db import models

class Organization(models.Model):
    name = models.CharField(max_length=255)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)""",
    "python": """# models.py
class Organization(models.Model):
    name = models.CharField(max_length=100)

class Trade(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # other fields...""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')