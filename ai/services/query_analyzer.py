from datetime import timedelta
from django.db.models import Count, Sum, Avg, Max, Min, Q
from django.utils import timezone
from main.models import Student, Mentor, Group, Course, Book, GivePoint


class QueryAnalyzer:

    @staticmethod
    def analyze_question(question: str) -> dict:
        question_lower = question.lower()

        if any(word in question_lower for word in ['kun', 'day', 'hafta', 'week', 'oy', 'month', 'oxirgi', 'last', 'so\'nggi']):
            return QueryAnalyzer.get_time_based_analysis(question)
        elif any(word in question_lower for word in ['talaba', 'student', 'ball', 'point', 'top', 'eng ko\'p', 'reyting']):
            return QueryAnalyzer.get_student_analysis(question)
        elif any(word in question_lower for word in ['mentor', 'teacher', 'o\'qituvchi', 'muallif']):
            return QueryAnalyzer.get_mentor_analysis(question)
        elif any(word in question_lower for word in ['kurs', 'course', 'fan', 'predmet']):
            return QueryAnalyzer.get_course_analysis(question)
        elif any(word in question_lower for word in ['guruh', 'group', 'class', 'sinf']):
            return QueryAnalyzer.get_group_analysis(question)
        elif any(word in question_lower for word in ['kitob', 'book', 'o\'qish', 'o\'qiyapman']):
            return QueryAnalyzer.get_book_analysis(question)
        elif any(word in question_lower for word in ['ball', 'point', 'reyting', 'ballar']):
            return QueryAnalyzer.get_points_analysis(question)
        else:
            return QueryAnalyzer.get_all_analytics()

    @staticmethod
    def _fetch_time_students(start_date) -> list:
        give_points = list(
            GivePoint.objects.filter(created_at__gte=start_date)
            .values('student')
            .annotate(total_points=Sum('amount'))
            .order_by('-total_points')[:10]
        )
        student_ids = [gp['student'] for gp in give_points]
        students_map = {
            s.id: s for s in Student.objects.filter(id__in=student_ids).select_related('user')
        }
        result = []
        for gp in give_points:
            s = students_map.get(gp['student'])
            if s:
                result.append({
                    'id': s.id,
                    'username': s.user.username,
                    'first_name': s.first_name or '',
                    'last_name': s.last_name or '',
                    'points_earned': gp['total_points'],
                    'total_points': s.point
                })
        return result

    @staticmethod
    def get_time_based_analysis(question: str) -> dict:
        question_lower = question.lower()
        now = timezone.now()

        if any(word in question_lower for word in ['300', 'uch yuz', 'three hundred']):
            students = list(
                Student.objects.filter(point__gt=300)
                .order_by('-point').select_related('user').prefetch_related('groups')[:10]
            )
            return {
                'type': 'students_by_points',
                'filter': '300 dan ko\'p',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in students],
                'message': f'300 dan ko\'p ball olgan {len(students)} ta talaba',
                'count': len(students)
            }

        elif any(word in question_lower for word in ['500', 'besh yuz', 'five hundred']):
            students = list(
                Student.objects.filter(point__gt=500)
                .order_by('-point').select_related('user').prefetch_related('groups')[:10]
            )
            return {
                'type': 'students_by_points',
                'filter': '500 dan ko\'p',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in students],
                'message': f'500 dan ko\'p ball olgan {len(students)} ta talaba',
                'count': len(students)
            }

        elif any(word in question_lower for word in ['1000', 'ming', 'thousand']):
            students = list(
                Student.objects.filter(point__gt=1000)
                .order_by('-point').select_related('user').prefetch_related('groups')[:10]
            )
            return {
                'type': 'students_by_points',
                'filter': '1000 dan ko\'p',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in students],
                'message': f'1000 dan ko\'p ball olgan {len(students)} ta talaba',
                'count': len(students)
            }

        elif any(word in question_lower for word in ['bugun', 'today']):
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=1))
            return {'type': 'time_based_students', 'period': 'Bugun', 'data': data, 'message': f'Bugun eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

        elif any(word in question_lower for word in ['2 kun', 'ikki kun', 'two day', 'oxirgi 2']):
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=2))
            return {'type': 'time_based_students', 'period': 'Oxirgi 2 kun', 'data': data, 'message': f'Oxirgi 2 kunda eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

        elif any(word in question_lower for word in ['1 kun', 'bir kun', 'one day']):
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=1))
            return {'type': 'time_based_students', 'period': 'Oxirgi 1 kun', 'data': data, 'message': f'Oxirgi 1 kunda eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

        elif any(word in question_lower for word in ['hafta', 'week', 'oxirgi 7']):
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=7))
            return {'type': 'time_based_students', 'period': 'Oxirgi hafta', 'data': data, 'message': f'Oxirgi haftada eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

        elif any(word in question_lower for word in ['oy', 'month', 'oxirgi 30']):
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=30))
            return {'type': 'time_based_students', 'period': 'Oxirgi oy', 'data': data, 'message': f'Oxirgi oyda eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

        else:
            data = QueryAnalyzer._fetch_time_students(now - timedelta(days=2))
            return {'type': 'time_based_students', 'period': 'Oxirgi 2 kun', 'data': data, 'message': f'Oxirgi 2 kunda eng ko\'p ball olgan {len(data)} ta talaba', 'count': len(data)}

    @staticmethod
    def get_student_analysis(question: str) -> dict:
        question_lower = question.lower()

        if any(word in question_lower for word in ['eng ko\'p', 'top', 'best', 'yuqori', 'birinchi']):
            top_students = list(
                Student.objects.order_by('-point').select_related('user').prefetch_related('groups')[:10]
            )
            return {
                'type': 'top_students',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in top_students],
                'message': f'Eng ko\'p ball to\'plagan {len(top_students)} ta talaba',
                'count': len(top_students)
            }

        elif any(word in question_lower for word in ['eng kam', 'bottom', 'past', 'minimal', 'oxirgi']):
            bottom_students = list(
                Student.objects.order_by('point').select_related('user').prefetch_related('groups')[:10]
            )
            return {
                'type': 'bottom_students',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point, 'groups': [g.name for g in s.groups.all()]} for s in bottom_students],
                'message': f'Eng kam ball to\'plagan {len(bottom_students)} ta talaba',
                'count': len(bottom_students)
            }

        elif any(word in question_lower for word in ['jami', 'total', 'hammasi', 'soni', 'nechta']):
            total = Student.objects.count()
            agg = Student.objects.aggregate(avg=Avg('point'), max=Max('point'), min=Min('point'))
            return {
                'type': 'student_stats',
                'data': {'total_students': total, 'average_points': round(agg['avg'] or 0, 2), 'max_points': agg['max'] or 0, 'min_points': agg['min'] or 0},
                'message': f'Jami {total} ta talaba, o\'rtacha {round(agg["avg"] or 0, 2)} ball',
                'count': total
            }

        elif any(word in question_lower for word in ['ro\'yxat', 'list', 'barcha', 'hammasi']):
            students = list(Student.objects.all().order_by('-point').select_related('user')[:20])
            return {
                'type': 'student_list',
                'data': [{'id': s.id, 'username': s.user.username, 'first_name': s.first_name or '', 'last_name': s.last_name or '', 'points': s.point} for s in students],
                'message': f'{len(students)} ta talaba',
                'count': len(students)
            }

        else:
            total = Student.objects.count()
            avg_points = Student.objects.aggregate(Avg('point'))['point__avg'] or 0
            return {
                'type': 'student_stats',
                'data': {'total_students': total, 'average_points': round(avg_points, 2)},
                'message': f'Jami {total} ta talaba, o\'rtacha {round(avg_points, 2)} ball',
                'count': total
            }

    @staticmethod
    def get_mentor_analysis(question: str) -> dict:
        mentors = Mentor.objects.annotate(
            group_count=Count('groups'),
            student_count=Count('groups__student', distinct=True)
        ).order_by('-group_count').select_related('user')

        mentor_data = [
            {'id': m.id, 'username': m.user.username, 'name': m.user.get_full_name() or m.user.username, 'groups': m.group_count, 'students': m.student_count, 'direction': m.direction or ''}
            for m in mentors
        ]
        return {'type': 'mentors', 'data': mentor_data, 'message': f'Jami {len(mentor_data)} ta mentor', 'count': len(mentor_data)}

    @staticmethod
    def get_course_analysis(question: str) -> dict:
        courses = Course.objects.annotate(
            group_count=Count('groups'),
            student_count=Count('groups__student', distinct=True)
        ).order_by('-student_count')

        course_data = [
            {'id': c.id, 'name': c.name, 'groups': c.group_count, 'students': c.student_count, 'is_active': c.is_active}
            for c in courses
        ]
        return {'type': 'courses', 'data': course_data, 'message': f'Jami {len(course_data)} ta kurs', 'count': len(course_data)}

    @staticmethod
    def get_group_analysis(question: str) -> dict:
        groups = Group.objects.annotate(
            student_count=Count('student')
        ).order_by('-student_count').select_related('course', 'mentor__user')

        group_data = [
            {'id': g.id, 'name': g.name, 'course': g.course.name, 'mentor': g.mentor.user.username if g.mentor else 'Yo\'q', 'students': g.student_count, 'active': g.active}
            for g in groups
        ]
        return {'type': 'groups', 'data': group_data, 'message': f'Jami {len(group_data)} ta guruh', 'count': len(group_data)}

    @staticmethod
    def get_book_analysis(question: str) -> dict:
        question_lower = question.lower()
        total_books = Book.objects.count()
        completed = Book.objects.filter(status="Tugatim").count()
        reading = Book.objects.filter(status="O'qiyapman").count()

        if any(word in question_lower for word in ['eng ko\'p', 'popular', 'ko\'p o\'qilgan']):
            books = list(Book.objects.values('title', 'author').annotate(count=Count('id')).order_by('-count')[:10])
            return {'type': 'popular_books', 'data': books, 'message': f'Eng ko\'p o\'qilgan {len(books)} ta kitob', 'count': len(books)}

        return {
            'type': 'books',
            'data': {'total_books': total_books, 'completed_books': completed, 'reading_books': reading, 'completion_rate': round((completed / total_books * 100) if total_books > 0 else 0, 2)},
            'message': f'Jami {total_books} ta kitob, {completed} ta tugatilgan',
            'count': total_books
        }

    @staticmethod
    def get_points_analysis(question: str) -> dict:
        question_lower = question.lower()
        total_points = GivePoint.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        points_by_type = list(
            GivePoint.objects.values('point_type__name').annotate(total=Sum('amount'), count=Count('id')).order_by('-total')
        )

        if any(word in question_lower for word in ['tur', 'type', 'kategoriya']):
            return {'type': 'points_by_type', 'data': points_by_type, 'message': 'Ball turlari bo\'yicha taqsimot', 'count': len(points_by_type)}

        return {
            'type': 'points',
            'data': {'total_points_given': total_points, 'points_by_type': points_by_type},
            'message': f'Jami {total_points} ta ball berilgan',
            'count': total_points
        }

    @staticmethod
    def get_all_analytics() -> dict:
        students_count = Student.objects.count()
        mentors_count = Mentor.objects.count()
        courses_count = Course.objects.count()
        groups_count = Group.objects.count()
        books_count = Book.objects.count()
        total_points = GivePoint.objects.aggregate(Sum('amount'))['amount__sum'] or 0

        return {
            'type': 'all_analytics',
            'data': {
                'students': {'total': students_count, 'average_points': round(Student.objects.aggregate(Avg('point'))['point__avg'] or 0, 2)},
                'mentors': {'total': mentors_count},
                'courses': {'total': courses_count},
                'groups': {'total': groups_count},
                'books': {'total': books_count},
                'points': {'total': total_points}
            },
            'message': f'Jami: {students_count} talaba, {mentors_count} mentor, {courses_count} kurs, {groups_count} guruh',
            'count': students_count + mentors_count + courses_count + groups_count
        }

    @staticmethod
    def search_by_name(search_term: str) -> dict:
        students = list(
            Student.objects.filter(
                Q(user__username__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term)
            ).select_related('user')[:10]
        )

        mentors = list(
            Mentor.objects.filter(
                Q(user__username__icontains=search_term) |
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term)
            ).select_related('user')[:10]
        )

        courses = list(Course.objects.filter(name__icontains=search_term)[:10])
        groups = list(Group.objects.filter(name__icontains=search_term)[:10])

        return {
            'type': 'search_results',
            'data': {
                'students': [{'id': s.id, 'username': s.user.username, 'name': f"{s.first_name} {s.last_name}".strip(), 'points': s.point} for s in students],
                'mentors': [{'id': m.id, 'username': m.user.username, 'name': m.user.get_full_name() or m.user.username} for m in mentors],
                'courses': [{'id': c.id, 'name': c.name} for c in courses],
                'groups': [{'id': g.id, 'name': g.name} for g in groups]
            },
            'message': f'Qidiruv natijalari: {len(students)} talaba, {len(mentors)} mentor, {len(courses)} kurs, {len(groups)} guruh',
            'count': len(students) + len(mentors) + len(courses) + len(groups)
        }
