from django.db import models
from django.contrib.auth.models import User

#auction form when user wants to list their item/asset for auction auction form page db
class Auctionform(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    itemname=models.CharField(max_length=30)
    itempicture=models.FileField(upload_to="services/", max_length=250, null=True,blank=True, default=None)
    itemcat=models.CharField(max_length=30)
    itembaseprice=models.IntegerField()
    itemdatetoauction=models.DateField()
    itemtimetoauction=models.TimeField()
    itemdescription=models.TextField()
    isactive = models.BooleanField(default=True)

#when user enter a perticular bid to save their id auction id bid amount and winner perticular auction page db
class Auctiontransaction(models.Model):
    auctionid=models.ForeignKey(Auctionform, on_delete=models.CASCADE)
    userid=models.ForeignKey(User, on_delete=models.CASCADE)
    bidamount=models.IntegerField()
    bidtime=models.DateTimeField(auto_now_add=True)
    winner=models.BooleanField(default=False)

# Create your models here.
