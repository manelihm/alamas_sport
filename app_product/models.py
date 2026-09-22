from django.db import models
from django.conf import settings

class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)



class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=50)
    description = models.TextField()
    brand = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)


class ProductColor(models.Model):
    name = models.CharField(max_length=50)
    color_code = models.TextField()


class ProductSize(models.Model):
    name = models.TextField()

class ProductMaterial(models.Model):
    name = models.CharField(max_length=122)
    description = models.TextField(blank=True)


class ProductOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="options")
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name="options")
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, related_name="options")
    material = models.ForeignKey(ProductMaterial ,on_delete=models.CASCADE,related_name="options")
    retail_price = models.DecimalField(max_digits=10, decimal_places=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=0)
    wholesale_min_quantity = models.PositiveIntegerField(default=1)
    stock = models.PositiveIntegerField(default=0)
    is_active= models.BooleanField(default=True)


class ProductImage(models.Model):
    product = models.ForeignKey(ProductOption, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='product_images')
    is_primary = models.BooleanField(default=False)


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]

    product = models.ForeignKey(ProductOption, on_delete=models.CASCADE, related_name='discounts')
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()





class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]

    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=0)
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_discount_codes'
    )
    used_at = models.DateTimeField(null=True, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
   