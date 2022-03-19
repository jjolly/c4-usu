from django.db import models

# Create your models here.
class Win(models.Model):
    winner = models.IntegerField(default=0)
