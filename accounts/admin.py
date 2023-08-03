from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserAdminCreationForm, UserAdminChangeForm
from .models import User, Profile, EmailActivation


class UserAccountAdmin(BaseUserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm

    list_display = ['pk', 'email', 'full_name', 'admin']
    list_filter = ['admin', 'staff', 'is_active']
    fieldsets = (
        (None, {
            'fields':
                (
                    'first_name', 'last_name', 'email', 'password'
                )
        }),
        ('Permissions', {
            'fields':
                (
                    'admin', 'staff', 'is_active', 'has_password_changed'
                )
        }),
        ('Status', {
            'fields':
                (
                    'is_profile_filled', 'invited_user'
                )
        })
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':
                (
                    'email', 'first_name', 'last_name', 'password1', 'password2'
                )
        }),
    )
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    filter_horizontal = ()


admin.site.register(User, UserAccountAdmin)

admin.site.register(Profile)
admin.site.register(EmailActivation)