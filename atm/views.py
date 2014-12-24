import json
import re
import urllib
import urllib2

from datetime import datetime
from decimal import Decimal
from functools import wraps

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext
from django.utils.html import escape
from django.utils.timezone import utc
from django.utils.timezone import localtime

from models import Balance, Customer, PIN, Transaction, ZIPCode, DebitStatus
from mybank.settings import LOCAL_DB

def active_customer(account_number):
    try:
        customer = Customer.objects.get(account_number=account_number)
        if customer is not None and customer.status == 'A':
            return customer
    except:
        return None
    return None

def authenticate(account_number, zipcode, pin):
    try:
        if (re.match(r'\d{12}', account_number) is None
                or re.match(r'\d{5}', zipcode) is None
                or re.match(r'\d{4}', pin) is None):
            return False

        customer = active_customer(account_number)
        if customer is None:
            return False
        if PIN.objects.filter(account_number=customer, pin=pin).count() != 1:
            return False
        if not LOCAL_DB and ZIPCode.objects.filter(zipcode=zipcode,
                zcity=customer.city.upper(),
                zstate=customer.state.upper()).count() == 0:
            return False

        return True
    except:
        return False

def login_required():
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if is_active(request):
                return view(request, *args, **kwargs)
            else:
                return HttpResponseServerError('logout')
        return wrapper
    return decorator

def is_logged(request):
    return 'account_number' in request.session

def is_active(request):
    if (is_logged(request)
            and active_customer(request.session['account_number']) is not None):
        return True
    else:
        return False


# Create your views here.
def login(request):
    if ('account_number' in request.POST
            and 'zipcode' in request.POST
            and 'pin' in request.POST):
        if authenticate(request.POST['account_number'],
                request.POST['zipcode'], request.POST['pin']):
            request.session['account_number'] = request.POST['account_number']
            return HttpResponse('success')
    return HttpResponseServerError()

def logout(request):
    if 'account_number' in request.session:
        del request.session['account_number']
    return HttpResponse('success')

