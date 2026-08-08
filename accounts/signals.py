from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, CandidateProfile, EmployerProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):

    if created:

        if instance.role == CustomUser.Role.CANDIDATE:
            CandidateProfile.objects.create(user=instance,full_name=instance.username)

        elif instance.role == CustomUser.Role.EMPLOYER:
            EmployerProfile.objects.create(user=instance,company_name=instance.username)  