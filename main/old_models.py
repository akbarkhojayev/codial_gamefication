from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Course(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    point_limit = models.PositiveIntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Mentor'
        verbose_name_plural = 'Mentors'


class Group(models.Model):
    name = models.CharField(max_length=100)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    birth_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='students/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    point = models.PositiveIntegerField(default=0)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name} ({self.group})"
        return f"Unknown User ({self.group})"

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'


class PointType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_point = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class GivePoint(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.PositiveIntegerField()
    point_type = models.ForeignKey(PointType, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} {self.amount} {self.point_type}"

    def clean(self):
        """
        Custom validation:
        1. `amount` should not exceed `PointType.max_point`.
        2. Mentor must have enough point_limit to give.
        """
        if self.point_type and self.amount > self.point_type.max_point:
            raise ValidationError(
                f"Amount cannot exceed the max point of {self.point_type.max_point} for {self.point_type.name}.")

        if self.mentor and self.mentor.point_limit < self.amount:
            raise ValidationError(
                f"Mentor {self.mentor.user.username} does not have enough point_limit (available: {self.mentor.point_limit}).")

    # def save(self, *args, **kwargs):
    #     self.clean()
    #
    #     # Handle updating old data if this is an update
    #     if self.pk:
    #         prev_instance = GivePoint.objects.get(pk=self.pk)
    #         prev_student = prev_instance.student
    #         prev_mentor = prev_instance.mentor
    #         prev_amount = prev_instance.amount
    #
    #         # Revert previous points
    #         if prev_student:
    #             prev_student.point -= prev_amount
    #             prev_student.save()
    #
    #         if prev_mentor:
    #             prev_mentor.point_limit += prev_amount
    #             prev_mentor.save()
    #
    #     # Save new instance
    #     super().save(*args, **kwargs)
    #
    #     # Update student points
    #     if self.student:
    #         self.student.point += self.amount
    #         self.student.save()
    #
    #     # Update mentor point limit
    #     if self.mentor:
    #         self.mentor.point_limit -= self.amount
    #         self.mentor.save()

    def save(self, *args, **kwargs):
        if self.pk:
            prev_instance = GivePoint.objects.select_related('student', 'mentor').get(pk=self.pk)


            if prev_instance.student:
                self.student.point -= prev_instance.amount
                self.student.save()

            if prev_instance.mentor:
                self.mentor.point_limit += prev_instance.amount
                self.mentor.save()

        super().save(*args, **kwargs)

        if self.student:
            self.student.point += self.amount
            self.student.save()

        if self.mentor:
            self.mentor.point_limit -= self.amount
            self.mentor.save()

    def delete(self,*args,**kwargs):

        if self.student:
            self.student.point-=self.amount
            self.student.save()
        if self.mentor:
            self.mentor.point_limit+=self.amount
            self.mentor.save()

        super().delete(*args,**kwargs)


class New(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(default=now)
    image = models.ImageField(upload_to='news/', null=True, blank=True)
    seminary = models.BooleanField(default=False)
    point=models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class NewsReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(New, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.news.title} - {'Read' if self.is_read else 'Unread'}"


