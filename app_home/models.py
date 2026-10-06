from django.db import models

class Banner(models.Model):
    title = models.CharField(max_length=122)
    description = models.TextField()
    image = models.ImageField(upload_to='banner')
    button_link = models.CharField(max_length=122)
    button_text = models.CharField(max_length=122)
    sort_order = models.CharField(max_length=122)
    is_active = models.BooleanField()


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