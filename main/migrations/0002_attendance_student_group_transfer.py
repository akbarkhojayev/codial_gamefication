# Generated manually for attendance and student group transfer workflows.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(default=django.utils.timezone.localdate)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("absent", "Absent"),
                            ("late", "Late"),
                            ("excused", "Excused"),
                        ],
                        default="present",
                        max_length=20,
                    ),
                ),
                ("note", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_records",
                        to="main.group",
                    ),
                ),
                (
                    "mentor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="attendance_records",
                        to="main.mentor",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_records",
                        to="main.student",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudentGroupTransferLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "from_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transfer_out_logs",
                        to="main.group",
                    ),
                ),
                (
                    "moved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="student_group_moves",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_transfer_logs",
                        to="main.student",
                    ),
                ),
                (
                    "to_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transfer_in_logs",
                        to="main.group",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="attendance",
            constraint=models.UniqueConstraint(
                fields=("student", "group", "date"),
                name="uniq_attendance_student_group_date",
            ),
        ),
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(fields=["group", "date"], name="main_attend_group_i_7b6ec8_idx"),
        ),
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(fields=["student", "date"], name="main_attend_student_b88e8f_idx"),
        ),
        migrations.AddIndex(
            model_name="studentgrouptransferlog",
            index=models.Index(fields=["student", "created_at"], name="main_studen_student_223e49_idx"),
        ),
        migrations.AddIndex(
            model_name="studentgrouptransferlog",
            index=models.Index(fields=["from_group", "to_group"], name="main_studen_from_gr_e645cc_idx"),
        ),
    ]
