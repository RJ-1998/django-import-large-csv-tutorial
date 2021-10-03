from django.db import models

# Create your models here.
class Characters(models.Model):
    name = models.CharField(max_length=255,null=True,blank=True)
    height = models.FloatField(null=True, blank=True)
    mass = models.FloatField(null=True, blank=True)
    hair_color = models.CharField(max_length=25,null=True, blank=True)
    skin_color = models.CharField(max_length=25,null=True, blank=True)
    eye_color = models.CharField(max_length=25,null=True, blank=True)
    birth_year = models.CharField(max_length=25,null=True, blank=True)
    gender = models.CharField(max_length=25,null=True, blank=True)

    class Meta:
        verbose_name = "Characters"

    def __str__(self):
        return str(self.name)
