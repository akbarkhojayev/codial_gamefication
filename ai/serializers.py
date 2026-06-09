from rest_framework import serializers
from ai.models import QueryLog


class QueryLogSerializer(serializers.ModelSerializer):
    """
    QueryLog serializer
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = QueryLog
        fields = ['id', 'user', 'user_username', 'question', 'query_type', 'result_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']


class AnalyticsRequestSerializer(serializers.Serializer):
    """
    Analytics request serializer
    """
    question = serializers.CharField(
        max_length=5000,
        min_length=3,
        help_text="Savol 3 dan 5000 belgigacha bo'lishi kerak"
    )


class SearchRequestSerializer(serializers.Serializer):
    """
    Search request serializer
    """
    search = serializers.CharField(
        max_length=200,
        min_length=2,
        help_text="Qidiruv 2 dan 200 belgigacha bo'lishi kerak"
    )


class AnalyticsResponseSerializer(serializers.Serializer):
    """
    Analytics response serializer
    """
    question = serializers.CharField()
    analysis = serializers.JSONField()
    type = serializers.CharField()
    message = serializers.CharField()
    count = serializers.IntegerField()


class SearchResponseSerializer(serializers.Serializer):
    """
    Search response serializer
    """
    type = serializers.CharField()
    data = serializers.JSONField()
    message = serializers.CharField()
    count = serializers.IntegerField()
