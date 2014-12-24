import urllib
import urllib2

from datetime import datetime
from decimal import Decimal

from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.utils.timezone import utc

from atm.models import Balance, Customer, Transaction, DebitStatus

# Create your views here.
def purchase(request):
    try:
        account_number = request.POST['account_number']
        customer = Customer.objects.get(account_number=account_number)
        balance = Balance.objects.get(account_number=customer)
        status = DebitStatus.objects.get(account_number=customer)
        amount = balance.balance
        p_amount = Decimal(10)

        if status.status == 'I':
            return HttpResponseServerError('Your debit card is disabled!')
        elif p_amount > amount:
            return HttpResponseServerError('You don\'t have enough money!')
        else:
            Transaction.objects.create(account_number=customer,
                    amount=p_amount, tran_type='P', time_start=datetime.utcnow().replace(tzinfo=utc)).save()
            balance.balance = amount - p_amount
            balance.save()
            return HttpResponse('success')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

def purchase_page(request):
    return render(request, 'shopping/shopping.html', {'title': 'Shopping'})

def shopping(request):
    if request.method == 'POST' and request.is_ajax():
        if 'fnc' in request.POST:
            if request.POST['fnc'] == 'purchase':
                return purchase(request)
        return HttpResponseServerError()
    else:
        return purchase_page(request)
