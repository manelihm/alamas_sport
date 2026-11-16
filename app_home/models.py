from django.db import models
import os
from io import BytesIO

from PIL import Image, ImageOps
from django.core.files.base import ContentFile

def resize_banner_image(uploaded_file):
    target_size = (1920, 650)

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as original:
            image = ImageOps.exif_transpose(original)
            image.load()

            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA')

            image = ImageOps.fit(
                image,
                target_size,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )

            if image.mode == 'RGBA':
                background = Image.new(
                    'RGB', target_size, 'white'
                )
                background.paste(
                    image,
                    mask=image.getchannel('A')
                )
                image = background
            else:
                image = image.convert('RGB')

            output = BytesIO()

            image.save(
                output,
                format='WEBP',
                quality=85,
                method=6
            )

            filename = (
                os.path.splitext(
                    os.path.basename(uploaded_file.name)
                )[0] + '.webp'
            )

            return filename, ContentFile(output.getvalue())

    except (OSError, ValueError) as error:
        raise ValueError(
            'Invalid banner image.'
        ) from error
class Banner(models.Model):
    title = models.CharField(max_length=122)
    description = models.TextField()
    image = models.ImageField(upload_to='banner')
    button_link = models.CharField(max_length=122)
    button_text = models.CharField(max_length=122)
    sort_order = models.CharField(max_length=122)
    is_active = models.BooleanField()
    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            filename, processed_image = resize_banner_image(
                self.image.file
            )

            self.image.save(
                filename,
                processed_image,
                save=False
            )

        super().save(*args, **kwargs)

class HomeContent(models.Model):
    TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('trending', 'Trending'),
        ('discount', 'Discount'),
        ('category', 'Category'),
        ('company_info', 'Company Info'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    banner = models.ForeignKey(Banner, on_delete=models.SET_NULL, null=True, blank=True, related_name='home_contents')
    discount = models.ForeignKey('app_product.Discount', on_delete=models.SET_NULL, null=True, blank=True, related_name='home_contents')
    category = models.ForeignKey('app_product.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='home_contents')


class TrendingProduct(models.Model):
    product = models.ForeignKey('app_product.Product', on_delete=models.CASCADE, related_name='trending_entries')
    home_content = models.ForeignKey(HomeContent, on_delete=models.SET_NULL, null=True, blank=True, related_name='trending_products')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)


class CompanyInformation(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    logo_url = models.ImageField(upload_to='company/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    home_content = models.ForeignKey(HomeContent, on_delete=models.SET_NULL, null=True, blank=True, related_name='company_informations')


class CompanyInformationContent(models.Model):
    company_information = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    value = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)