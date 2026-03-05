import os

project_files = {
    "python": """# models.py
class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_billing_addon = models.BooleanField(default=False)
    # add other addons as needed

# views.py
def billing_view(request):
    if not request.user.subscription.has_billing_addon:
        return HttpResponseForbidden("Addon not enabled.")
    # normal billing logic here""",
    "python": """class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)""",
    "python": """# views.py
def upload_audio(request):
    if request.method == 'POST':
        audio_file = request.FILES['audio']
        # send to speech-to-text API, get transcript
        # save transcript to DB""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')