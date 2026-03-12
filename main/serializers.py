from rest_framework import serializers
from django.db import transaction
from .models import (
    UserProfile, Course, Mentor, Group, Student,
    PointType, GivePoint, Book, New, Auction, Product
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class MentorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = '__all__'

    def validate_user(self, value):
        if value.role != 'teacher':
            raise serializers.ValidationError("Bu user teacher bo‘lishi kerak.")
        if Mentor.objects.filter(user=value).exists():
            raise serializers.ValidationError("Bu user uchun mentor allaqachon yaratilgan.")
        return value


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


class GroupCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.PrimaryKeyRelatedField(
        source='course',
        queryset=Course.objects.all(),
        write_only=True
    )
    mentor_id = serializers.PrimaryKeyRelatedField(
        source='mentor',
        queryset=Mentor.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    lesson_days = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'active',
            'created_at',
            'lesson_days',
            'course_id',
            'mentor_id',
        ]
        read_only_fields = ['id', 'created_at']


class StudentCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )

    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'user',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'image',
            'bio',
            'point',
            'birth_date',
            'phone_number',
            'groups',
        ]
        extra_kwargs = {
            'point': {'required': False},
        }

    def validate_username(self, value):
        if UserProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username allaqachon band.")
        return value

    def validate_email(self, value):
        if value and UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        username = validated_data.pop('username')
        email = validated_data.pop('email', '')
        password = validated_data.pop('password')

        with transaction.atomic():
            user = UserProfile.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='student'
            )

            student = Student.objects.create(
                user=user,
                **validated_data
            )

            if groups:
                student.groups.set(groups)

        return student


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

        if amount <= 0:
            raise serializers.ValidationError("Amount 0 dan katta bo‘lishi kerak.")

        if point_type and amount > point_type.max_point:
            raise serializers.ValidationError(
                {'amount': f"Bu point type uchun maksimal qiymat {point_type.max_point}"}
            )

        if amount > mentor.point_limit:
            raise serializers.ValidationError(
                {'amount': f"Mentorda faqat {mentor.point_limit} point qolgan"}
            )

        return data

    def create(self, validated_data):
        with transaction.atomic():
            give_point = GivePoint.objects.create(**validated_data)

            student = give_point.student
            mentor = give_point.mentor

            student.point += give_point.amount
            mentor.point_limit -= give_point.amount

            student.save(update_fields=['point'])
            mentor.save(update_fields=['point_limit'])

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


class GetMeSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    student = StudentSerializer(read_only=True, required=False, allow_null=True)
    mentor = MentorSerializer(read_only=True, required=False, allow_null=True)

    def to_representation(self, instance):
        user = instance

        data = {
            'user': UserSerializer(user, context=self.context).data,
            'student': None,
            'mentor': None,
        }

        if user.role == 'student':
            student = (
                Student.objects
                .select_related('user')
                .prefetch_related('groups__course', 'groups__mentor__user')
                .filter(user=user)
                .first()
            )
            if student:
                data['student'] = StudentSerializer(student, context=self.context).data

        elif user.role == 'teacher':
            mentor = (
                Mentor.objects
                .select_related('user')
                .filter(user=user)
                .first()
            )
            if mentor:
                data['mentor'] = MentorSerializer(mentor, context=self.context).data

        return data


class BulkPointItemSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    point_type_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class BulkSaveSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    date = serializers.DateField()
    items = BulkPointItemSerializer(many=True)

    def validate_group_id(self, value):
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday group mavjud emas.")
        return value

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Items bo‘sh bo‘lmasligi kerak.")
        return items