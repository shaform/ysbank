from django.db import models
from atm.models import Customer

# Create your models here.
class CityState(models.Model):
    state = models.CharField(max_length=2,
            db_column='state')
    city = models.CharField(max_length=30,
            db_column='city')

    class Meta:
        db_table = 'city_state'
