from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Invoice

@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(user=request.user)
    return render(request, 'billing/invoice_list.html', {'invoices': invoices})