import os

project_files = {
    "plaintext": """tradesai/
├── manage.py
├── tradesai/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── quotes/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── templates/
│       └── quotes/
│           └── quote_form.html
├── requirements.txt
├── .env""",
    "python": """from django.db import models

class QuoteRequest(models.Model):
    job_description = models.TextField()
    generated_quote = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote on {self.created_at:%Y-%m-%d} - {self.job_description[:30]}"""",
    "python": """from django import forms

class QuoteRequestForm(forms.Form):
    job_description = forms.CharField(
        label="Job Description",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the job...'}),
        max_length=1000,
    )""",
    "python": """import os
import openai
from django.conf import settings
from django.shortcuts import render
from .forms import QuoteRequestForm
from .models import QuoteRequest

def generate_quote_with_openai(description):
    openai.api_key = settings.OPENAI_API_KEY
    prompt = (
        f"Write a professional job quote for the following job description in Ireland. "
        f"Be concise, clear, and include estimated cost, timeline, and terms.\n\n"
        f"Job Description: {description}\n\nQuote:"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()

def quote_request_view(request):
    quote = None
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['job_description']
            quote = generate_quote_with_openai(description)
            # Save to DB (optional)
            QuoteRequest.objects.create(
                job_description=description,
                generated_quote=quote
            )
    else:
        form = QuoteRequestForm()
    return render(request, 'quotes/quote_form.html', {'form': form, 'quote': quote})""",
    "html": """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TradesAI - Generate Job Quote</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Simple mobile-friendly CSS -->
    <link rel="stylesheet" href="{% static 'quotes/style.css' %}">
    <style>
        body { font-family: sans-serif; margin: 2em; background: #f9f9f9; }
        .container { max-width: 500px; margin: auto; background: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 2px 8px #ddd; }
        textarea, input[type=submit] { width: 100%; }
        .quote { background: #e6f2ff; padding: 1em; border-radius: 6px; margin-top: 1em; }
        @media (max-width: 600px) { .container { padding: 1em; } }
    </style>
</head>
<body>
<div class="container">
    <h1>TradesAI - Generate Job Quote</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <input type="submit" value="Generate Quote">
    </form>
    {% if quote %}
        <div class="quote">
            <h3>Generated Quote:</h3>
            <pre>{{ quote }}</pre>
        </div>
    {% endif %}
</div>
</body>
</html>""",
    "output.txt": """Django>=4.2
openai
python-dotenv""",
    "output.txt": """OPENAI_API_KEY=sk-...""",
    "python": """import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')""",
    "output.txt": """.env
__pycache__/
db.sqlite3
/static/""",
    "python": """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quotes.urls')),
]""",
    "python": """from django.urls import path
from .views import quote_request_view

urlpatterns = [
    path('', quote_request_view, name='quote_request'),
]""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')