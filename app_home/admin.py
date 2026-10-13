from django.contrib import admin
from app_home.models import (
    Banner,
    TrendingProduct,
    CompanyInformation,
    CompanyInformationContent,
    HomeContent,
)
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'sort_order',
        'is_active',
    ]
    list_filter = ['is_active']
    search_fields = ['title']
    ordering = ['id']
@admin.register(TrendingProduct)
class TrendingProductAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'product',
        'home_content',
        'sort_order',
        'is_active',
    ]
    list_filter = ['is_active']
    ordering = ['sort_order']
class CompanyInformationContentInline(admin.TabularInline):
    model = CompanyInformationContent
    extra = 1
    fields = ['title', 'value', 'sort_order']
    ordering = ['sort_order']
@admin.register(CompanyInformation)
class CompanyInformationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'is_active',
        'home_content',
    ]
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    inlines = [CompanyInformationContentInline]
    ordering = ['id']
@admin.register(CompanyInformationContent)
class CompanyInformationContentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'company_information',
        'title',
        'sort_order',
    ]
    list_filter = ['company_information']
    search_fields = ['title', 'value']
    ordering = ['sort_order']
@admin.register(HomeContent)
class HomeContentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'type',
        'title',
        'sort_order',
        'is_active',
        'banner',
        'discount',
        'category',
    ]
    list_filter = ['type', 'is_active']
    search_fields = ['title']
    ordering = ['sort_order']