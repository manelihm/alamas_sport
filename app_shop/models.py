from django.db import models

class Banner(models.Model):
    title = models.CharField(max_length=122)
    description = models.TextField()
    image = models.ImageField(upload_to='banner')
    button_link = models.CharField(max_length=122)
    button_text = models.CharField(max_length=122)
    sort_order = models.CharField(max_length=122)
    is_active = models.BooleanField()


