from django.db import models

# Create your models here.
# CUSTOMER
#   (ACCT CHAR(12) NOT NULL,
#    STATUS CHAR(1) NOT NULL,
#    FN VARCHAR(35) NOT NULL,
#    LN VARCHAR(35) NOT NULL,
#    ADDR VARCHAR(35) NOT NULL,
#    CITY VARCHAR(35) NOT NULL,
#    STATE CHAR(2) NOT NULL,
#    PKEY(ACCT)
class Customer(models.Model):
    account_number = models.CharField(max_length=12,
            primary_key=True, db_column='acct')
    status = models.CharField(max_length=1, db_column='status')
    first_name = models.CharField(max_length=35, db_column='fn')
    last_name = models.CharField(max_length=35, db_column='ln')
    address = models.CharField(max_length=35, db_column='addr')
    city = models.CharField(max_length=35, db_column='city')
    state = models.CharField(max_length=2, db_column='state')

    class Meta:
        db_table = 'customer'


# PIN
#   (ACCT CHAR(12) NOT NULL,
#    PIN CHAR(4) NOT NULL,
#    PKEY(ACCT)
class PIN(models.Model):
    account_number = models.ForeignKey(Customer,
            primary_key=True, db_column='acct')
    pin = models.CharField(max_length=4, db_column='pin')

    class Meta:
        db_table = 'pin'

# BALANCE
#   (ACCT CHAR(12) NOT NULL,
#    BALANCE DECIMAL(7,2)
#    PKEY(ACCT)
class Balance(models.Model):
    account_number = models.ForeignKey(Customer,
            primary_key=True, db_column='acct')
    balance = models.DecimalField(max_digits=7, decimal_places=2,
            db_column='balance')

    class Meta:
        db_table = 'balance'

# TRANS
#   (ACCT CHAR(12) NOT NULL,
#    TACCT CHAR(12) NOT NULL,
#    AMOUNT DECIMAL(7,2),
#    TRNTYPE CHAR(1),
#    TIME_START TIMESTAMP NOT NULL,
#    TIME_END TIMESTAMP)
#    PKEY(ID)
class Transaction(models.Model):
    account_number = models.ForeignKey(Customer, db_column='acct', related_name='trans')
    t_account_number = models.ForeignKey(Customer, db_column='tacct', null=True, related_name='ttrans')
    amount = models.DecimalField(max_digits=7, decimal_places=2,
            db_column='amount')
    tran_type = models.CharField(max_length=1, db_column='trntype')
    time_start = models.DateTimeField(db_column='time_start')
    time_end = models.DateTimeField(db_column='time_end')

    class Meta:
        db_table = 'trans'


class DebitStatus(models.Model):
    account_number = models.ForeignKey(Customer, db_column='acct')
    status = models.CharField(max_length=1,
            db_column='status')

    class Meta:
        db_table = 'debst'


#ZBANK.ZIPCODE
#   (ZIP CHAR(5),
#    ZCITY CHAR(30),
#    ZSTATE CHAR(2),
#    ZLOCATION CHAR(35)
class ZIPCode(models.Model):
    zipcode = models.CharField(max_length=5, db_column='zip')
    zcity = models.CharField(max_length=30, db_column='zcity')
    zstate = models.CharField(max_length=2, db_column='zstate')
    zlocation = models.CharField(primary_key=True, max_length=35, db_column='zlocation')

    class Meta:
        db_table = '"zbank"."zipcode"'
