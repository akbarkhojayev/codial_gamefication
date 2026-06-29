from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import token_refresh
from django.conf import settings
from django.conf.urls.static import static
from main.views import *

schema_view = get_schema_view(
  openapi.Info(
     title="Codial Academy API",
     default_version='v1',
     description="Codial Academy Gamification API - talabalar, mentorlar, kurslar, guruhlar va davomat boshqaruvi",
     terms_of_service="https://www.google.com/policies/terms/",
     contact=openapi.Contact(email="contact@codial.local"),
     license=openapi.License(name="MIT License"),
  ),
  public=True,
  permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('token/', CustomTokenObtainPairView.as_view() ),
    path('token/refresh/', token_refresh ),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

urlpatterns += [

    path('get/me/', GetMeView.as_view()),
    path('users/', UserListView.as_view()),
    path('courses/', CourseListCreateView.as_view()),
    path('courses/<int:pk>/', CourseDetailView.as_view()),
    path('mentors/', MentorListCreateView.as_view()),
    path('mentors/add/',MentorCreateView.as_view()),
    path('mentors/<int:pk>/', MentorDetailView.as_view()),
    path('students/', StudentListView.as_view()),
    path('students/add/', StudentCreateView.as_view()),
    path('students/transfer/', StudentGroupTransferView.as_view()),
    path('students/<int:pk>/', StudentDetailView.as_view()),
    path('groups/', GroupListCreateView.as_view()),
    path('groups/add/', GroupCreateView.as_view()),
    path('groups/<int:pk>/students/add/', GroupStudentAddView.as_view()),
    path('groups/<int:pk>/students/<int:student_id>/remove/', GroupStudentRemoveView.as_view()),
    path('groups/<int:pk>/', GroupDetailView.as_view()),
    path('points/', GivePointListCreateView.as_view()),
    path('points/<int:pk>/', GivePointDetailView.as_view()),
    path('books/', BookListCreateView.as_view()),
    path('books/<int:pk>/', BookDetailView.as_view()),
    path('news/', NewsListCreateView.as_view()),
    path('news/<int:pk>/', NewsDetailView.as_view()),
    path('news/add/',NewCreateView.as_view()),
    path('auctions/', AuctionListCreateView.as_view()),
    path('auctions/<int:pk>/', AuctionDetailView.as_view()),
    path('pointtypes/', PointTypeListCreateView.as_view()),
    path('pointtypes/<int:pk>/', PointTypeDetailView.as_view()),
    path('admins/', AdminListView.as_view()),
    path('admins/add/', AdminCreateView.as_view()),
    path('admins/<int:pk>/', AdminDetailView.as_view()),
    path('leaderboard/', LeaderboardView.as_view()),
    path('coin-history/', CoinHistoryView.as_view()),
    path('active-groups/', ActiveGroupsView.as_view()),
    path('products/', ProductListCreateView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),
    path("api/teacher/assessment/<int:pk>/", AssessmentTableView.as_view(), name="api_teacher_assessment_retrieve"),
    path("api/teacher/assessment/save/", AssessmentBulkSaveView.as_view()),
    path("api/teacher/assessment/update/", AssessmentBulkUpdateView.as_view()),
    path("api/teacher/attendance/<int:pk>/", AttendanceTableView.as_view(), name="api_teacher_attendance_retrieve"),
    path("api/teacher/attendance/save/", AttendanceBulkSaveView.as_view()),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
