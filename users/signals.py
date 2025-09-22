from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User, Profile
from users.models import ArtisanProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_artisan_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'ARTISAN':
        ArtisanProfile.objects.create(user=instance)