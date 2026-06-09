from rest_framework import generics
from django.db import transaction
from django.db.models import F
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import *
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
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

class UserFilter(django_filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = ['role']

class UserListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
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
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = CourseFilter
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']
    ordering = ['id']

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class MentorFilter(django_filters.FilterSet):
    class Meta:
        model = Mentor
        fields = ['direction']

class MentorListCreateView(generics.ListAPIView):
    queryset = Mentor.objects.select_related('user')
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MentorFilter
    search_fields = ['user__username', 'user__email', 'direction']
    ordering_fields = ['id', 'user__username']
    ordering = ['id']

class MentorCreateView(generics.CreateAPIView):
    queryset = Mentor.objects.all()
    serializer_class = MentorCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class MentorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mentor.objects.select_related('user')
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return MentorUpdateSerializer
        return MentorSerializer

class StudentCreateView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class StudentFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = ['groups']

class StudentListView(generics.ListAPIView):
    queryset = Student.objects.select_related('user').prefetch_related('groups')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = StudentFilter
    search_fields = ['user__username', 'user__email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['id', 'user__username', 'point']
    ordering = ['id']

class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related('user').prefetch_related('groups')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class GroupFilter(django_filters.FilterSet):
    class Meta:
        model = Group
        fields = ['course', 'mentor', 'active']

class GroupListCreateView(generics.ListAPIView):
    queryset = Group.objects.select_related('course', 'mentor')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = GroupFilter
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['-created_at']

class GroupCreateView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupCreateSerializer
    permission_classes = [IsAuthenticated]

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.select_related('course', 'mentor')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

class GivePointFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = GivePoint
        fields = ['student', 'group', 'mentor', 'date', 'point_type', 'date_from', 'date_to']

class GivePointListCreateView(generics.ListCreateAPIView):
    serializer_class = GivePointSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = GivePointFilter
    ordering_fields = ['id', 'date', 'created_at', 'amount']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        return GivePoint.objects.select_related(
            'mentor', 'student', 'point_type', 'group'
        )

class GivePointDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GivePoint.objects.select_related(
        'mentor', 'student', 'point_type'
    )
    serializer_class = GivePointSerializer
    permission_classes = [IsAuthenticated]

class BookFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = ['student', 'status']

class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = BookFilter
    search_fields = ['title', 'author']
    ordering_fields = ['id', 'title', 'start_date', 'end_date']
    ordering = ['-start_date']

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class NewsFilter(django_filters.FilterSet):
    class Meta:
        model = New
        fields = ['pin']

class NewsListCreateView(generics.ListAPIView):
    queryset = New.objects.all()
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
    queryset = New.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class AuctionFilter(django_filters.FilterSet):
    class Meta:
        model = Auction
        fields = ['is_active']

class AuctionListCreateView(generics.ListCreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AuctionFilter
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'data', 'time']
    ordering = ['-data']

class AuctionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.all()
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

        mentor = Mentor.objects.select_related("user").get(user=request.user)
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

class AssessmentBulkSaveView(generics.CreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = BulkSaveSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        group_id = ser.validated_data["group_id"]
        the_date = ser.validated_data["date"]
        items = ser.validated_data["items"]

        mentor = Mentor.objects.select_related("user").get(user=request.user)

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

        mentor = Mentor.objects.select_related("user").get(user=request.user)

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
        return GivePoint.objects.select_related(
            'mentor__user', 'student', 'group', 'point_type'
        ).order_by('-date', '-created_at')

class ActiveGroupsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        from django.db.models import Sum, Count

        groups = (
            Group.objects
            .select_related('mentor__user')
            .prefetch_related('student_set__user')
            .annotate(
                total_coins=Sum('givepoint__amount'),
                student_count=Count('student', distinct=True),
            )
            .order_by('-total_coins')
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
            for g in groups
        ]

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
        return Student.objects.select_related('user').prefetch_related('groups').order_by('-point')

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
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AdminFilter
    search_fields = ['name', 'user__username', 'user__email']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']

class AdminCreateView(generics.CreateAPIView):
    queryset = Admin.objects.all()
    serializer_class = AdminCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated]