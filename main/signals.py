# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.db import transaction
# from .models import UserProfile, Student, Mentor
#
#
# @receiver(post_save, sender=UserProfile)
# def create_related_profile(sender, instance, created, **kwargs):
#     if not created:
#         return
#
#     with transaction.atomic():
#         if instance.role == "student":
#             Student.objects.create(user=instance)
#
#         elif instance.role == "teacher":
#             Mentor.objects.create(user=instance)
