from django.db import models
from django.contrib.auth.models import User
import datetime
import os

def getFileName(request,filename):
    now_time=datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
    new_filename="%s_%s" % (now_time, filename)
    return os.path.join('uploads/',new_filename)

class Category(models.Model):
    name=models.CharField(max_length=150,null=False,blank=False)
    image=models.ImageField(upload_to=getFileName,null=True,blank=True)
    description=models.TextField(max_length=500,null=False,blank=False)
    status=models.BooleanField(default=False,help_text="0=Show, 1=Hidden")
    created_at=models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.name


class Product(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name=models.CharField(max_length=150,null=False,blank=False)
    vendor=models.CharField(max_length=150,null=False,blank=False)
    Product_image=models.ImageField(upload_to=getFileName,null=True,blank=True)
    Quantity=models.IntegerField(null=False,blank=False)
    original_price=models.FloatField(null=False,blank=False)
    Selling_price=models.FloatField(null=False,blank=False)
    description=models.TextField(max_length=500,null=False,blank=False)
    status=models.BooleanField(default=False,help_text="0=Show, 1=Hidden")
    trending=models.BooleanField(default=False,help_text="0=default, 1=Trending")
    created_at=models.DateTimeField(auto_now_add=True)

def __srt__(self):
    return self.name

class Cart(models.Model):
    User=models.ForeignKey(User,on_delete=models.CASCADE)
    Products=models.ForeignKey(Product,on_delete=models.CASCADE)
    Product_qty=models.IntegerField(null=False,blank=False)
    created_at=models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        try:
            return self.Product_qty * float(self.Products.Selling_price)
        except Exception:
            return 0
from django.db import models
from django.contrib.auth.models import User
import datetime
import os

def getFileName(request,filename):
    now_time=datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
    new_filename="%s_%s" % (now_time, filename)
    return os.path.join('uploads/',new_filename)

class Category(models.Model):
    name=models.CharField(max_length=150,null=False,blank=False)
    image=models.ImageField(upload_to=getFileName,null=True,blank=True)
    description=models.TextField(max_length=500,null=False,blank=False)
    status=models.BooleanField(default=False,help_text="0=Show, 1=Hidden")
    created_at=models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.name


class Product(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name=models.CharField(max_length=150,null=False,blank=False)
    vendor=models.CharField(max_length=150,null=False,blank=False)
    Product_image=models.ImageField(upload_to=getFileName,null=True,blank=True)
    Quantity=models.IntegerField(null=False,blank=False)
    original_price=models.FloatField(null=False,blank=False)
    Selling_price=models.FloatField(null=False,blank=False)
    description=models.TextField(max_length=500,null=False,blank=False)
    status=models.BooleanField(default=False,help_text="0=Show, 1=Hidden")
    trending=models.BooleanField(default=False,help_text="0=default, 1=Trending")
    created_at=models.DateTimeField(auto_now_add=True)

def __srt__(self):
    return self.name

class Cart(models.Model):
    User=models.ForeignKey(User,on_delete=models.CASCADE)
    Products=models.ForeignKey(Product,on_delete=models.CASCADE)
    Product_qty=models.IntegerField(null=False,blank=False)
    created_at=models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        try:
            return self.Product_qty * float(self.Products.Selling_price)
        except Exception:
            return 0

@property
def total_cost(self):
    return self.Product_qty*self.Product.Selling_price  

class Favourite(models.Model):
    User=models.ForeignKey(User,on_delete=models.CASCADE)
    Product=models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
