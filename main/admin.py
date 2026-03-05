from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import (
    UserProfile, Course, Mentor, Group,
    Student, PointType, GivePoint,
    Book, New, Auction, Product
)

# -------------------------
# Helpers
# -------------------------
DAY_CHOICES = [
    ("monday", "Dushanba"),
    ("tuesday", "Seshanba"),
    ("wednesday", "Chorshanba"),
    ("thursday", "Payshanba"),
    ("friday", "Juma"),
    ("saturday", "Shanba"),
    ("sunday", "Yakshanba"),
]

DAYKEY_UZ = dict(DAY_CHOICES)

def lesson_days_label(days):
    if not days:
        return "-"
    return ", ".join(DAYKEY_UZ.get(d, d) for d in days)


def badge(text, kind="secondary"):
    """
    kind: primary|secondary|success|danger|warning|info|dark
    Jazzmin Bootstrap badge classlariga mos.
    """
    return format_html('<span class="badge badge-{}">{}</span>', kind, text)


# -------------------------
# Custom form for Group.lesson_days (JSONField)
# -------------------------
class GroupAdminForm(forms.ModelForm):
    lesson_days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Group
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # instance bor bo‘lsa, JSONField ichidagi listni formga joylaymiz
        if self.instance and getattr(self.instance, "lesson_days", None):
            self.initial["lesson_days"] = self.instance.lesson_days

    def clean_lesson_days(self):
        # har doim list bo‘lib saqlansin
        return self.cleaned_data.get("lesson_days", [])


# -------------------------
# UserProfile
# -------------------------
@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ("username", "email", "role_badge", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )

    def role_badge(self, obj):
        color = {
            "admin": "danger",
            "teacher": "info",
            "student": "success",
        }.get(obj.role, "secondary")
        return badge(obj.get_role_display(), color)
    role_badge.short_description = "Role"


# -------------------------
# Course
# -------------------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# -------------------------
# Mentor
# -------------------------
@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point_limit")
    search_fields = ("user__username", "user__email")
    list_filter = ("point_limit",)
    autocomplete_fields = ("user",)


# -------------------------
# Group -> Student Inline
# -------------------------
class GroupStudentInline(admin.TabularInline):
    model = Student.groups.through
    extra = 1
    verbose_name = "Student"
    verbose_name_plural = "Students"
    autocomplete_fields = ("student",) if hasattr(Student.groups.through, "student") else ()


# -------------------------
# Group
# -------------------------
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm

    list_display = ("id", "name", "course", "mentor", "active_badge", "lesson_days_view", "created_at")
    list_filter = ("active", "course", "mentor")
    search_fields = ("name", "course__name", "mentor__user__username", "mentor__user__email")
    autocomplete_fields = ("course", "mentor")
    ordering = ("-created_at",)
    inlines = (GroupStudentInline,)

    # Jazzmin: form sahifasini chiroyli bo‘lib bo‘lib chiqarish
    fieldsets = (
        ("Asosiy ma'lumot", {"fields": ("name", "course", "mentor", "active")}),
        ("Dars jadvali", {"fields": ("lesson_days",)}),
    )

    def lesson_days_view(self, obj):
        return lesson_days_label(getattr(obj, "lesson_days", None))
    lesson_days_view.short_description = "Dars kunlari"

    def active_badge(self, obj):
        return badge("Active" if obj.active else "Inactive", "success" if obj.active else "secondary")
    active_badge.short_description = "Status"


# -------------------------
# Student
# -------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "point", "phone_number", "created_at")
    list_filter = ("groups", "created_at")
    search_fields = ("user__username", "user__email", "phone_number", "first_name", "last_name")
    autocomplete_fields = ("user", "groups")
    ordering = ("-created_at",)

    fieldsets = (
        ("Asosiy", {"fields": ("user", "groups", "point")}),
        ("Profil", {"fields": ("first_name", "last_name", "image", "bio")}),
        ("Kontakt", {"fields": ("phone_number", "birth_date")}),
    )

    def full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name or "-"
    full_name.short_description = "F.I.SH"


# -------------------------
# PointType
# -------------------------
@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "max_point", "manual_badge")
    list_filter = ("is_manual",)
    search_fields = ("name",)
    ordering = ("id",)

    def manual_badge(self, obj):
        # is_manual=True => input (imtihon/vazifa), False => chip (qatnashdi, vaqtida...)
        return badge("Input" if obj.is_manual else "Chip", "warning" if obj.is_manual else "info")
    manual_badge.short_description = "UI turi"


# -------------------------
# GivePoint
# -------------------------
@admin.register(GivePoint)
class GivePointAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "group",
        "mentor",
        "student",
        "point_type",
        "amount",
        "created_at",
    )
    list_filter = ("date", "group", "point_type", "mentor")
    search_fields = (
        "mentor__user__username",
        "mentor__user__email",
        "student__user__username",
        "student__user__email",
        "group__name",
        "point_type__name",
    )
    autocomplete_fields = ("mentor", "student", "group", "point_type")
    readonly_fields = ("created_at",)
    ordering = ("-date", "-created_at")

    fieldsets = (
        ("Asosiy", {"fields": ("date", "group", "mentor", "student")}),
        ("Baholash", {"fields": ("point_type", "amount", "description")}),
        ("System", {"fields": ("created_at",)}),
    )


# -------------------------
# Book
# -------------------------
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "student")
    list_filter = ("status",)
    search_fields = ("title", "author", "student__user__username", "student__user__email")
    autocomplete_fields = ("student",)
    ordering = ("-id",)


# -------------------------
# News
# -------------------------
@admin.register(New)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "created_at")
    search_fields = ("title", "user__username", "user__email")
    list_filter = ("created_at",)
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)


# -------------------------
# Auction
# -------------------------
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("id", "description", "data", "time")
    list_filter = ("data",)
    search_fields = ("description",)
    ordering = ("-data", "-time")


# -------------------------
# Product
# -------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "auction", "amount", "point_cost")
    list_filter = ("auction",)
    search_fields = ("name",)
    autocomplete_fields = ("auction",)
    ordering = ("-id",)