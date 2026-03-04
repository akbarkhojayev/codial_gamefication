from rest_framework import serializers
from django.db import transaction
from .models import (
    UserProfile, Course, Mentor, Group,
    Student, PointType, GivePoint,
    Book, New, Auction, Product
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'password', 'role']

    def create(self, validated_data):
        with transaction.atomic():
            user = UserProfile.objects.create_user(
                username=validated_data['username'],
                password=validated_data['password'],
                role=validated_data['role']
            )
            if user.role == "student":
                Student.objects.get_or_create(user=user)
            elif user.role == "teacher":
                Mentor.objects.get_or_create(user=user)

            return user

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        data['role'] = self.user.role

        return data

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class MentorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Mentor
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    mentor = MentorSerializer(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'

class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = '__all__'

class PointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointType
        fields = '__all__'

class GivePointSerializer(serializers.ModelSerializer):

    class Meta:
        model = GivePoint
        fields = '__all__'

    def validate(self, data):
        mentor = data['mentor']
        amount = data['amount']
        point_type = data.get('point_type')

        if point_type and amount > point_type.max_point:
            raise serializers.ValidationError(
                f"Max allowed for this type is {point_type.max_point}"
            )

        if amount > mentor.point_limit:
            raise serializers.ValidationError(
                f"Mentor has only {mentor.point_limit} points left"
            )

        return data

    def create(self, validated_data):
        with transaction.atomic():
            give_point = GivePoint.objects.create(**validated_data)

            student = give_point.student
            mentor = give_point.mentor

            student.point += give_point.amount
            mentor.point_limit -= give_point.amount

            student.save()
            mentor.save()

        return give_point

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = New
        fields = '__all__'
        read_only_fields = ['user']

class AuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'