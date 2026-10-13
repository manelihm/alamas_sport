from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from app_auth.models import User
from app_users.models import (
    Address,
    Favorite,
    ProductFeedback,
    ProductRequest,
)
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = [
        'id',
        'phone_number',
        'username',
        'role',
        'status',
        'is_active',
        'is_staff',
    ]
    list_filter = [
        'role',
        'status',
        'is_active',
        'is_staff',
    ]
    search_fields = ['phone_number', 'username']
    ordering = ['id']
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'username', 'password')
        }),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'gender',
                'image',
            )
        }),
        ('Permissions', {
            'fields': (
                'role',
                'status',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'username',
                'password1',
                'password2',
            ),
        }),
    )
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'province',
        'city',
        'postal_code',
        'is_default',
        'created_at',
    ]
    list_filter = ['province', 'city', 'is_default']
    search_fields = [
        'user__phone_number',
        'user__username',
        'province',
        'city',
        'postal_code',
        'address',
    ]
    ordering = ['-created_at']
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'product',
        'created_at',
    ]
    search_fields = [
        'user__phone_number',
        'user__username',
        'product__name',
    ]
    ordering = ['-created_at']
@admin.register(ProductFeedback)
class ProductFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'product',
        'rating',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'rating']
    search_fields = [
        'user__phone_number',
        'user__username',
        'product__name',
        'content',
    ]
    ordering = ['-created_at']
@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'title',
        'status',
        'created_at',
        'updated_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'user__phone_number',
        'user__username',
        'title',
        'description',
        'admin_note',
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fields = [
        'user',
        'title',
        'description',
        'status',
        'admin_note',
        'created_at',
        'updated_at',
    ]