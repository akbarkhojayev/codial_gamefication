# Generated manually for list endpoint performance.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_attendance_student_group_transfer"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="group",
            index=models.Index(fields=["active", "created_at"], name="main_group_active_63a05b_idx"),
        ),
        migrations.AddIndex(
            model_name="group",
            index=models.Index(fields=["mentor", "created_at"], name="main_group_mentor__79e18d_idx"),
        ),
        migrations.AddIndex(
            model_name="group",
            index=models.Index(fields=["course", "active"], name="main_group_course__dd0ed4_idx"),
        ),
        migrations.AddIndex(
            model_name="student",
            index=models.Index(fields=["point"], name="main_studen_point_61ee75_idx"),
        ),
        migrations.AddIndex(
            model_name="student",
            index=models.Index(fields=["created_at"], name="main_studen_created_0e8a6b_idx"),
        ),
        migrations.AddIndex(
            model_name="givepoint",
            index=models.Index(fields=["date", "created_at"], name="main_givepo_date_e5115e_idx"),
        ),
        migrations.AddIndex(
            model_name="givepoint",
            index=models.Index(fields=["group", "date"], name="main_givepo_group_i_101d3e_idx"),
        ),
        migrations.AddIndex(
            model_name="givepoint",
            index=models.Index(fields=["student", "created_at"], name="main_givepo_student_77d616_idx"),
        ),
        migrations.AddIndex(
            model_name="givepoint",
            index=models.Index(fields=["mentor", "date"], name="main_givepo_mentor__bb0100_idx"),
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["student", "status"], name="main_book_student_7598fd_idx"),
        ),
        migrations.AddIndex(
            model_name="new",
            index=models.Index(fields=["pin", "created_at"], name="main_new_pin_6f49ed_idx"),
        ),
        migrations.AddIndex(
            model_name="auction",
            index=models.Index(fields=["is_active", "data"], name="main_auctio_is_acti_f554cc_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["auction"], name="main_produc_auction_626c11_idx"),
        ),
    ]
