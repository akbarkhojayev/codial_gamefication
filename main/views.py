from rest_framework import generics
from django.db import transaction
from django.db.models import Count, F, OuterRef, Prefetch, Subquery, Sum, Window, prefetch_related_objects
from django.db.models.functions import Rank
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import *
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from datetime import date as dt_date
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

WEEKDAY_UZ = {
    0: "Dushanba",
    1: "Seshanba",
    2: "Chorshanba",
    3: "Payshanba",
    4: "Juma",
    5: "Shanba",
    6: "Yakshanba",
}

DAYKEY_UZ = {
    "monday": "Dushanba",
    "tuesday": "Seshanba",
    "wednesday": "Chorshanba",
    "thursday": "Payshanba",
    "friday": "Juma",
    "saturday": "Shanba",
    "sunday": "Yakshanba",
}

def _get_request_mentor(user):
    if not user.is_authenticated or user.role != 'teacher':
        return None
    return Mentor.objects.select_related('user').filter(user=user).first()

def _can_manage_group(user, group):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    mentor = _get_request_mentor(user)
    return bool(mentor and group.mentor_id == mentor.id)

def _can_transfer_student_between_groups(user, from_group, to_group):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    mentor = _get_request_mentor(user)
    return bool(
        mentor
        and from_group.mentor_id == mentor.id
        and to_group.mentor_id == mentor.id
        and to_group.active
    )

def _group_for_management(user, group_id):
    group = Group.objects.select_related('course', 'mentor__user').filter(pk=group_id).first()
    if not group:
        return None, Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
    if not _can_manage_group(user, group):
        return None, Response({"detail": "You cannot manage this group"}, status=status.HTTP_403_FORBIDDEN)
    return group, None

