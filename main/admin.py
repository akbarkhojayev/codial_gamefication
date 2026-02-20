from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    UserProfile, Course, Mentor, Group,
    Student, PointType, GivePoint,
    Book, New, Auction, Product
)

@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point_limit")
    search_fields = ("user__username",)
    list_filter = ("point_limit",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "mentor", "active", "created_at")
    list_filter = ("active", "course")
    search_fields = ("name", "course__name", "mentor__user__username")
    autocomplete_fields = ("course", "mentor")

class StudentInline(admin.TabularInline):
    model = Student.groups.through
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point", "phone_number", "created_at")
    list_filter = ("groups", "created_at")
    search_fields = ("user__username", "phone_number")
    autocomplete_fields = ("groups",)

@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "max_point")
    search_fields = ("name",)

@admin.register(GivePoint)
class GivePointAdmin(admin.ModelAdmin):
    list_display = (
        "id", "mentor", "student",
        "amount", "point_type",
        "created_at", "date"
    )
    list_filter = ("point_type", "created_at")
    search_fields = (
        "mentor__user__username",
        "student__user__username"
    )
    autocomplete_fields = ("mentor", "student", "point_type")
    readonly_fields = ("created_at",)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "student")
    list_filter = ("status",)
    search_fields = ("title", "author", "student__user__username")
    autocomplete_fields = ("student",)

@admin.register(New)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "created_at")
    search_fields = ("title", "user__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("user",)

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("id", "description", "data", "time")
    list_filter = ("data",)
    search_fields = ("description",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "auction", "amount", "point_cost")
    list_filter = ("auction",)
    search_fields = ("name",)
    autocomplete_fields = ("auction",)