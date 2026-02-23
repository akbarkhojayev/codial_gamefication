from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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
    point_limit = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


class Group(models.Model):
    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    def __str__(self):
        return self.name

class GivePoint(models.Model):
    mentor = models.ForeignKey('Mentor', on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)
    point_type = models.ForeignKey('PointType', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ('mentor', 'student', 'point_type', 'created_at')

    def __str__(self):
        return f"{self.student.user.username} +{self.amount} pts ({self.point_type.name if self.point_type else 'No type'})"

    def clean(self):
        # max point type check
        if self.point_type and self.amount > self.point_type.max_point:
            raise ValidationError(
                f"Amount cannot exceed {self.point_type.max_point} for {self.point_type.name}."
            )

        # mentor available point_limit check
        if self.pk:
            prev_instance = GivePoint.objects.get(pk=self.pk)
            available_points = self.mentor.point_limit + prev_instance.amount
        else:
            available_points = self.mentor.point_limit

        if self.amount > available_points:
            raise ValidationError(
                f"Mentor {self.mentor.user.username} does not have enough point_limit "
                f"(available: {available_points})."
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # rollback old points if update
            if self.pk:
                prev_instance = GivePoint.objects.select_related('student', 'mentor').get(pk=self.pk)
                if prev_instance.student:
                    prev_instance.student.point -= prev_instance.amount
                    prev_instance.student.save()
                if prev_instance.mentor:
                    prev_instance.mentor.point_limit += prev_instance.amount
                    prev_instance.mentor.save()

            super().save(*args, **kwargs)

            # apply new points
            if self.student:
                self.student.point += self.amount
                self.student.save()
            if self.mentor:
                self.mentor.point_limit -= self.amount
                self.mentor.save()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.student:
                self.student.point -= self.amount
                self.student.save()
            if self.mentor:
                self.mentor.point_limit += self.amount
                self.mentor.save()
            super().delete(*args, **kwargs)


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

    def __str__(self):
        return self.title

class Auction(models.Model):
    description = models.TextField(blank=True, null=True)
    data = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return self.description

class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)
    point_cost = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name