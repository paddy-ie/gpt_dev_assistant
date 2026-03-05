from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Subscription

@login_required
def addons_dashboard(request):
    subscription, created = Subscription.objects.get_or_create(user=request.user)
    return render(request, 'addons/dashboard.html', {'subscription': subscription})