from xml.etree.ElementTree import Comment
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Category(models.Model):
    category = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.category}"

class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=64)
    description = models.TextField()
    price = models.DecimalField(max_digits=64, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="listing_category")
    img_url = models.URLField()
    sold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} posted by {self.user}"

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=64, decimal_places=2)
    
    def __str__(self):
        return f"bid on item: {self.listing} by {self.user} with price: {self.price}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return f"{self.comment} - {self.user.username.capitalize()}"

class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    watching = models.BooleanField(default=False)