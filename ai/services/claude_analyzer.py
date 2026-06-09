import json
import os
from datetime import timedelta

from groq import Groq
from django.db.models import Count, Sum, Avg, Max, Min, Q
from django.utils import timezone

from main.models import Student, Mentor, Group, Course, Book, GivePoint


def _int_param(desc=""):
    return {"description": desc}


def _str_param(desc=""):
    return {"type": "string", "description": desc}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "filter_students",
            "description": (
                "Filter and rank students. "
                "Uzbek: talaba, o'quvchi, ball, coin, reyting, top, eng ko'p, eng kam, "
                "kitob o'qigan (order_by=books_desc), eng ko'p ball olgan (order_by=points_received_desc)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "min_points": _int_param("Minimum total accumulated points"),
                    "max_points": _int_param("Maximum total accumulated points"),
                    "name_contains": _str_param("Search by first_name, last_name or username"),
                    "group_name": _str_param("Filter by group name"),
                    "course_name": _str_param("Filter by course name"),
                    "mentor_name": _str_param("Filter students who belong to this mentor's groups"),
                    "book_status": _str_param("Filter students who have books with status: O'qiyapman or Tugatim"),
                    "order_by": _str_param(
                        "Sort order: points_desc (default), points_asc, name_asc, created_desc, "
                        "books_desc (rank by total books), books_completed_desc (rank by completed books), "
                        "points_received_desc (rank by points received in a period, use with date_from/date_to or days_ago)"
                    ),
                    "date_from": _str_param("Filter by points received from this date YYYY-MM-DD (used with points_received_desc)"),
                    "date_to": _str_param("Filter by points received until this date YYYY-MM-DD"),
                    "days_ago": _int_param("Received points in last N days (alternative to date_from/date_to)"),
                    "min_points_in_period": _int_param("Min points received in the period"),
                    "limit": _int_param("Number of results (default 10, max 50)"),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_mentors",
            "description": (
                "Filter and rank mentors/teachers. "
                "Uzbek: mentor, teacher, o'qituvchi, ustoz, eng ko'p ball bergan, faol mentor. "
                "For 'did not give' use find_mentors_no_activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_contains": _str_param("Search by name or username"),
                    "direction": _str_param("Filter by direction/specialization"),
                    "order_by": _str_param(
                        "Sort: groups_desc (default), students_desc, name_asc, "
                        "points_given_desc (rank by total points given to students)"
                    ),
                    "date_from": _str_param("Count points given from this date YYYY-MM-DD (used with points_given_desc)"),
                    "date_to": _str_param("Count points given until this date YYYY-MM-DD"),
                    "days_ago": _int_param("Count points given in last N days"),
                    "limit": _int_param("Number of results (default 20)"),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_groups",
            "description": (
                "Filter and rank groups. "
                "Uzbek: guruh, sinf, class, eng ko'p ballga ega guruh, faol guruh."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_contains": _str_param("Search by group name"),
                    "course_name": _str_param("Filter by course name"),
                    "mentor_name": _str_param("Filter by mentor name"),
                    "active": _str_param("true or false"),
                    "order_by": _str_param(
                        "Sort: students_desc (default), name_asc, created_desc, "
                        "total_points_desc (rank by total points received in group)"
                    ),
                    "date_from": _str_param("Count points from this date YYYY-MM-DD (used with total_points_desc)"),
                    "date_to": _str_param("Count points until this date YYYY-MM-DD"),
                    "days_ago": _int_param("Count points in last N days"),
                    "limit": _int_param("Number of results (default 20)"),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_mentors_no_activity",
            "description": (
                "Find mentors/teachers who did NOT give points on a date/period. "
                "MUST use when question has: qoymadi, bermadi, faol emas, did not give, not active, "
                "coin qoymadi, ball bermadi, ball qoymadi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exact_date": _str_param("Exact date YYYY-MM-DD. Extract from question."),
                    "days_ago": _int_param("Last N days (if no exact date)"),
                    "group_name": _str_param("Filter by group"),
                    "course_name": _str_param("Filter by course"),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_students_no_activity",
            "description": (
                "Find students who did NOT receive any points on a date/period. "
                "Use when: ball olmadi, coin olmadi, faol emas talabalar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exact_date": _str_param("Exact date YYYY-MM-DD"),
                    "days_ago": _int_param("Last N days"),
                    "group_name": _str_param(),
                    "course_name": _str_param(),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_courses",
            "description": "Filter courses. Uzbek: kurs, yo'nalish, fan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_contains": _str_param(),
                    "is_active": _str_param("true or false"),
                    "order_by": _str_param("Sort: students_desc, groups_desc, name_asc"),
                    "limit": _int_param(),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_books",
            "description": "Filter books. Uzbek: kitob, o'qiyapman, tugatdim.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_contains": _str_param(),
                    "author_contains": _str_param(),
                    "status": _str_param("O'qiyapman or Tugatim"),
                    "student_name": _str_param("Filter by student name"),
                    "order_by": _str_param("Sort: count_desc, title_asc"),
                    "limit": _int_param(),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_points",
            "description": (
                "Filter individual point transactions. "
                "Uzbek: ball berdi, coin qo'ydi, berilgan ballar, qaysi ball berildi. "
                "For 'did not give' use find_mentors_no_activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_name": _str_param(),
                    "mentor_name": _str_param(),
                    "group_name": _str_param(),
                    "point_type_name": _str_param("Filter by point type name e.g. Hulq, Dars, Imtihon"),
                    "min_amount": _int_param("Min amount (default 1)"),
                    "exact_date": _str_param("Exact date YYYY-MM-DD"),
                    "date_from": _str_param("Date range start YYYY-MM-DD"),
                    "date_to": _str_param("Date range end YYYY-MM-DD"),
                    "days_ago": _int_param("Last N days"),
                    "order_by": _str_param("Sort: amount_desc, date_desc"),
                    "limit": _int_param(),
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_statistics",
            "description": "Aggregate statistics. Uzbek: statistika, jami, nechta, hammasi, umumiy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": _str_param(
                        "Which entity: students, mentors, groups, courses, books, points, all"
                    ),
                },
                "required": ["entity"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are an analytics AI for a gamified education platform called Codial (Uzbekistan).

=== DATABASE SCHEMA ===
- Student: user(username), first_name, last_name, point(total accumulated), groups(M2M→Group), created_at
- Mentor: user(username, first_name, last_name), direction, point_limit, groups(FK→Group)
- Group: name, course(FK→Course), mentor(FK→Mentor), active, created_at
- Course: name, is_active
- Book: title, author, status("O'qiyapman"/"Tugatim"), student(FK→Student)
- GivePoint: student(FK), mentor(FK), group(FK), point_type(FK→PointType.name), amount, date(YYYY-MM-DD), created_at
- PointType: name (e.g. Hulq, Dars, Imtihon, Kitob), max_point

=== UZBEK/RUSSIAN VOCABULARY ===
- "coin / ball / xol / ochko" = points
- "qo'ydi / berdi / topshirdi" = gave points
- "qoymadi / bermadi / olmadi / topshirmadi" = did NOT give/receive → find_mentors_no_activity or find_students_no_activity
- "teacher / mentor / ustoz / o'qituvchi / domla" = Mentor model
- "talaba / o'quvchi / student / bola" = Student model
- "guruh / sinf / group" = Group model
- "kurs / yo'nalish / direction" = Course model
- "faol / active / ishlayapti" = active=true
- "faol emas / inactive / ishlamaydi" = active=false
- "eng ko'p ball bergan mentor" → filter_mentors with order_by=points_given_desc
- "eng ko'p ball olgan talaba" → filter_students with order_by=points_desc
- "eng ko'p ball olgan guruh" → filter_groups with order_by=total_points_desc
- "eng ko'p kitob o'qigan" → filter_students with order_by=books_desc
- "eng ko'p kitob tugatgan" → filter_students with order_by=books_completed_desc

=== DATE HANDLING ===
- Extract exact date: "2026-05-08 kuni" → exact_date="2026-05-08"
- "bugun/today" → exact_date = today's date in YYYY-MM-DD
- "kecha/yesterday" → exact_date = yesterday in YYYY-MM-DD
- "bu hafta/this week" → days_ago=7
- "bu oy/this month" → days_ago=30
- Date range: "X dan Y gacha" → date_from=X, date_to=Y

=== RULES ===
1. "qoymadi/bermadi/olmadi" → find_mentors_no_activity or find_students_no_activity
2. "eng ko'p ball bergan mentor" → filter_mentors(order_by=points_given_desc)
3. "eng ko'p ball olgan guruh" → filter_groups(order_by=total_points_desc)
4. "kitob o'qigan" → filter_students(order_by=books_desc)
5. Always set min_amount=1 in filter_points unless 0-amount specifically requested
6. Always call exactly ONE tool — never respond in plain text"""

_DATE_WORDS = {
    'bugun': 0, 'today': 0,
    'kecha': -1, 'yesterday': -1,
    'ertaga': 1, 'tomorrow': 1,
}

_INT_KEYS = {
    'min_points', 'max_points', 'limit', 'days_ago',
    'min_points_in_period', 'min_amount',
}
_DATE_KEYS = {'exact_date', 'date_from', 'date_to'}
_BOOL_KEYS = {'active', 'is_active'}

_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _coerce_params(params: dict) -> dict:
    result = {}
    for k, v in params.items():
        if v is None or v == '':
            continue
        if k in _INT_KEYS:
            try:
                result[k] = int(v)
            except (TypeError, ValueError):
                pass
        elif k in _DATE_KEYS:
            if isinstance(v, str):
                offset = _DATE_WORDS.get(v.lower())
                if offset is not None:
                    today = timezone.now().date()
                    result[k] = str(today + timedelta(days=offset))
                else:
                    result[k] = v
            else:
                result[k] = v
        elif k in _BOOL_KEYS:
            result[k] = v.lower() in ('true', '1', 'yes') if isinstance(v, str) else bool(v)
        else:
            result[k] = v
    return result


def _build_period_filter(params: dict) -> tuple:
    gp_filter = Q(amount__gt=0)
    exact_date = params.get('exact_date')
    days_ago = params.get('days_ago')

    if exact_date:
        return gp_filter & Q(date=exact_date), exact_date
    if days_ago:
        since = timezone.now().date() - timedelta(days=days_ago)
        return gp_filter & Q(date__gte=since), f'oxirgi {days_ago} kun'

    today = timezone.now().date()
    return gp_filter & Q(date=today), str(today)


def _apply_date_range(qs, params: dict, date_field='date'):
    if params.get('exact_date'):
        qs = qs.filter(**{date_field: params['exact_date']})
    elif params.get('date_from') or params.get('date_to'):
        if params.get('date_from'):
            qs = qs.filter(**{f'{date_field}__gte': params['date_from']})
        if params.get('date_to'):
            qs = qs.filter(**{f'{date_field}__lte': params['date_to']})
    elif params.get('days_ago'):
        since = timezone.now().date() - timedelta(days=params['days_ago'])
        qs = qs.filter(**{f'{date_field}__gte': since})
    return qs


def _execute_find_mentors_no_activity(params: dict) -> dict:
    gp_filter, period_label = _build_period_filter(params)
    active_ids = set(
        GivePoint.objects.filter(gp_filter).values_list('mentor', flat=True).distinct()
    )
    qs = Mentor.objects.select_related('user').annotate(group_count=Count('groups', distinct=True))
    if params.get('group_name'):
        qs = qs.filter(groups__name__icontains=params['group_name'])
    if params.get('course_name'):
        qs = qs.filter(groups__course__name__icontains=params['course_name'])

    mentors = list(qs.exclude(id__in=active_ids)[:100])
    return {
        'type': 'mentors_no_activity',
        'period': period_label,
        'data': [{'id': m.id, 'username': m.user.username, 'name': m.user.get_full_name() or m.user.username, 'direction': m.direction or '', 'groups': m.group_count} for m in mentors],
        'count': len(mentors),
        'message': f"{period_label} kuni coin/ball qo'ymagan {len(mentors)} ta mentor",
    }


def _execute_find_students_no_activity(params: dict) -> dict:
    gp_filter, period_label = _build_period_filter(params)
    active_ids = set(
        GivePoint.objects.filter(gp_filter).values_list('student', flat=True).distinct()
    )
    qs = Student.objects.select_related('user').prefetch_related('groups')
    if params.get('group_name'):
        qs = qs.filter(groups__name__icontains=params['group_name'])
    if params.get('course_name'):
        qs = qs.filter(groups__course__name__icontains=params['course_name'])

    students = list(qs.exclude(id__in=active_ids)[:100])
    return {
        'type': 'students_no_activity',
        'period': period_label,
        'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in students],
        'count': len(students),
        'message': f"{period_label} kuni coin/ball olmagan {len(students)} ta talaba",
    }


def _execute_filter_students(params: dict) -> dict:
    qs = Student.objects.select_related('user').prefetch_related('groups')

    order_by = params.get('order_by') or 'points_desc'

    # Period-based filtering
    has_period = params.get('days_ago') or params.get('date_from') or params.get('date_to')

    if order_by == 'points_received_desc' and has_period:
        gp_qs = GivePoint.objects.filter(amount__gt=0)
        gp_qs = _apply_date_range(gp_qs, params)
        min_in_period = params.get('min_points_in_period')
        agg = gp_qs.values('student').annotate(total=Sum('amount'))
        if min_in_period:
            agg = agg.filter(total__gte=min_in_period)
        agg_rows = list(agg.order_by('-total')[:min(params.get('limit', 10), 50)])
        student_ids = [row['student'] for row in agg_rows]
        points_map = {row['student']: row['total'] for row in agg_rows}
        students_map = {s.id: s for s in qs.filter(id__in=student_ids)}
        students = [students_map[sid] for sid in student_ids if sid in students_map]

        return {
            'type': 'students',
            'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'points_in_period': points_map.get(s.id, 0), 'groups': [g.name for g in s.groups.all()]} for s in students],
            'count': len(students),
            'message': f'{len(students)} ta talaba topildi',
        }

    elif has_period and order_by not in ('books_desc', 'books_completed_desc'):
        gp_qs = GivePoint.objects.filter(amount__gt=0)
        gp_qs = _apply_date_range(gp_qs, params)
        min_in_period = params.get('min_points_in_period')
        agg = gp_qs.values('student').annotate(total=Sum('amount'))
        if min_in_period:
            agg = agg.filter(total__gte=min_in_period)
        qs = qs.filter(id__in=agg.values_list('student', flat=True).distinct())

    # Standard filters
    if params.get('min_points') is not None:
        qs = qs.filter(point__gte=params['min_points'])
    if params.get('max_points') is not None:
        qs = qs.filter(point__lte=params['max_points'])
    if params.get('name_contains'):
        n = params['name_contains']
        qs = qs.filter(Q(first_name__icontains=n) | Q(last_name__icontains=n) | Q(user__username__icontains=n))
    if params.get('group_name'):
        qs = qs.filter(groups__name__icontains=params['group_name'])
    if params.get('course_name'):
        qs = qs.filter(groups__course__name__icontains=params['course_name'])
    if params.get('mentor_name'):
        n = params['mentor_name']
        qs = qs.filter(Q(groups__mentor__user__username__icontains=n) | Q(groups__mentor__user__first_name__icontains=n) | Q(groups__mentor__user__last_name__icontains=n))
    if params.get('book_status'):
        qs = qs.filter(book__status=params['book_status'])

    if order_by == 'books_desc':
        qs = qs.annotate(book_count=Count('book', distinct=True)).order_by('-book_count')
    elif order_by == 'books_completed_desc':
        qs = qs.annotate(book_count=Count('book', distinct=True, filter=Q(book__status='Tugatim'))).order_by('-book_count')
    else:
        order_map = {'points_desc': '-point', 'points_asc': 'point', 'name_asc': 'first_name', 'created_desc': '-created_at'}
        qs = qs.order_by(order_map.get(order_by, '-point'))

    limit = min(params.get('limit', 10), 50)
    students = list(qs.distinct()[:limit])
    show_books = order_by in ('books_desc', 'books_completed_desc')

    def _row(s):
        d = {'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]}
        if show_books:
            d['book_count'] = getattr(s, 'book_count', 0)
        return d

    return {
        'type': 'students',
        'data': [_row(s) for s in students],
        'count': len(students),
        'message': f'{len(students)} ta talaba topildi',
    }


def _execute_filter_mentors(params: dict) -> dict:
    order_by = params.get('order_by') or 'groups_desc'

    if order_by == 'points_given_desc':
        gp_qs = GivePoint.objects.filter(amount__gt=0)
        gp_qs = _apply_date_range(gp_qs, params)
        agg = list(gp_qs.values('mentor').annotate(total=Sum('amount')).order_by('-total')[:min(params.get('limit', 20), 50)])
        mentor_ids = [row['mentor'] for row in agg]
        mentors_map = {m.id: m for m in Mentor.objects.filter(id__in=mentor_ids).select_related('user').annotate(group_count=Count('groups', distinct=True), student_count=Count('groups__student', distinct=True))}
        points_map = {row['mentor']: row['total'] for row in agg}

        if params.get('name_contains'):
            n = params['name_contains']
            mentor_ids = [mid for mid in mentor_ids if mid in mentors_map and (n.lower() in mentors_map[mid].user.username.lower() or n.lower() in (mentors_map[mid].user.get_full_name() or '').lower())]

        mentors = [mentors_map[mid] for mid in mentor_ids if mid in mentors_map]
        return {
            'type': 'mentors',
            'data': [{'id': m.id, 'username': m.user.username, 'name': m.user.get_full_name() or m.user.username, 'direction': m.direction or '', 'groups': m.group_count, 'students': m.student_count, 'points_given': points_map.get(m.id, 0)} for m in mentors],
            'count': len(mentors),
            'message': f'{len(mentors)} ta mentor topildi',
        }

    qs = Mentor.objects.annotate(
        group_count=Count('groups', distinct=True),
        student_count=Count('groups__student', distinct=True),
    ).select_related('user')

    if params.get('name_contains'):
        n = params['name_contains']
        qs = qs.filter(Q(user__username__icontains=n) | Q(user__first_name__icontains=n) | Q(user__last_name__icontains=n))
    if params.get('direction'):
        qs = qs.filter(direction__icontains=params['direction'])

    order_map = {'groups_desc': '-group_count', 'students_desc': '-student_count', 'name_asc': 'user__username'}
    qs = qs.order_by(order_map.get(order_by, '-group_count'))

    limit = min(params.get('limit', 20), 50)
    mentors = list(qs[:limit])
    return {
        'type': 'mentors',
        'data': [{'id': m.id, 'username': m.user.username, 'name': m.user.get_full_name() or m.user.username, 'direction': m.direction or '', 'groups': m.group_count, 'students': m.student_count} for m in mentors],
        'count': len(mentors),
        'message': f'{len(mentors)} ta mentor topildi',
    }


def _execute_filter_groups(params: dict) -> dict:
    order_by = params.get('order_by') or 'students_desc'

    if order_by == 'total_points_desc':
        gp_qs = GivePoint.objects.filter(amount__gt=0)
        gp_qs = _apply_date_range(gp_qs, params)
        agg = list(gp_qs.values('group').annotate(total=Sum('amount')).order_by('-total')[:min(params.get('limit', 20), 50)])
        group_ids = [row['group'] for row in agg]
        groups_map = {g.id: g for g in Group.objects.filter(id__in=group_ids).select_related('course', 'mentor__user').annotate(student_count=Count('student', distinct=True))}
        points_map = {row['group']: row['total'] for row in agg}

        groups = [groups_map[gid] for gid in group_ids if gid in groups_map]
        return {
            'type': 'groups',
            'data': [{'id': g.id, 'name': g.name, 'course': g.course.name, 'mentor': g.mentor.user.username if g.mentor else None, 'students': g.student_count, 'active': g.active, 'total_points': points_map.get(g.id, 0)} for g in groups],
            'count': len(groups),
            'message': f'{len(groups)} ta guruh topildi',
        }

    qs = Group.objects.annotate(student_count=Count('student', distinct=True)).select_related('course', 'mentor__user')

    if params.get('name_contains'):
        qs = qs.filter(name__icontains=params['name_contains'])
    if params.get('course_name'):
        qs = qs.filter(course__name__icontains=params['course_name'])
    if params.get('mentor_name'):
        n = params['mentor_name']
        qs = qs.filter(Q(mentor__user__username__icontains=n) | Q(mentor__user__first_name__icontains=n))
    if params.get('active') is not None:
        qs = qs.filter(active=params['active'])

    order_map = {'students_desc': '-student_count', 'name_asc': 'name', 'created_desc': '-created_at'}
    qs = qs.order_by(order_map.get(order_by, '-student_count'))

    limit = min(params.get('limit', 20), 50)
    groups = list(qs[:limit])
    return {
        'type': 'groups',
        'data': [{'id': g.id, 'name': g.name, 'course': g.course.name, 'mentor': g.mentor.user.username if g.mentor else None, 'students': g.student_count, 'active': g.active} for g in groups],
        'count': len(groups),
        'message': f'{len(groups)} ta guruh topildi',
    }


def _execute_filter_courses(params: dict) -> dict:
    qs = Course.objects.annotate(group_count=Count('groups', distinct=True), student_count=Count('groups__student', distinct=True))
    if params.get('name_contains'):
        qs = qs.filter(name__icontains=params['name_contains'])
    if params.get('is_active') is not None:
        qs = qs.filter(is_active=params['is_active'])

    order_map = {'students_desc': '-student_count', 'groups_desc': '-group_count', 'name_asc': 'name'}
    qs = qs.order_by(order_map.get(params.get('order_by') or 'students_desc', '-student_count'))

    limit = min(params.get('limit', 20), 50)
    courses = list(qs[:limit])
    return {
        'type': 'courses',
        'data': [{'id': c.id, 'name': c.name, 'groups': c.group_count, 'students': c.student_count, 'is_active': c.is_active} for c in courses],
        'count': len(courses),
        'message': f'{len(courses)} ta kurs topildi',
    }


def _execute_filter_books(params: dict) -> dict:
    qs = Book.objects.select_related('student__user')
    if params.get('title_contains'):
        qs = qs.filter(title__icontains=params['title_contains'])
    if params.get('author_contains'):
        qs = qs.filter(author__icontains=params['author_contains'])
    if params.get('status'):
        qs = qs.filter(status=params['status'])
    if params.get('student_name'):
        n = params['student_name']
        qs = qs.filter(Q(student__first_name__icontains=n) | Q(student__last_name__icontains=n) | Q(student__user__username__icontains=n))

    qs = qs.order_by('title' if params.get('order_by') == 'title_asc' else '-id')
    limit = min(params.get('limit', 20), 50)
    books = list(qs[:limit])
    return {
        'type': 'books',
        'data': [{'id': b.id, 'title': b.title, 'author': b.author, 'status': b.status, 'student': b.student.user.username} for b in books],
        'count': len(books),
        'message': f'{len(books)} ta kitob topildi',
    }


def _execute_filter_points(params: dict) -> dict:
    qs = GivePoint.objects.select_related('student__user', 'mentor__user', 'group', 'point_type')

    if params.get('student_name'):
        n = params['student_name']
        qs = qs.filter(Q(student__first_name__icontains=n) | Q(student__last_name__icontains=n) | Q(student__user__username__icontains=n))
    if params.get('mentor_name'):
        n = params['mentor_name']
        qs = qs.filter(Q(mentor__user__username__icontains=n) | Q(mentor__user__first_name__icontains=n))
    if params.get('group_name'):
        qs = qs.filter(group__name__icontains=params['group_name'])
    if params.get('point_type_name'):
        qs = qs.filter(point_type__name__icontains=params['point_type_name'])

    qs = qs.filter(amount__gte=params.get('min_amount', 1))
    qs = _apply_date_range(qs, params)

    qs = qs.order_by('-amount' if params.get('order_by') == 'amount_desc' else '-date')
    limit = min(params.get('limit', 20), 50)
    points = list(qs[:limit])
    return {
        'type': 'points',
        'data': [{'id': p.id, 'student': p.student.user.username, 'mentor': p.mentor.user.username, 'group': p.group.name, 'point_type': p.point_type.name, 'amount': p.amount, 'date': str(p.date)} for p in points],
        'count': len(points),
        'message': f'{len(points)} ta ball yozuvi topildi',
    }


def _execute_get_statistics(params: dict) -> dict:
    entity = params.get('entity', 'all')

    students_stats = None
    agg = None
    if entity in ('students', 'all'):
        agg = Student.objects.aggregate(total=Count('id'), avg_points=Avg('point'), max_points=Max('point'), min_points=Min('point'))
        students_stats = {'total': agg['total'], 'avg_points': round(agg['avg_points'] or 0, 2), 'max_points': agg['max_points'] or 0, 'min_points': agg['min_points'] or 0}
        if entity == 'students':
            return {'type': 'statistics', 'data': {'students': students_stats}, 'count': agg['total'], 'message': f"Jami {agg['total']} ta talaba"}

    if entity == 'mentors':
        total = Mentor.objects.count()
        return {'type': 'statistics', 'data': {'mentors': {'total': total}}, 'count': total, 'message': f'Jami {total} ta mentor'}
    if entity == 'groups':
        total = Group.objects.count()
        active = Group.objects.filter(active=True).count()
        return {'type': 'statistics', 'data': {'groups': {'total': total, 'active': active}}, 'count': total, 'message': f'Jami {total} ta guruh'}
    if entity == 'courses':
        total = Course.objects.count()
        active = Course.objects.filter(is_active=True).count()
        return {'type': 'statistics', 'data': {'courses': {'total': total, 'active': active}}, 'count': total, 'message': f'Jami {total} ta kurs'}
    if entity == 'books':
        total = Book.objects.count()
        completed = Book.objects.filter(status='Tugatim').count()
        reading = Book.objects.filter(status="O'qiyapman").count()
        return {'type': 'statistics', 'data': {'books': {'total': total, 'completed': completed, 'reading': reading}}, 'count': total, 'message': f'Jami {total} ta kitob'}
    if entity == 'points':
        total = GivePoint.objects.aggregate(total=Sum('amount'))['total'] or 0
        return {'type': 'statistics', 'data': {'points': {'total_given': total}}, 'count': total, 'message': f'Jami {total} ball berilgan'}

    mentor_count = Mentor.objects.count()
    total_points = GivePoint.objects.aggregate(total=Sum('amount'))['total'] or 0
    return {
        'type': 'statistics',
        'data': {'students': students_stats, 'mentors': {'total': mentor_count}, 'groups': {'total': Group.objects.count()}, 'courses': {'total': Course.objects.count()}, 'books': {'total': Book.objects.count()}, 'points': {'total_given': total_points}},
        'count': agg['total'],
        'message': f"Jami: {agg['total']} talaba, {mentor_count} mentor",
    }


TOOL_EXECUTORS = {
    'filter_students': _execute_filter_students,
    'find_mentors_no_activity': _execute_find_mentors_no_activity,
    'find_students_no_activity': _execute_find_students_no_activity,
    'filter_mentors': _execute_filter_mentors,
    'filter_groups': _execute_filter_groups,
    'filter_courses': _execute_filter_courses,
    'filter_books': _execute_filter_books,
    'filter_points': _execute_filter_points,
    'get_statistics': _execute_get_statistics,
}


def analyze_with_claude(question: str) -> dict:
    client = _get_groq_client()

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_tokens=512,
        tool_choice="auto",
        tools=TOOLS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )

    msg = response.choices[0].message
    tool_calls = msg.tool_calls

    if not tool_calls:
        text = (msg.content or "").strip()
        return {
            'type': 'general',
            'query_type': 'general',
            'data': None,
            'count': 0,
            'message': text or "Bu savolga mavjud ma'lumotlar asosida javob bera olmayman.",
        }

    tool_name = tool_calls[0].function.name
    tool_input = _coerce_params(json.loads(tool_calls[0].function.arguments))

    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        raise RuntimeError(f"Unknown tool: {tool_name}")

    result = executor(tool_input)
    result['query_type'] = tool_name
    return result
