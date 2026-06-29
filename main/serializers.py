from rest_framework import serializers
from django.db import transaction
from rest_framework.fields import SerializerMethodField
from .models import (
    UserProfile, Course, Mentor, Group, Student,
    PointType, GivePoint, Book, New, Auction, Product, Admin,
    Attendance, StudentGroupTransferLog
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Course, Student, Mentor, Group


def _attach_course_counts_from_group(group):
    course = getattr(group, 'course', None)
    if not course:
        return
    mapping = {
        'course_group_count': 'group_count',
        'course_student_count': 'student_count',
        'course_teacher_count': 'teacher_count',
    }
    for source, target in mapping.items():
        value = getattr(group, source, None)
        if value is not None:
            setattr(course, target, value)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data

class CourseSerializer(serializers.ModelSerializer):
    group_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'icon',
            'color',
            'description',
            'is_active',
            'group_count',
            'student_count',
            'teacher_count',
        ]

    def get_group_count(self, obj):
        value = getattr(obj, 'group_count', None)
        if value is not None:
            return value
        return Group.objects.filter(course=obj).count()

    def get_student_count(self, obj):
        value = getattr(obj, 'student_count', None)
        if value is not None:
            return value
        return Student.objects.filter(groups__course=obj).distinct().count()

    def get_teacher_count(self, obj):
        value = getattr(obj, 'teacher_count', None)
        if value is not None:
            return value
        return Mentor.objects.filter(groups__course=obj).distinct().count()


class MentorCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    user = UserSerializer(read_only=True)

    class Meta:
        model = Mentor
        fields = [
            'user',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'avatar',
            'bio',
            'direction',
            'point_limit',
        ]
        extra_kwargs = {
            'point_limit': {'required': False},
            'avatar': {'required': False},
            'bio': {'required': False},
            'direction': {'required': False},
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
        username = validated_data.pop('username')
        email = validated_data.pop('email', '')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        with transaction.atomic():
            user = UserProfile.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='teacher'
            )

            mentor = Mentor.objects.create(
                user=user,
                **validated_data
            )
        return mentor

class MentorMiniSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Mentor
        fields = ['id', 'user', 'point_limit']

class GroupForMentorSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'active',
            'created_at',
            'lesson_days',
            'course',
            'student_count',
        ]

    def get_student_count(self, obj):
        value = getattr(obj, 'student_count', None)
        if value is not None:
            return value
        return Student.objects.filter(groups=obj).count()

    def to_representation(self, instance):
        _attach_course_counts_from_group(instance)
        return super().to_representation(instance)

class MentorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    groups = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Mentor
        fields = [
            'id',
            'user',
            'bio',
            'avatar',
            'direction',
            'point_limit',
            'groups',
            'total_students',
        ]

    def get_groups(self, obj):
        groups = obj.groups.all()
        return GroupForMentorSerializer(groups, many=True, context=self.context).data

    def get_total_students(self, obj):
        value = getattr(obj, 'total_students_value', None)
        if value is not None:
            return value
        return Student.objects.filter(groups__mentor=obj).distinct().count()

class MentorUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Mentor
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'avatar',
            'direction',
            'point_limit',
        ]
        extra_kwargs = {
            'bio': {'required': False},
            'avatar': {'required': False},
            'direction': {'required': False},
            'point_limit': {'required': False},
        }

    def validate_username(self, value):
        user = self.instance.user
        if UserProfile.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Bu username allaqachon band.")
        return value

    def validate_email(self, value):
        if not value:
            return value
        user = self.instance.user
        if UserProfile.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value

    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', None)
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)

        with transaction.atomic():
            user = instance.user
            update_fields = []
            if username is not None:
                user.username = username
                update_fields.append('username')
            if email is not None:
                user.email = email
                update_fields.append('email')
            if first_name is not None:
                user.first_name = first_name
                update_fields.append('first_name')
            if last_name is not None:
                user.last_name = last_name
                update_fields.append('last_name')
            if update_fields:
                user.save(update_fields=update_fields)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return instance

class AdminSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)

    class Meta:
        model = Admin
        fields = [
            'id',
            'user',
            'username',
            'user_email',
            'is_staff',
            'name',
            'email',
            'description',
            'avatar',
            'is_active',
            'created_at',
        ]

class AdminCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    user = UserSerializer(read_only=True)

    class Meta:
        model = Admin
        fields = [
            'user',
            'username',
            'email',
            'password',
            'name',
            'description',
            'avatar',
            'is_active',
        ]
        extra_kwargs = {
            'is_active': {'required': False},
        }

    def validate_username(self, value):
        if UserProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username allaqachon band.")
        return value

    def validate_email(self, value):
        if value and UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name bo'sh bo'lishi mumkin emas.")
        return value

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email', '')
        password = validated_data.pop('password')

        with transaction.atomic():
            is_active = validated_data.get('is_active', True)
            user = UserProfile.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='admin',
                is_staff=True,
                is_active=is_active
            )

            admin = Admin.objects.create(
                user=user,
                email=email or None,
                **validated_data
            )

        return admin

class AdminUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, write_only=True, allow_blank=True)

    class Meta:
        model = Admin
        fields = [
            'username',
            'email',
            'password',
            'name',
            'description',
            'avatar',
            'is_active',
        ]
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'avatar': {'required': False},
            'is_active': {'required': False},
        }

    def validate_username(self, value):
        user = self.instance.user
        if UserProfile.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Bu username allaqachon band.")
        return value

    def validate_email(self, value):
        if not value:
            return value
        user = self.instance.user
        if UserProfile.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name bo'sh bo'lishi mumkin emas.")
        return value

    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)

        with transaction.atomic():
            user = instance.user
            user_update_fields = []

            if username is not None:
                user.username = username
                user_update_fields.append('username')
            if email is not None:
                user.email = email
                user_update_fields.append('email')
                instance.email = email or None
            if password:
                user.set_password(password)
                user_update_fields.append('password')
            if 'is_active' in validated_data:
                user.is_active = validated_data['is_active']
                user_update_fields.append('is_active')

            if not user.is_staff:
                user.is_staff = True
                user_update_fields.append('is_staff')
            if user.role != 'admin':
                user.role = 'admin'
                user_update_fields.append('role')

            if user_update_fields:
                user.save(update_fields=user_update_fields)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return instance

class GroupSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    mentor = MentorMiniSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'
    def get_student_count(self, obj):
        value = getattr(obj, 'student_count', None)
        if value is not None:
            return value
        return Student.objects.filter(groups=obj).count()

    def to_representation(self, instance):
        _attach_course_counts_from_group(instance)
        return super().to_representation(instance)

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

    VALID_LESSON_DAYS = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }

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
            'icon',
            'color',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Group name bo'sh bo'lishi mumkin emas.")
        return value.strip()

    def validate_lesson_days(self, value):
        invalid = [day for day in value if day not in self.VALID_LESSON_DAYS]
        if invalid:
            raise serializers.ValidationError(
                f"Noto'g'ri lesson_days qiymatlari: {', '.join(invalid)}"
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError("lesson_days ichida takrorlangan kunlar bo'lmasligi kerak.")
        return value

    def validate(self, attrs):
        course = attrs.get('course')
        mentor = attrs.get('mentor')

        if course and not course.is_active:
            raise serializers.ValidationError({"course_id": "Faol bo'lmagan kursga guruh ochib bo'lmaydi."})
        if mentor and mentor.user.role != 'teacher':
            raise serializers.ValidationError({"mentor_id": "Guruh mentori teacher role'da bo'lishi kerak."})
        return attrs

class StudentCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=True
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
            'birth_date',
            'phone_number',
            'groups',
        ]

    def validate_username(self, value):
        if UserProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username allaqachon band.")
        return value

    def validate_email(self, value):
        if value and UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value

    def validate_groups(self, value):
        if not value:
            raise serializers.ValidationError("Student kamida bitta guruhga biriktirilishi kerak.")
        inactive = [group.name for group in value if not group.active]
        if inactive:
            raise serializers.ValidationError(
                f"Faol bo'lmagan guruhlarga qo'shib bo'lmaydi: {', '.join(inactive)}"
            )
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'teacher':
            mentor = Mentor.objects.filter(user=request.user).first()
            if not mentor:
                raise serializers.ValidationError("Teacher profile topilmadi.")
            wrong_groups = [group.name for group in value if group.mentor_id != mentor.id]
            if wrong_groups:
                raise serializers.ValidationError(
                    f"Teacher faqat o'z guruhlariga student qo'sha oladi: {', '.join(wrong_groups)}"
                )
        return value

    def validate_first_name(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("First name bo'sh bo'lishi mumkin emas.")
        return value.strip() if value else value

    def validate_last_name(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("Last name bo'sh bo'lishi mumkin emas.")
        return value.strip() if value else value

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

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all()
    )
    book_count = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def validate_groups(self, value):
        request = self.context.get('request')
        if not value:
            raise serializers.ValidationError("Student kamida bitta guruhga biriktirilishi kerak.")
        inactive = [group.name for group in value if not group.active]
        if inactive:
            raise serializers.ValidationError(
                f"Faol bo'lmagan guruhlarga qo'shib bo'lmaydi: {', '.join(inactive)}"
            )
        if request and request.user.is_authenticated and request.user.role == 'teacher':
            mentor = Mentor.objects.filter(user=request.user).first()
            if not mentor:
                raise serializers.ValidationError("Teacher profile topilmadi.")
            wrong_groups = [group.name for group in value if group.mentor_id != mentor.id]
            if wrong_groups:
                raise serializers.ValidationError(
                    f"Teacher studentni faqat o'z guruhlariga biriktira oladi: {', '.join(wrong_groups)}"
                )
        return value

    def get_book_count(self, obj):
        value = getattr(obj, 'book_count_value', None)
        if value is not None:
            return value
        return Book.objects.filter(student=obj).count()

    def get_rank(self, obj):
        value = getattr(obj, 'student_rank', None)
        if value is not None:
            return value
        return Student.objects.filter(point__gt=obj.point).count() + 1

class GroupStudentAddSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()

    def validate_student_id(self, value):
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday student mavjud emas.")
        return value


class GroupStudentRemoveSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()

    def validate_student_id(self, value):
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday student mavjud emas.")
        return value

class StudentGroupTransferSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    from_group_id = serializers.IntegerField()
    to_group_id = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        student = Student.objects.filter(id=attrs['student_id']).first()
        from_group = Group.objects.filter(id=attrs['from_group_id']).first()
        to_group = Group.objects.filter(id=attrs['to_group_id']).first()

        errors = {}
        if not student:
            errors['student_id'] = "Bunday student mavjud emas."
        if not from_group:
            errors['from_group_id'] = "Bunday guruh mavjud emas."
        if not to_group:
            errors['to_group_id'] = "Bunday guruh mavjud emas."
        if errors:
            raise serializers.ValidationError(errors)

        if from_group.id == to_group.id:
            raise serializers.ValidationError({"to_group_id": "Ko'chirish uchun boshqa guruh tanlang."})
        if not to_group.active:
            raise serializers.ValidationError({"to_group_id": "Faol bo'lmagan guruhga ko'chirib bo'lmaydi."})
        if not student.groups.filter(id=from_group.id).exists():
            raise serializers.ValidationError({"from_group_id": "Student bu guruhda mavjud emas."})
        if student.groups.filter(id=to_group.id).exists():
            raise serializers.ValidationError({"to_group_id": "Student bu guruhda allaqachon mavjud."})

        attrs['student'] = student
        attrs['from_group'] = from_group
        attrs['to_group'] = to_group
        return attrs

class AttendanceItemSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class AttendanceBulkSaveSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    date = serializers.DateField()
    items = AttendanceItemSerializer(many=True)

    def validate_group_id(self, value):
        if not Group.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday guruh mavjud emas.")
        return value

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Davomat ro'yxati bo'sh bo'lmasligi kerak.")

        seen = set()
        duplicates = []
        for item in items:
            student_id = item['student_id']
            if student_id in seen:
                duplicates.append(student_id)
            seen.add(student_id)
        if duplicates:
            raise serializers.ValidationError(
                f"Bir student bir so'rovda takrorlanmasligi kerak: {sorted(set(duplicates))}"
            )
        return items

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    username = serializers.CharField(source='student.user.username', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'student',
            'student_name',
            'username',
            'group',
            'group_name',
            'mentor',
            'date',
            'status',
            'note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'mentor', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name or ''} {obj.student.last_name or ''}".strip() or obj.student.user.username

class StudentGroupTransferLogSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    from_group = GroupSerializer(read_only=True)
    to_group = GroupSerializer(read_only=True)
    moved_by = UserSerializer(read_only=True)

    class Meta:
        model = StudentGroupTransferLog
        fields = ['id', 'student', 'from_group', 'to_group', 'moved_by', 'note', 'created_at']

class GivePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GivePoint
        fields = '__all__'
        extra_kwargs = {
            'mentor': {'required': False},
        }

    def validate(self, data):
        request = self.context.get('request')
        instance = getattr(self, 'instance', None)

        mentor = data.get('mentor') or (instance.mentor if instance else None)
        student = data.get('student') or (instance.student if instance else None)
        group = data.get('group') or (instance.group if instance else None)
        point_type = data.get('point_type') or (instance.point_type if instance else None)
        amount = data.get('amount', instance.amount if instance else None)

        if request and request.user.is_authenticated and request.user.role == 'teacher':
            mentor = Mentor.objects.filter(user=request.user).first()
            if not mentor:
                raise serializers.ValidationError("Teacher profile topilmadi.")
            data['mentor'] = mentor

        if not mentor:
            raise serializers.ValidationError({"mentor": "Mentor majburiy."})
        if not student:
            raise serializers.ValidationError({"student": "Student majburiy."})
        if not group:
            raise serializers.ValidationError({"group": "Group majburiy."})
        if not point_type:
            raise serializers.ValidationError({"point_type": "Point type majburiy."})
        if amount is None:
            raise serializers.ValidationError({"amount": "Amount majburiy."})

        if amount <= 0:
            raise serializers.ValidationError("Amount 0 dan katta bo‘lishi kerak.")

        if amount > point_type.max_point:
            raise serializers.ValidationError(
                {'amount': f"Bu point type uchun maksimal qiymat {point_type.max_point}"}
            )

        if request and request.user.is_authenticated and request.user.role == 'teacher':
            if group.mentor_id != mentor.id:
                raise serializers.ValidationError({"group": "Teacher faqat o'z guruhiga point bera oladi."})

        if not student.groups.filter(pk=group.pk).exists():
            raise serializers.ValidationError({"student": "Student tanlangan guruhda mavjud emas."})

        required_limit = amount
        if instance:
            required_limit = amount - instance.amount

        if required_limit > mentor.point_limit:
            raise serializers.ValidationError(
                {'amount': f"Mentorda faqat {mentor.point_limit} point qolgan"}
            )

        return data

    def create(self, validated_data):
        with transaction.atomic():
            give_point = GivePoint.objects.create(**validated_data)
        return give_point

class NewsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = New
        fields = '__all__'
        read_only_fields = ['user']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class AuctionSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Auction
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
    amount = serializers.IntegerField(min_value=0)

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

class BulkUpdateItemSerializer(serializers.Serializer):
    givepoint_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=0)

class BulkUpdateSerializer(serializers.Serializer):
    items = BulkUpdateItemSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Items bo'sh bo'lmasligi kerak.")
        return items

class CoinHistorySerializer(serializers.ModelSerializer):
    point_type_name = serializers.CharField(source='point_type.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    mentor_name = serializers.CharField(source='mentor.user.username', read_only=True)

    class Meta:
        model = GivePoint
        fields = ['id', 'student', 'group_name', 'mentor_name', 'point_type_name', 'amount', 'description', 'date', 'created_at']

class LeaderboardSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    last_coin = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'user', 'full_name', 'image', 'point', 'groups', 'last_coin']

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.user.username

    def get_groups(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]

    def get_last_coin(self, obj):
        amount = getattr(obj, 'last_coin_amount', None)
        if amount is not None:
            return {
                'amount': amount,
                'point_type': getattr(obj, 'last_coin_point_type', None),
                'date': getattr(obj, 'last_coin_date', None),
            }
        gp = GivePoint.objects.filter(student=obj).order_by('-created_at').first()
        if not gp:
            return None
        return {
            'amount': gp.amount,
            'point_type': gp.point_type.name,
            'date': gp.date,
        }

class PointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointType
        fields = '__all__'

    def validate_max_point(self, value):
        if value < 0:
            raise serializers.ValidationError("max_point manfiy bo‘lishi mumkin emas.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name bo‘sh bo‘lishi mumkin emas.")
        return value
