from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Visitor


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type',
                    'security_number', 'is_verified', 'face_registered', 'created_at')
    list_filter = ('user_type', 'is_verified', 'created_at')
    search_fields = ('username', 'email', 'first_name',
                     'last_name', 'security_number')
    readonly_fields = ('security_number', 'created_at', 'face_preview')

    fieldsets = UserAdmin.fieldsets + (
        ('AFZ Information', {
            'fields': ('user_type', 'security_number', 'phone_number', 'unit', 'face_encoding', 'face_preview', 'is_verified', 'profile_picture')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('AFZ Information', {
            'fields': ('user_type', 'security_number', 'phone_number', 'unit', 'email')
        }),
    )

    def face_registered(self, obj):
        return bool(obj.face_encoding)
    face_registered.boolean = True
    face_registered.short_description = 'Face Registered'

    def face_preview(self, obj):
        if obj.face_encoding:
            return format_html(
                '<div style="background: #e7f3ff; padding: 10px; border-radius: 5px; border: 1px solid #b3d4ff;">'
                '<strong>✅ Face Encoding Registered</strong><br>'
                '<small>Length: {} characters</small>'
                '</div>',
                len(obj.face_encoding)
            )
        return format_html(
            '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeaa7;">'
            '<strong>⚠️ No Face Encoding</strong><br>'
            '<small>Use "Register Face" action below</small>'
            '</div>'
        )
    face_preview.short_description = 'Face Registration Status'

    actions = ['register_faces']

    def register_faces(self, request, queryset):
        # This would typically redirect to a face registration page
        # For now, we'll mark them as needing face registration
        self.message_user(
            request, f"Selected users need face registration. Use the face registration system.")
    register_faces.short_description = "Register faces for selected users"


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
