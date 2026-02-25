from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView



class UserListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class UserCreateView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class MentorListCreateView(generics.ListCreateAPIView):
    queryset = Mentor.objects.select_related('user')
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]

class MentorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mentor.objects.select_related('user')
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]

class StudentCreateView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentCreateSerializer
    permission_classes = [IsAuthenticated]

class StudentListView(generics.ListAPIView):
    queryset = Student.objects.select_related('user').prefetch_related('groups')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related('user').prefetch_related('groups')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.select_related('course', 'mentor')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.select_related('course', 'mentor')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

class GivePointListCreateView(generics.ListCreateAPIView):
    queryset = GivePoint.objects.select_related(
        'mentor', 'student', 'point_type'
    )
    serializer_class = GivePointSerializer
    permission_classes = [IsAuthenticated]


class GivePointDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GivePoint.objects.select_related(
        'mentor', 'student', 'point_type'
    )
    serializer_class = GivePointSerializer
    permission_classes = [IsAuthenticated]

class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

class NewsListCreateView(generics.ListCreateAPIView):
    queryset = New.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]

class NewsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = New.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated]

class AuctionListCreateView(generics.ListCreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]

class AuctionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('auction')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('auction')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]