@login_required()
def info(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        balance = Balance.objects.get(account_number=customer)

        response_data = {'name': '%s %s' % (escape(customer.first_name.strip()),
            escape(customer.last_name.strip())),
                'account_number': account_number,
                'balance': str(balance.balance)}
        return HttpResponse(json.dumps(response_data), content_type='application/json')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

@login_required()
def inquiry(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        balance = Balance.objects.get(account_number=customer)
        trans = Transaction.objects.filter(account_number=customer).order_by('time_start').reverse()

        amount = balance.balance
        trans_data = []
        for tran in trans:
            type_string = ''
            if tran.tran_type == 'D':
                type_string = 'Deposit'
                amount_diff = amount - tran.amount
            elif tran.tran_type == 'W':
                type_string = 'Withrawal'
                amount_diff = amount + tran.amount
            elif tran.tran_type == 'X':
                type_string = 'Transfer from %s' % tran.t_account_number.account_number
                amount_diff = amount - tran.amount
            elif tran.tran_type == 'T':
                type_string = 'Transfer to %s' % tran.t_account_number.account_number
                amount_diff = amount + tran.amount
            elif tran.tran_type == 'P':
                type_string = 'Purchase'
                amount_diff = amount + tran.amount
            trans_data.append([
                localtime(tran.time_start).strftime("%Y-%m-%d %H:%M:%S"),
                type_string,
                str(tran.amount),
                str(amount),
                ])
            amount = amount_diff
        trans_data.append(['0: Initial', 'Initial', str(amount), str(amount)])

        response_data = {'name': '%s %s' % (escape(customer.first_name.strip()),
            escape(customer.last_name.strip())),
                'account_number': account_number,
                'balance': str(balance.balance),
                'trans': trans_data}
        return HttpResponse(json.dumps(response_data), content_type='application/json')
    except Exception as e:
        print e
        return HttpResponseServerError()
    return HttpResponseServerError()

@login_required()
def withdrawal(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        balance = Balance.objects.get(account_number=customer)
        amount = balance.balance
        w_amount = Decimal(re.match('\d+(.\d{1,2})?', request.POST['w_amount']).group(0))

        if w_amount > amount:
            return HttpResponseServerError('You don\'t have enough money!')
        elif w_amount == 0:
            return HttpResponseServerError('You can\'t withdraw zero dollar!')
        else:
            Transaction.objects.create(account_number=customer,
                    amount=w_amount, tran_type='W', time_start=datetime.utcnow().replace(tzinfo=utc)).save()
            balance.balance = amount - w_amount
            balance.save()

            response_data = {'balance': str(balance.balance),
                    'w_amount': str(w_amount)}
            return HttpResponse(json.dumps(response_data), content_type='application/json')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

@login_required()
def deposit(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        balance = Balance.objects.get(account_number=customer)
        amount = balance.balance
        d_amount = Decimal(re.match('\d+(.\d{1,2})?', request.POST['d_amount']).group(0))

        if d_amount == 0:
            return HttpResponseServerError('You can\'t deposit zero dollar!')
        elif d_amount + balance.balance > 99999.99:
            return HttpResponseServerError('You deposit too much!')
        else:
            Transaction.objects.create(account_number=customer,
                    amount=d_amount, tran_type='D', time_start=datetime.utcnow().replace(tzinfo=utc)).save()
            balance.balance = amount + d_amount
            balance.save()

            response_data = {'balance': str(balance.balance),
                    'd_amount': str(d_amount)}
            return HttpResponse(json.dumps(response_data), content_type='application/json')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()


@login_required()
def transfer(request):
    try:
        t_acct = active_customer(request.POST['t_acct'])
        t_account_number = t_acct.account_number
    except:
        return HttpResponseServerError('Destination account doesn\'t exist or is inactive!')


    try:
        account_number = request.session['account_number']
        if t_account_number == account_number:
            return HttpResponseServerError('You cannot transfer to your same account!')
        customer = Customer.objects.get(account_number=account_number)

        balance = Balance.objects.get(account_number=customer)
        t_balance = Balance.objects.get(account_number=t_acct)

        amount = balance.balance
        t_amount = Decimal(re.match('\d+(.\d{1,2})?', request.POST['t_amount']).group(0))

        if t_amount > amount:
            return HttpResponseServerError('You don\'t have enough money!')
        elif t_amount == 0:
            return HttpResponseServerError('You can\'t transfer zero dollar!')
        elif t_amount + t_balance.balance > 99999.99:
            return HttpResponseServerError('You transfer too much!')
        else:
            Transaction.objects.create(account_number=customer, t_account_number=t_acct,
                    amount=t_amount, tran_type='T', time_start=datetime.utcnow().replace(tzinfo=utc)).save()
            Transaction.objects.create(account_number=t_acct, t_account_number=customer,
                    amount=t_amount, tran_type='X', time_start=datetime.utcnow().replace(tzinfo=utc)).save()
            balance.balance -= t_amount
            balance.save()
            t_balance.balance += t_amount
            t_balance.save()

            response_data = {'balance': str(balance.balance),
                    't_acct': t_account_number,
                    't_amount': str(t_amount)}
            return HttpResponse(json.dumps(response_data), content_type='application/json')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

@login_required()
def changepin(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        try:
            pin = PIN.objects.get(account_number=customer, pin=request.POST['old_pin'])
        except:
            return HttpResponseServerError('Incorrect old PIN!')

        new_pin = re.match('\d{4}', request.POST['pin']).group(0)
        pin_again = re.match('\d{4}', request.POST['pin_again']).group(0)

        if new_pin != pin_again:
            return HttpResponseServerError('PINs do not match!')

        pin.pin = new_pin
        pin.save()

        return HttpResponse()

    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

@login_required()
def changedebit(request):
    try:
        account_number = request.session['account_number']
        customer = Customer.objects.get(account_number=account_number)
        try:
            debit_status = DebitStatus.objects.get(account_number=customer)
        except:
            return HttpResponseServerError()

        if request.POST['status'] == 'A':
            debit_status.status = 'A'
        else:
            debit_status.status = 'I'
        debit_status.save()

        return HttpResponse('success')
    except:
        return HttpResponseServerError()
    return HttpResponseServerError()

def login_page(request):
    if 'account_number' in request.session:
        del request.session['account_number']
    return render(request, 'atm/login.html', {'title': 'Sing in to ATM'})

def operation_page(request):
    return render(request, 'atm/atm.html', {'title': 'YS ATM'})

def atm(request):
    if request.method == 'POST':
        if 'fnc' in request.POST:
            if request.POST['fnc'] == 'login':
                return login(request)
            elif request.POST['fnc'] == 'logout':
                return logout(request)
            elif request.POST['fnc'] == 'changedebit':
                return changedebit(request)
            elif request.is_ajax():
                if request.POST['fnc'] == 'info':
                    return info(request)
                elif request.POST['fnc'] == 'inquiry':
                    return inquiry(request)
                elif request.POST['fnc'] == 'withdrawal':
                    return withdrawal(request)
                elif request.POST['fnc'] == 'deposit':
                    return deposit(request)
                elif request.POST['fnc'] == 'transfer':
                    return transfer(request)
                elif request.POST['fnc'] == 'changepin':
                    return changepin(request)
        return HttpResponseServerError()

    elif is_logged(request):
        return operation_page(request)

    else:
        return login_page(request)
