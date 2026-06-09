from django.conf import settings
from django.db import models


class QueryLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='query_logs'
    )
    
    question = models.TextField()
    
    query_type = models.CharField(max_length=50)
    
    result_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.query_type}"
