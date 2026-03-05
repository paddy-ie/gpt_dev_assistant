from django.db import models
from django.contrib.auth.models import User

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_billing_addon = models.BooleanField(default=False)
    # Add more addon flags as needed

    def __str__(self):
        return f"Subscription for {self.user.username}"