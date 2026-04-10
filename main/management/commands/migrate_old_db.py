"""
Management command: migrate_old_db
Eski old_db.sqlite3 dan yangi db.sqlite3 ga
Course, Mentor, Group, Student ma'lumotlarini ko'chiradi.

Ishlatish:
    python3 manage.py migrate_old_db
    python3 manage.py migrate_old_db --dry-run   # faqat hisobot, hech narsa yozmaydi
"""

import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as tz
from main.models import UserProfile, Course, Mentor, Group, Student


def _make_aware(dt_str):
    """SQLite string → aware datetime"""
    if not dt_str:
        return None
    dt = datetime.fromisoformat(dt_str)
    return tz.make_aware(dt) if tz.is_naive(dt) else dt


OLD_DB_PATH = 'old_db.sqlite3'


class Command(BaseCommand):
    help = "Ko'chirish: old_db.sqlite3 → yangi db (Course, Mentor, Group, Student)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Hech narsa yozmaydi, faqat nechta yozuv ko'chirilishini ko'rsatadi",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        conn = sqlite3.connect(OLD_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY-RUN rejimi ==="))

        try:
            with transaction.atomic():
                course_map = self._migrate_courses(cur, dry_run)
                mentor_map = self._migrate_mentors(cur, dry_run, course_map)
                group_map = self._migrate_groups(cur, dry_run, mentor_map)
                self._migrate_students(cur, dry_run, group_map)

                if dry_run:
                    # Hech narsa saqlanmasin
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING("Dry-run: barcha o'zgarishlar bekor qilindi."))
                else:
                    self.stdout.write(self.style.SUCCESS("Ko'chirish muvaffaqiyatli yakunlandi!"))
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    def _migrate_courses(self, cur, dry_run):
        """Course → Course (name bo'yicha get_or_create)"""
        cur.execute("SELECT id, name FROM main_course")
        rows = cur.fetchall()
        course_map = {}  # old_id → new Course obj

        created = skipped = 0
        for row in rows:
            obj, is_new = Course.objects.get_or_create(name=row['name'])
            course_map[row['id']] = obj
            if is_new:
                created += 1
            else:
                skipped += 1

        self.stdout.write(f"Course: {created} yangi, {skipped} mavjud")
        return course_map

    # ------------------------------------------------------------------ #
    def _migrate_mentors(self, cur, dry_run, course_map):
        """
        Eski Mentor → yangi UserProfile (role='teacher') + Mentor
        Eski auth_user → yangi UserProfile
        """
        cur.execute("""
            SELECT m.id, m.point_limit, m.course_id,
                   u.username, u.first_name, u.last_name, u.email,
                   u.password, u.is_staff, u.is_superuser, u.is_active, u.date_joined
            FROM main_mentor m
            JOIN auth_user u ON u.id = m.user_id
        """)
        rows = cur.fetchall()
        mentor_map = {}  # old_id → new Mentor obj

        created = skipped = 0
        for row in rows:
            # UserProfile
            up, is_new = UserProfile.objects.get_or_create(
                username=row['username'],
                defaults={
                    'first_name': row['first_name'] or '',
                    'last_name': row['last_name'] or '',
                    'email': row['email'] or '',
                    'password': row['password'],
                    'is_staff': bool(row['is_staff']),
                    'is_superuser': bool(row['is_superuser']),
                    'is_active': bool(row['is_active']),
                    'role': 'teacher',
                }
            )
            if is_new:
                up.date_joined = _make_aware(row['date_joined'])
                up.save(update_fields=['date_joined'])

            # Mentor
            mentor, m_new = Mentor.objects.get_or_create(
                user=up,
                defaults={'point_limit': row['point_limit']}
            )
            mentor_map[row['id']] = mentor
            if m_new:
                created += 1
            else:
                skipped += 1

        self.stdout.write(f"Mentor: {created} yangi, {skipped} mavjud")
        return mentor_map

    # ------------------------------------------------------------------ #
    def _migrate_groups(self, cur, dry_run, mentor_map):
        """
        Eski Group → yangi Group
        Yangi Group da course majburiy, shuning uchun mentorning course'ini olamiz.
        """
        cur.execute("""
            SELECT g.id, g.name, g.active, g.created_at, g.mentor_id
            FROM main_group g
        """)
        rows = cur.fetchall()
        group_map = {}  # old_id → new Group obj

        created = skipped = 0
        for row in rows:
            mentor = mentor_map.get(row['mentor_id'])

            # Mentor orqali course topamiz
            # Eski mentorda course_id bor, uni course_map dan olamiz
            # Lekin bu yerda mentor_map → Mentor obj bor, uning course'i yo'q (yangi modelda)
            # Shuning uchun eski DB dan course_id ni to'g'ridan olamiz
            course = None
            if mentor:
                # Eski DB dan ushbu mentorning course_id sini olamiz
                cur.execute("SELECT course_id FROM main_mentor WHERE id=?",
                            (row['mentor_id'],))
                r = cur.fetchone()
                if r:
                    cur.execute("SELECT name FROM main_course WHERE id=?", (r['course_id'],))
                    cn = cur.fetchone()
                    if cn:
                        course, _ = Course.objects.get_or_create(name=cn['name'])

            if course is None:
                # Fallback: birinchi kursni ol yoki yaratma
                course = Course.objects.first()
                if course is None:
                    course = Course.objects.create(name='Nomalum')

            obj, is_new = Group.objects.get_or_create(
                name=row['name'],
                course=course,
                defaults={
                    'mentor': mentor,
                    'active': bool(row['active']),
                }
            )
            group_map[row['id']] = obj
            if is_new:
                created += 1
            else:
                skipped += 1

        self.stdout.write(f"Group: {created} yangi, {skipped} mavjud")
        return group_map

    # ------------------------------------------------------------------ #
    def _migrate_students(self, cur, dry_run, group_map):
        """
        Eski Student → yangi UserProfile (role='student') + Student
        """
        cur.execute("""
            SELECT s.id, s.birth_date, s.image, s.bio, s.point,
                   s.created_at, s.group_id, s.phone_number,
                   u.username, u.first_name, u.last_name, u.email,
                   u.password, u.is_active, u.date_joined
            FROM main_student s
            JOIN auth_user u ON u.id = s.user_id
        """)
        rows = cur.fetchall()

        created = skipped = errors = 0
        for row in rows:
            try:
                # UserProfile
                up, is_new = UserProfile.objects.get_or_create(
                    username=row['username'],
                    defaults={
                        'first_name': row['first_name'] or '',
                        'last_name': row['last_name'] or '',
                        'email': row['email'] or '',
                        'password': row['password'],
                        'is_active': bool(row['is_active']),
                        'role': 'student',
                    }
                )
                if is_new:
                    up.date_joined = _make_aware(row['date_joined'])
                    up.save(update_fields=['date_joined'])

                # Student
                student, s_new = Student.objects.get_or_create(
                    user=up,
                    defaults={
                        'first_name': row['first_name'] or '',
                        'last_name': row['last_name'] or '',
                        'bio': row['bio'],
                        'point': row['point'] or 0,
                        'birth_date': row['birth_date'],
                        'phone_number': row['phone_number'],
                        'image': row['image'] or '',
                    }
                )

                # Group ni ManyToMany ga qo'shamiz
                group = group_map.get(row['group_id'])
                if group:
                    student.groups.add(group)

                if s_new:
                    created += 1
                else:
                    skipped += 1

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"  Xato (username={row['username']}): {e}")
                )

        self.stdout.write(f"Student: {created} yangi, {skipped} mavjud, {errors} xato")
