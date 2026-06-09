from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from ai.models import QueryLog
from ai.serializers import (
    QueryLogSerializer,
    AnalyticsRequestSerializer,
    AnalyticsResponseSerializer,
    SearchRequestSerializer,
    SearchResponseSerializer
)
from ai.services.query_analyzer import QueryAnalyzer
from ai.services.formatter import ResponseFormatter
from ai.services.claude_analyzer import analyze_with_claude


class HealthCheckView(APIView):
    """
    Django serverining holatini tekshirish
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Server healthy",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'django': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )
    def get(self, request):
        """
        Django serverining holatini tekshirish
        """
        return Response({
            'status': 'healthy',
            'django': {
                'connected': True,
                'version': '4.2.11'
            },
            'message': 'Server ishga tushgan'
        }, status=status.HTTP_200_OK)


class AnalyticsAPIView(generics.GenericAPIView):
    """
    Analytics API
    Savol tahlil qiladi va database'dan ma'lumot oladi
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsRequestSerializer
    
    @swagger_auto_schema(
        request_body=AnalyticsRequestSerializer,
        responses={
            200: AnalyticsResponseSerializer,
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def post(self, request):
        """
        Savol bilan analytics olish
        
        Misol:
        ```
        {
          "question": "Eng ko'p ball to'plagan talabalar kimlar?"
        }
        ```
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        
        try:
            analysis = analyze_with_claude(question)

            QueryLog.objects.create(
                user=request.user,
                question=question,
                query_type=analysis.get('query_type', 'all'),
                result_count=analysis.get('count', 0)
            )

            return Response(
                ResponseFormatter.format_success(
                    {
                        'question': question,
                        'type': analysis.get('type'),
                        'message': analysis.get('message'),
                        'count': analysis.get('count', 0),
                        'data': analysis.get('data'),
                    },
                    "Analytics retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                ResponseFormatter.format_error(str(e), "ANALYTICS_ERROR"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Analytics data"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def get(self, request):
        """
        Barcha analytics'ni olish
        """
        try:
            analysis = QueryAnalyzer.get_all_analytics()
            
            QueryLog.objects.create(
                user=request.user,
                question="Barcha analytics",
                query_type='all',
                result_count=analysis.get('count', 0)
            )
            
            return Response(
                ResponseFormatter.format_success(analysis),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                ResponseFormatter.format_error(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchAPIView(generics.GenericAPIView):
    """
    Qidiruv API
    Ism, kurs, guruh bo'yicha qidirish
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SearchRequestSerializer
    
    @swagger_auto_schema(
        request_body=SearchRequestSerializer,
        responses={
            200: SearchResponseSerializer,
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def post(self, request):
        """
        Qidiruv
        
        Misol:
        ```
        {
          "search": "Ali"
        }
        ```
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        search_term = serializer.validated_data['search']
        
        try:
            results = QueryAnalyzer.search_by_name(search_term)
            
            QueryLog.objects.create(
                user=request.user,
                question=f"Qidiruv: {search_term}",
                query_type='search',
                result_count=results.get('count', 0)
            )
            
            return Response(
                ResponseFormatter.format_success(
                    results,
                    "Qidiruv natijalari"
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                ResponseFormatter.format_error(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentAnalyticsView(generics.GenericAPIView):
    """
    Talabalar haqida analytics
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Talabalar statistikasi"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def get(self, request):
        """
        Talabalar statistikasi
        """
        analysis = QueryAnalyzer.get_student_analysis("top students")
        
        # Log qilish
        QueryLog.objects.create(
            user=request.user,
            question="Talabalar statistikasi",
            query_type='students',
            result_count=analysis.get('count', 0)
        )
        
        return Response(
            ResponseFormatter.format_success(analysis),
            status=status.HTTP_200_OK
        )


class CourseAnalyticsView(generics.GenericAPIView):
    """
    Kurslar haqida analytics
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Kurslar statistikasi"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def get(self, request):
        """
        Kurslar statistikasi
        """
        analysis = QueryAnalyzer.get_course_analysis("courses")
        
        # Log qilish
        QueryLog.objects.create(
            user=request.user,
            question="Kurslar statistikasi",
            query_type='courses',
            result_count=analysis.get('count', 0)
        )
        
        return Response(
            ResponseFormatter.format_success(analysis),
            status=status.HTTP_200_OK
        )


class GroupAnalyticsView(generics.GenericAPIView):
    """
    Guruhlar haqida analytics
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Guruhlar statistikasi"),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def get(self, request):
        """
        Guruhlar statistikasi
        """
        analysis = QueryAnalyzer.get_group_analysis("groups")
        
        # Log qilish
        QueryLog.objects.create(
            user=request.user,
            question="Guruhlar statistikasi",
            query_type='groups',
            result_count=analysis.get('count', 0)
        )
        
        return Response(
            ResponseFormatter.format_success(analysis),
            status=status.HTTP_200_OK
        )


class QueryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    QueryLog ViewSet
    Barcha so'rovlarni ko'rish
    """
    queryset = QueryLog.objects.all()
    serializer_class = QueryLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Foydalanuvchining o'z so'rovlarini ko'rish
        """
        return QueryLog.objects.filter(user=self.request.user).order_by('-created_at')
    
    @swagger_auto_schema(
        responses={
            200: QueryLogSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        """
        Barcha so'rovlarni ko'rish
        """
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        responses={
            200: QueryLogSerializer,
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Not found"),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Bitta so'rovni ko'rish
        """
        return super().retrieve(request, *args, **kwargs)
