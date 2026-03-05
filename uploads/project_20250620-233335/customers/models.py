from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    last_active = models.DateField()
    reactivated = models.BooleanField(default=False)

    def __str__(self):
        return self.name