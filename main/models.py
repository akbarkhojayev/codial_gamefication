from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F
from django.db import transaction

class UserProfile(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Course(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.name

class Mentor(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='mentors/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    point_limit = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username

class Group(models.Model):
    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    icon = models.CharField(blank=True, null=True)
    color = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    lesson_days = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({self.course.name})"

class Student(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='students/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    point = models.PositiveIntegerField(default=0)
    groups = models.ManyToManyField(Group, blank=True)

    birth_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class PointType(models.Model):
    name = models.CharField(max_length=200, unique=True)
    max_point = models.PositiveIntegerField(default=0)
    is_manual = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class GivePoint(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    point_type = models.ForeignKey(PointType, on_delete=models.PROTECT)
    amount = models.PositiveIntegerField(default=0)

    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'group', 'point_type', 'date'],
                name='uniq_givepoint_student_group_type_date'
            )
        ]

    def clean(self):
        if self.amount > self.point_type.max_point:
            raise ValidationError(
                f"Amount cannot exceed {self.point_type.max_point} for {self.point_type.name}."
            )
        if not self.student.groups.filter(pk=self.group_id).exists():
            raise ValidationError("Student is not in this group.")

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            old_amount = 0
            if self.pk:
                old_amount = GivePoint.objects.select_for_update().get(pk=self.pk).amount

            delta = self.amount - old_amount

            mentor = Mentor.objects.select_for_update().get(pk=self.mentor_id)
            if delta > mentor.point_limit:
                raise ValidationError(f"Not enough point_limit (available: {mentor.point_limit}).")

            super().save(*args, **kwargs)

            Student.objects.filter(pk=self.student_id).update(point=F('point') + delta)
            Mentor.objects.filter(pk=self.mentor_id).update(point_limit=F('point_limit') - delta)


class Book(models.Model):

    BOOK_STATUS_CHOICES = (
    ("O'qiyapman", "O'qiyapman"),
    ("Tugatim", "Tugatim"),
    )

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    book_photo = models.ImageField(upload_to='books/', blank=True, null=True)
    status = models.CharField(max_length=20,choices=BOOK_STATUS_CHOICES, default="O'qiyapman")

    student = models.ForeignKey('Student', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class New(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    pin = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Auction(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    data = models.DateField()
    time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.description

class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='products')
    amount = models.PositiveIntegerField(default=0)
    point_cost = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