class UserFilter(django_filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = ['role']

class UserListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_class = UserFilter
    search_fields = ['username', 'email']
    ordering_fields = ['id', 'username', 'email']
    ordering = ['id']

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CourseFilter(django_filters.FilterSet):
    class Meta:
        model = Course
        fields = ['is_active']

class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = CourseFilter
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']
    ordering = ['id']

    def get_queryset(self):
        return Course.objects.annotate(
            group_count=Count('groups', distinct=True),
            student_count=Count('groups__student', distinct=True),
            teacher_count=Count('groups__mentor', distinct=True),
        )

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.annotate(
            group_count=Count('groups', distinct=True),
            student_count=Count('groups__student', distinct=True),
            teacher_count=Count('groups__mentor', distinct=True),
        )

class MentorFilter(django_filters.FilterSet):
    class Meta:
        model = Mentor
        fields = ['direction']

class MentorListCreateView(generics.ListAPIView):
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MentorFilter
    search_fields = ['user__username', 'user__email', 'direction']
    ordering_fields = ['id', 'user__username']
    ordering = ['id']

    def get_queryset(self):
        groups_qs = (
            Group.objects
            .select_related('course')
            .annotate(
                student_count=Count('student', distinct=True),
                course_group_count=Count('course__groups', distinct=True),
                course_student_count=Count('course__groups__student', distinct=True),
                course_teacher_count=Count('course__groups__mentor', distinct=True),
            )
        )
        return (
            Mentor.objects
            .select_related('user')
            .annotate(total_students_value=Count('groups__student', distinct=True))
            .prefetch_related(Prefetch('groups', queryset=groups_qs))
        )

class MentorCreateView(generics.CreateAPIView):
    queryset = Mentor.objects.all()
    serializer_class = MentorCreateSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

class MentorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MentorSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return MentorUpdateSerializer
        return MentorSerializer

    def get_queryset(self):
        groups_qs = (
            Group.objects
            .select_related('course')
            .annotate(
                student_count=Count('student', distinct=True),
                course_group_count=Count('course__groups', distinct=True),
                course_student_count=Count('course__groups__student', distinct=True),
                course_teacher_count=Count('course__groups__mentor', distinct=True),
            )
        )
        return (
            Mentor.objects
            .select_related('user')
            .annotate(total_students_value=Count('groups__student', distinct=True))
            .prefetch_related(Prefetch('groups', queryset=groups_qs))
        )

class StudentCreateView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentCreateSerializer
    permission_classes = [IsAdminOrTeacher]
    parser_classes = [MultiPartParser, FormParser]

class StudentFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = ['groups']

class StudentListView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = StudentFilter
    search_fields = ['user__username', 'user__email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['id', 'user__username', 'point']
    ordering = ['id']

    def get_queryset(self):
        qs = (
            Student.objects
            .select_related('user')
            .prefetch_related('groups')
            .annotate(
                book_count_value=Count('book', distinct=True),
                student_rank=Window(expression=Rank(), order_by=F('point').desc()),
            )
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(groups__mentor=mentor).distinct()
        return qs

class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdminOrTeacher()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = (
            Student.objects
            .select_related('user')
            .prefetch_related('groups')
            .annotate(
                book_count_value=Count('book', distinct=True),
                student_rank=Window(expression=Rank(), order_by=F('point').desc()),
            )
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(groups__mentor=mentor).distinct()
        return qs

class GroupFilter(django_filters.FilterSet):
    class Meta:
        model = Group
        fields = ['course', 'mentor', 'active']

class GroupListCreateView(generics.ListAPIView):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = GroupFilter
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Group.objects.select_related('course', 'mentor__user').annotate(
            student_count=Count('student', distinct=True),
            course_group_count=Count('course__groups', distinct=True),
            course_student_count=Count('course__groups__student', distinct=True),
            course_teacher_count=Count('course__groups__mentor', distinct=True),
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(mentor=mentor)
        return qs

class GroupCreateView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupCreateSerializer
    permission_classes = [IsAdminOrTeacher]

    def perform_create(self, serializer):
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                raise PermissionDenied("Teacher profile not found")
            serializer.save(mentor=mentor)
            return
        serializer.save()

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.select_related('course', 'mentor')
    serializer_class = GroupSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [IsAdminOrTeacher()]

    def get_queryset(self):
        qs = Group.objects.select_related('course', 'mentor__user').annotate(
            student_count=Count('student', distinct=True),
            course_group_count=Count('course__groups', distinct=True),
            course_student_count=Count('course__groups__student', distinct=True),
            course_teacher_count=Count('course__groups__mentor', distinct=True),
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(mentor=mentor)
        return qs

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return GroupCreateSerializer
        return GroupSerializer

    def perform_update(self, serializer):
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                raise PermissionDenied("Teacher profile not found")
            serializer.save(mentor=mentor)
            return
        serializer.save()

class GroupStudentAddView(generics.GenericAPIView):
    permission_classes = [IsAdminOrTeacher]
    serializer_class = GroupStudentAddSerializer

    def post(self, request, pk, *args, **kwargs):
        group, error = _group_for_management(request.user, pk)
        if error:
            return error

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        student = Student.objects.select_related('user').prefetch_related('groups').get(
            pk=ser.validated_data['student_id']
        )

        if student.groups.filter(pk=group.pk).exists():
            return Response(
                {"detail": "Student bu guruhda allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not group.active:
            return Response(
                {"detail": "Faol bo'lmagan guruhga student qo'shib bo'lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student.groups.add(group)
        student = Student.objects.select_related('user').prefetch_related('groups').get(pk=student.pk)
        return Response(StudentSerializer(student, context=self.get_serializer_context()).data, status=status.HTTP_200_OK)

class GroupStudentRemoveView(generics.GenericAPIView):
    permission_classes = [IsAdminOrTeacher]
    serializer_class = GroupStudentRemoveSerializer

    def delete(self, request, pk, student_id, *args, **kwargs):
        group, error = _group_for_management(request.user, pk)
        if error:
            return error

        ser = self.get_serializer(data={'student_id': student_id})
        ser.is_valid(raise_exception=True)
        student = Student.objects.select_related('user').prefetch_related('groups').get(
            pk=ser.validated_data['student_id']
        )

        if not student.groups.filter(pk=group.pk).exists():
            return Response(
                {"detail": "Student bu guruhda mavjud emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student.groups.remove(group)
        student = Student.objects.select_related('user').prefetch_related('groups').get(pk=student.pk)
        return Response(
            {
                "detail": "Student guruhdan olib tashlandi.",
                "student": StudentSerializer(student, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_200_OK
        )

class StudentGroupTransferView(generics.GenericAPIView):
    permission_classes = [IsAdminOrTeacher]
    serializer_class = StudentGroupTransferSerializer

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        student = ser.validated_data['student']
        from_group = ser.validated_data['from_group']
        to_group = ser.validated_data['to_group']

        if not _can_transfer_student_between_groups(request.user, from_group, to_group):
            return Response(
                {"detail": "Teacher faqat o'z guruhlari orasida studentni ko'chira oladi."},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            locked_student = Student.objects.select_for_update().get(pk=student.pk)
            if not locked_student.groups.filter(pk=from_group.pk).exists():
                return Response(
                    {"detail": "Student bu guruhda mavjud emas."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if locked_student.groups.filter(pk=to_group.pk).exists():
                return Response(
                    {"detail": "Student yangi guruhda allaqachon mavjud."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            locked_student.groups.remove(from_group)
            locked_student.groups.add(to_group)
            transfer_log = StudentGroupTransferLog.objects.create(
                student=locked_student,
                from_group=from_group,
                to_group=to_group,
                moved_by=request.user,
                note=ser.validated_data.get('note') or None,
            )

        transfer_log = (
            StudentGroupTransferLog.objects
            .select_related(
                'student__user',
                'from_group__course',
                'from_group__mentor__user',
                'to_group__course',
                'to_group__mentor__user',
                'moved_by',
            )
            .prefetch_related('student__groups')
            .get(pk=transfer_log.pk)
        )
        return Response(
            StudentGroupTransferLogSerializer(transfer_log, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK
        )

class GivePointFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = GivePoint
        fields = ['student', 'group', 'mentor', 'date', 'point_type', 'date_from', 'date_to']

class GivePointListCreateView(generics.ListCreateAPIView):
    serializer_class = GivePointSerializer
    permission_classes = [IsAdminOrTeacher]
    filterset_class = GivePointFilter
    ordering_fields = ['id', 'date', 'created_at', 'amount']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        qs = GivePoint.objects.select_related(
            'mentor__user', 'student__user', 'point_type', 'group'
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(mentor=mentor, group__mentor=mentor)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                raise PermissionDenied("Teacher profile not found")
            serializer.save(mentor=mentor)
            return
        serializer.save()

class GivePointDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GivePointSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_queryset(self):
        qs = GivePoint.objects.select_related(
            'mentor__user', 'student__user', 'point_type', 'group'
        )
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(mentor=mentor, group__mentor=mentor)
        return qs

    def perform_update(self, serializer):
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                raise PermissionDenied("Teacher profile not found")
            serializer.save(mentor=mentor)
            return
        serializer.save()

class BookFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = ['student', 'status']

class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.select_related('student__user')
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = BookFilter
    search_fields = ['title', 'author']
    ordering_fields = ['id', 'title', 'start_date', 'end_date']
    ordering = ['-start_date']

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related('student__user')
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class NewsFilter(django_filters.FilterSet):
    class Meta:
        model = New
        fields = ['pin']

class NewsListCreateView(generics.ListAPIView):
    queryset = New.objects.select_related('user')
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = NewsFilter
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title', 'created_at']
    ordering = ['-pin', '-created_at']

class NewCreateView(generics.CreateAPIView):
    queryset = New.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NewsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = New.objects.select_related('user')
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class AuctionFilter(django_filters.FilterSet):
    class Meta:
        model = Auction
        fields = ['is_active']

class AuctionListCreateView(generics.ListCreateAPIView):
    queryset = Auction.objects.prefetch_related('products')
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AuctionFilter
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'data', 'time']
    ordering = ['-data']

class AuctionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.prefetch_related('products')
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = ['auction']

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('auction')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'point_cost', 'amount']
    ordering = ['id']

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('auction')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class GetMeView(generics.RetrieveAPIView):
    serializer_class = GetMeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class AssessmentTableView(generics.RetrieveAPIView):
    permission_classes = [IsTeacher]
    queryset = Group.objects.select_related("course", "mentor")
    lookup_field = "pk"

    def retrieve(self, request, *args, **kwargs):
        group: Group = self.get_object()

        mentor = _get_request_mentor(request.user)
        if not mentor:
            return Response({"detail": "Teacher profile not found"}, status=status.HTTP_403_FORBIDDEN)
        if group.mentor_id != mentor.id:
            return Response({"detail": "Group not found or not yours"}, status=status.HTTP_404_NOT_FOUND)

        d = request.query_params.get("date")  # YYYY-MM-DD
        the_date = timezone.localdate()
        if d:
            try:
                the_date = dt_date.fromisoformat(d)
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        point_types = list(PointType.objects.all().order_by("id"))

        students = (
            Student.objects
            .filter(groups=group)
            .select_related("user")
            .order_by("user__username")
        )

        givepoints = (
            GivePoint.objects
            .filter(group=group, date=the_date, student__in=students)
            .select_related("point_type", "student", "student__user")
        )
        points_map = {}
        for gp in givepoints:
            points_map.setdefault(gp.student_id, {})[gp.point_type_id] = gp.amount

        rows = []
        for st in students:
            st_points = points_map.get(st.id, {})
            cols = []
            total = 0

            for pt in point_types:
                amt = int(st_points.get(pt.id, 0))
                cols.append({
                    "point_type_id": pt.id,
                    "name": pt.name,
                    "max_point": pt.max_point,
                    "is_manual": pt.is_manual,
                    "amount": amt,
                })
                total += amt

            full_name = f"{st.first_name or ''} {st.last_name or ''}".strip() or st.user.username

            rows.append({
                "student_id": st.id,
                "username": st.user.username,
                "full_name": full_name,
                "image": st.image.url if st.image else None,
                "points": cols,
                "total": total,
            })

        return Response({
            "group": {
                "id": group.id,
                "name": group.name,
                "course": group.course.name,
            },
            "today": {
                "date": the_date.isoformat(),
                "weekday": WEEKDAY_UZ[the_date.weekday()],
            },
            "lesson_days": [DAYKEY_UZ.get(x, x) for x in (group.lesson_days or [])],
            "point_types": PointTypeSerializer(point_types, many=True).data,
            "rows": rows,
        })

class AttendanceTableView(generics.RetrieveAPIView):
    permission_classes = [IsAdminOrTeacher]
    queryset = Group.objects.select_related("course", "mentor__user")
    lookup_field = "pk"

    def retrieve(self, request, *args, **kwargs):
        group: Group = self.get_object()
        if not _can_manage_group(request.user, group):
            return Response({"detail": "Group not found or not yours"}, status=status.HTTP_404_NOT_FOUND)

        d = request.query_params.get("date")
        the_date = timezone.localdate()
        if d:
            try:
                the_date = dt_date.fromisoformat(d)
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        students = (
            Student.objects
            .filter(groups=group)
            .select_related("user")
            .order_by("user__username")
        )
        attendance_map = {
            record.student_id: record
            for record in Attendance.objects.filter(group=group, date=the_date, student__in=students)
        }

        rows = []
        for student in students:
            record = attendance_map.get(student.id)
            rows.append({
                "student_id": student.id,
                "username": student.user.username,
                "full_name": f"{student.first_name or ''} {student.last_name or ''}".strip() or student.user.username,
                "image": student.image.url if student.image else None,
                "attendance": {
                    "id": record.id if record else None,
                    "status": record.status if record else None,
                    "note": record.note if record else None,
                    "updated_at": record.updated_at if record else None,
                },
            })

        return Response({
            "group": {
                "id": group.id,
                "name": group.name,
                "course": group.course.name,
            },
            "date": {
                "value": the_date.isoformat(),
                "weekday": WEEKDAY_UZ[the_date.weekday()],
            },
            "lesson_days": [DAYKEY_UZ.get(x, x) for x in (group.lesson_days or [])],
            "statuses": [
                {"value": value, "label": label}
                for value, label in Attendance.STATUS_CHOICES
            ],
            "rows": rows,
        })

class AttendanceBulkSaveView(generics.CreateAPIView):
    permission_classes = [IsAdminOrTeacher]
    serializer_class = AttendanceBulkSaveSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        group, error = _group_for_management(request.user, ser.validated_data["group_id"])
        if error:
            return error

        mentor = group.mentor
        the_date = ser.validated_data["date"]
        items = ser.validated_data["items"]
        student_ids = {item["student_id"] for item in items}
        students_in_group = set(
            Student.objects
            .filter(groups=group, id__in=student_ids)
            .values_list("id", flat=True)
        )

        missing = sorted(student_ids - students_in_group)
        if missing:
            return Response(
                {
                    "detail": "Davomat faqat guruhdagi studentlar uchun olinadi.",
                    "student_ids": missing,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_ids = []
        with transaction.atomic():
            for item in items:
                obj, _ = Attendance.objects.update_or_create(
                    group=group,
                    student_id=item["student_id"],
                    date=the_date,
                    defaults={
                        "mentor": mentor,
                        "status": item["status"],
                        "note": item.get("note") or None,
                    },
                )
                saved_ids.append(obj.id)

        records = (
            Attendance.objects
            .filter(id__in=saved_ids)
            .select_related("student__user", "group", "mentor__user")
            .order_by("student__user__username")
        )
        return Response(
            {
                "saved": len(saved_ids),
                "date": the_date.isoformat(),
                "records": AttendanceSerializer(records, many=True, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_200_OK
        )

class AssessmentBulkSaveView(generics.CreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = BulkSaveSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        group_id = ser.validated_data["group_id"]
        the_date = ser.validated_data["date"]
        items = ser.validated_data["items"]

        mentor = _get_request_mentor(request.user)
        if not mentor:
            return Response({"detail": "Teacher profile not found"}, status=status.HTTP_403_FORBIDDEN)

        group = (
            Group.objects
            .filter(pk=group_id, mentor=mentor)
            .select_related("course", "mentor")
            .first()
        )
        if not group:
            return Response({"detail": "Group not found or not yours"}, status=status.HTTP_404_NOT_FOUND)

        pt_map = {pt.id: pt for pt in PointType.objects.all()}

        student_ids = {i["student_id"] for i in items}
        students_in_group = set(
            Student.objects
            .filter(groups=group, id__in=student_ids)
            .values_list("id", flat=True)
        )

        saved = 0
        errors = []

        for i in items:
            sid = i["student_id"]
            ptid = i["point_type_id"]
            amt = int(i["amount"])

            if sid not in students_in_group:
                errors.append({"student_id": sid, "detail": "Student not in this group"})
                continue

            pt = pt_map.get(ptid)
            if not pt:
                errors.append({"point_type_id": ptid, "detail": "PointType not found"})
                continue

            if amt > pt.max_point:
                errors.append({"student_id": sid, "point_type_id": ptid, "detail": f"Max {pt.max_point}"})
                continue

            try:
                obj, created = GivePoint.objects.get_or_create(
                    mentor=mentor,
                    student_id=sid,
                    group=group,
                    point_type_id=ptid,
                    date=the_date,
                    defaults={"amount": amt},
                )
                if not created:
                    obj.amount = amt
                    obj.save()
                saved += 1
            except Exception as e:
                errors.append({"student_id": sid, "point_type_id": ptid, "detail": str(e)})

        return Response({"saved": saved, "errors": errors}, status=status.HTTP_200_OK)

class AssessmentBulkUpdateView(generics.UpdateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = BulkUpdateSerializer

    def update(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        items = ser.validated_data["items"]

        mentor = _get_request_mentor(request.user)
        if not mentor:
            return Response({"detail": "Teacher profile not found"}, status=status.HTTP_403_FORBIDDEN)

        givepoint_ids = [i["givepoint_id"] for i in items]
        givepoints = {
            gp.id: gp
            for gp in GivePoint.objects
            .select_related("point_type", "student")
            .filter(id__in=givepoint_ids, mentor=mentor)
        }

        updated = 0
        errors = []

        with transaction.atomic():
            mentor_locked = Mentor.objects.select_for_update().get(pk=mentor.pk)

            for i in items:
                gp = givepoints.get(i["givepoint_id"])
                if not gp:
                    errors.append({"givepoint_id": i["givepoint_id"], "detail": "Topilmadi yoki sizniki emas"})
                    continue

                new_amt = i["amount"]
                old_amt = gp.amount
                delta = new_amt - old_amt

                if new_amt > gp.point_type.max_point:
                    errors.append({
                        "givepoint_id": gp.id,
                        "detail": f"Maksimal ball: {gp.point_type.max_point}"
                    })
                    continue

                if delta > mentor_locked.point_limit:
                    errors.append({
                        "givepoint_id": gp.id,
                        "detail": f"Mentor limitida yetarli ball yo'q (mavjud: {mentor_locked.point_limit})"
                    })
                    continue

                GivePoint.objects.filter(pk=gp.id).update(amount=new_amt)
                Student.objects.filter(pk=gp.student_id).update(point=F("point") + delta)
                mentor_locked.point_limit -= delta
                updated += 1

            Mentor.objects.filter(pk=mentor.pk).update(point_limit=mentor_locked.point_limit)

        return Response({"updated": updated, "errors": errors}, status=status.HTTP_200_OK)


class CoinHistoryFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = GivePoint
        fields = ['student', 'group', 'date_from', 'date_to']

class CoinHistoryView(generics.ListAPIView):
    serializer_class = CoinHistorySerializer
    permission_classes = [IsAuthenticated]
    filterset_class = CoinHistoryFilter
    ordering_fields = ['id', 'date', 'created_at', 'amount']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        qs = GivePoint.objects.select_related(
            'mentor__user', 'student__user', 'group', 'point_type'
        ).order_by('-date', '-created_at')
        if self.request.user.role == 'teacher':
            mentor = _get_request_mentor(self.request.user)
            if not mentor:
                return qs.none()
            return qs.filter(mentor=mentor, group__mentor=mentor)
        if self.request.user.role == 'student':
            return qs.filter(student__user=self.request.user)
        return qs

class ActiveGroupsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        groups = (
            Group.objects
            .select_related('course', 'mentor__user')
            .annotate(
                total_coins=Sum('givepoint__amount'),
                student_count=Count('student', distinct=True),
                course_group_count=Count('course__groups', distinct=True),
                course_student_count=Count('course__groups__student', distinct=True),
                course_teacher_count=Count('course__groups__mentor', distinct=True),
            )
            .order_by('-total_coins')
        )

        page = self.paginate_queryset(groups)
        groups_page = page if page is not None else groups
        prefetch_related_objects(
            groups_page,
            Prefetch('student_set', queryset=Student.objects.select_related('user').order_by('user__username'))
        )

        data = [
            {
                'id': g.id,
                'name': g.name,
                'student_count': g.student_count,
                'total_coins': g.total_coins or 0,
                'mentor': {
                    'id': g.mentor.id,
                    'username': g.mentor.user.username,
                } if g.mentor else None,
                'students': [
                    {
                        'id': s.id,
                        'full_name': f"{s.first_name or ''} {s.last_name or ''}".strip() or s.user.username,
                        'point': s.point,
                        'image': s.image.url if s.image else None,
                    }
                    for s in g.student_set.all()
                ],
            }
            for g in groups_page
        ]

        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

class LeaderboardFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = ['groups', 'groups__course']

class LeaderboardView(generics.ListAPIView):
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = LeaderboardFilter
    search_fields = ['user__username', 'first_name', 'last_name']
    ordering_fields = ['id', 'point']
    ordering = ['-point']

    def get_queryset(self):
        last_coin = GivePoint.objects.filter(student=OuterRef('pk')).order_by('-created_at')
        return (
            Student.objects
            .select_related('user')
            .prefetch_related('groups')
            .annotate(
                last_coin_amount=Subquery(last_coin.values('amount')[:1]),
                last_coin_point_type=Subquery(last_coin.values('point_type__name')[:1]),
                last_coin_date=Subquery(last_coin.values('date')[:1]),
            )
            .order_by('-point')
        )

class PointTypeFilter(django_filters.FilterSet):
    class Meta:
        model = PointType
        fields = ['is_manual']

class PointTypeListCreateView(generics.ListCreateAPIView):
    queryset = PointType.objects.all().order_by('id')
    serializer_class = PointTypeSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PointTypeFilter
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'max_point']
    ordering = ['id']

class PointTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PointType.objects.all()
    serializer_class = PointTypeSerializer
    permission_classes = [IsAuthenticated]

class AdminFilter(django_filters.FilterSet):
    class Meta:
        model = Admin
        fields = ['is_active']

class AdminListView(generics.ListAPIView):
    queryset = Admin.objects.select_related('user')
    serializer_class = AdminSerializer
    permission_classes = [IsAdmin]
    filterset_class = AdminFilter
    search_fields = ['name', 'user__username', 'user__email']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']

class AdminCreateView(generics.CreateAPIView):
    queryset = Admin.objects.select_related('user')
    serializer_class = AdminCreateSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Admin.objects.select_related('user')
    serializer_class = AdminSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AdminUpdateSerializer
        return AdminSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user_id == request.user.id:
            return Response(
                {"detail": "O'zingizning admin profilingizni o'chira olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = instance.user
        self.perform_destroy(instance)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
