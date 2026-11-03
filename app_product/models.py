from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver

import os
from io import BytesIO

from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def resize_product_image(uploaded_file):
    target_size = (1200, 1200)

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as original:
            if original.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("unsupported image format.")

            image = ImageOps.exif_transpose(original)
            image.load()

            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGBA")
                background = Image.new("RGBA", image.size, "white")
                background.alpha_composite(image)
                image = background.convert("RGB")
            else:
                image = image.convert("RGB")

            resampling = getattr(Image, "Resampling", Image)
            image.thumbnail(target_size, resampling.LANCZOS)

            canvas = Image.new("RGB", target_size, "white")

            x = (target_size[0] - image.width) // 2
            y = (target_size[1] - image.height) // 2

            canvas.paste(image, (x, y))

            output = BytesIO()

            canvas.save(
                output,
                format="JPEG",
                quality=88,
                optimize=True
            )

            filename = os.path.splitext(
                os.path.basename(uploaded_file.name)
            )[0] + ".jpg"

            return filename, ContentFile(output.getvalue())

    except (OSError, ValueError) as error:
        raise ValueError(
            "Invalid image format or unable to process the image."
        ) from error
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
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
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
    retail_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)]
)

    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)]
)

    wholesale_min_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
)
    

    stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)
    is_active= models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'color', 'size', 'material'],
                name='unique_product_option',
            ),
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.ImageField(upload_to='product_images')
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.image_url and not self.image_url._committed:
            filename, processed_image = resize_product_image(
                self.image_url.file
            )

            self.image_url.save(
                filename,
                processed_image,
                save=False
            )

        super().save(*args, **kwargs)

@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """
    Delete the physical image file when its database record is deleted.
    """
    if instance.image_url:
        instance.image_url.delete(save=False)

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
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assigned_discount_codes"
    )
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
