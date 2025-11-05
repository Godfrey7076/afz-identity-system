from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Visitor


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'user_type', 'security_number', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_verified', 'created_at')
    search_fields = ('username', 'email', 'first_name',
                     'last_name', 'security_number')
    fieldsets = UserAdmin.fieldsets + (
        ('AFZ Information', {
            'fields': ('user_type', 'security_number', 'phone_number', 'unit', 'face_encoding', 'is_verified', 'profile_picture')
        }),
    )
    readonly_fields = ('security_number', 'created_at')


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'visitor_id', 'id_number',
                    'host_member', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'visitor_id', 'id_number', 'phone_number')
    readonly_fields = ('visitor_id', 'created_at')
    fieldsets = (
        ('Visitor Information', {
            'fields': ('full_name', 'id_number', 'phone_number', 'email')
        }),
        ('Visit Details', {
            'fields': ('purpose_of_visit', 'host_member', 'expected_duration', 'time_in', 'time_out')
        }),
        ('Status', {
            'fields': ('status', 'notes', 'created_by')
        }),
    )
