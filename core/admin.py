from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FacultyProfile, StudentProfile, LearningContent, TestProgress, Sentence, TestProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'staff_id', 'roll_number')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'staff_id', 'roll_number'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FacultyProfile)
admin.site.register(StudentProfile)
admin.site.register(LearningContent)
admin.site.register(TestProgress)
admin.site.register(Sentence)
admin.site.register(TestProfile)