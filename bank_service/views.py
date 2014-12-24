import json
import re

from datetime import datetime
from decimal import Decimal
from functools import wraps

from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.http import Http404
from django.shortcuts import render
from django.utils.timezone import utc
from django.utils.timezone import localtime

from atm.models import Balance, Customer, PIN, Transaction, ZIPCode, DebitStatus
from models import CityState

def is_admin(request):
    return 'iamtheadmin' in request.session

# decorators
def login_required():
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if is_admin(request):
                return view(request, *args, **kwargs)
            else:
                return HttpResponseServerError('logout')
        return wrapper
    return decorator

# Create your views here.

def login(request):
    if ('service_account' in request.POST
            and 'password' in request.POST):
        if request.POST['service_account'] == 'admin' and request.POST['password'] == 'iamtheadmin':
            request.session['iamtheadmin'] = True
            return HttpResponse('success')
    return HttpResponseServerError()

def logout(request):
    if 'iamtheadmin' in request.session:
        del request.session['iamtheadmin']
    return HttpResponse('success')

@login_required()
def mgmt(request):
    if 'account_number' in request.POST and 'account_status' in request.POST:
        try:
            customer = Customer.objects.get(account_number=request.POST['account_number'])
        except:
            return HttpResponseServerError('No such account!')
        if request.POST['account_status'] == 'A':
            customer.status = 'A'
        else:
            customer.status = 'I'
        customer.save()
        return HttpResponse('success')
    return HttpResponseServerError()

@login_required()
def new_customer(request):
    DATA = ['firstname', 'lastname', 'addr', 'state', 'city',
            'd_amount', 'account_number', 'pin', 'account_status']
    dt = request.POST
    for f in DATA:
        if f not in dt or dt[f] == '':
            print f
            return HttpResponseServerError()
    if (re.match(r'\d{12}', dt['account_number']) is None
                or re.match(r'\d{4}', dt['pin']) is None
                or re.match(r'\d+(.\d{1,2})?', dt['d_amount']) is None
                or re.match(r'(A|I)', dt['account_status']) is None):
        return HttpResponseServerError()

    if DebitStatus.objects.filter(
            account_number=dt['account_number']).count() > 0:
        return HttpResponseServerError('Account number exists!')

    if CityState.objects.using('sqlite3').filter(
            state=dt['state'].upper(), city=dt['city'].upper()).count() == 0:
        return HttpResponseServerError('State/City not exist!')

    try:
        d_amount = Decimal(dt['d_amount'])
        if d_amount > 99999.99:
            return HttpResponseServerError('Deposit amount too large!')
    except:
        return HttpResponseServerError('Deposit amount error!')

    r_customer = Customer.objects.create(account_number=dt['account_number'],
        status=dt['account_status'], first_name=dt['firstname'],
        last_name=dt['lastname'], address=dt['addr'],
        city=dt['city'], state=dt['state'])
    r_debit_status = DebitStatus.objects.create(
        account_number=r_customer, status='A')
    r_balance = Balance.objects.create(
        account_number=r_customer, balance=d_amount)
    r_pin = PIN.objects.create(
        account_number=r_customer, pin=dt['pin'])

    r_customer.save()
    r_debit_status.save()
    r_balance.save()
    r_pin.save()

    return HttpResponse('success')

def login_page(request):
    if 'iamtheadmin' in request.session:
        del request.session['iamtheadmin']
    return render(request, 'bank_service/login.html', {'title': 'Sing in to Bank Service'})

def operation_page(request):
    return render(request, 'bank_service/bank_service.html', {'title': 'YS Bank Service'})

##
def account_number(request):
    try:
        if request.is_ajax() and is_admin(request):
            account_numbers = DebitStatus.objects.values_list(
                    'account_number', flat=True)
            return HttpResponse(json.dumps(list(account_numbers)),
                    content_type='application/json')
        else:
            raise Http404
    except:
        raise Http404

def state(request):
    try:
        if request.is_ajax() and is_admin(request):
            states = CityState.objects.using(
                    'sqlite3').values_list('state', flat=True).distinct()
            return HttpResponse(json.dumps(list(states)),
                    content_type='application/json')
        else:
            raise Http404
    except:
        raise Http404

def city(request, q1, q2):
    try:
        if request.is_ajax() and is_admin(request):
            cities = None
            if q1 != '':
                states = CityState.objects.using(
                        'sqlite3').filter(state=q1.upper())
                if states.count() != 0:
                    cities = states.filter(
                            city__startswith=q2.upper()).values_list(
                                    'city', flat=True).distinct()[:10]
            if cities is None:
                cities = CityState.objects.using(
                        'sqlite3').filter(
                                city__startswith=q2.upper()).values_list(
                                        'city', flat=True).distinct()[:10]
            return HttpResponse(json.dumps(list(cities)),
                    content_type='application/json')
            raise Http404
        else:
            raise Http404
    except:
        raise Http404
##

def bank_service(request):
    if request.method == 'POST' and request.is_ajax():
        if 'fnc' in request.POST:
            if request.POST['fnc'] == 'login':
                return login(request)
            elif request.POST['fnc'] == 'logout':
                return logout(request)
            elif request.POST['fnc'] == 'new':
                return new_customer(request)
            elif request.POST['fnc'] == 'mgmt':
                return mgmt(request)
        return HttpResponseServerError()

    elif is_admin(request):
        return operation_page(request)

    else:
        return login_page(request)
