from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_active = models.BooleanField()


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_active = models.BooleanField()


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=50)
    description = models.TextField()
    brand = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField()


class ProductColor(models.Model):
    name = models.CharField(max_length=50)
    color_code = models.TextField()


class ProductSize(models.Model):
    name = models.TextField()
    is_active = models.BooleanField()


class ProductOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="options")
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name="options")
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, related_name="options")
    retail_price = models.DecimalField(max_digits=10, decimal_places=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    status = models.BooleanField(default=True)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='product_images')
    is_primary = models.BooleanField(default=False)


class ProductMaterial(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=122)
    description = models.TextField()

class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts')
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.BooleanField(default=False)
    