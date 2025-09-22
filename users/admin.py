from django.contrib import admin
from .models import User, ArtisanProfile, Profile, ArtisanPortfolio

@admin.register(ArtisanProfile)
class ArtisanProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'fulfillment_rate', 'rejection_rate', 'average_rating', 'is_verified', 'latitude', 'longitude')
    list_filter = ('is_verified', 'user__user_type')
    search_fields = ('user__email',)
    actions = ['update_verification']

    def update_verification(self, request, queryset):
        for profile in queryset:
            profile.update_verification_status()
        self.message_user(request, "Verification status updated.")
    update_verification.short_description = "Update verification status for selected profiles"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'user_type', 'is_active', 'image')  
    list_filter = ('user_type',)
    search_fields = ('email',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No image"
    display_image.short_description = "Profile Image"

    def get_profile_image_url(self, obj):
        try:
            return format_html('<a href="{}">{}</a>', obj.profile.image_url, obj.profile.image_url) if obj.profile.image_url else "No image URL"
        except Profile.DoesNotExist:
            return "No profile"
    get_profile_image_url.short_description = "Profile Image URL"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'image')  
    search_fields = ('user__email',)

@admin.register(ArtisanPortfolio)
class ArtisanPortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'artisan_id', 'created_at')
    search_fields = ('artisan__email', 'title')
