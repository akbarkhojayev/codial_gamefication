from datetime import datetime, timedelta
from django.utils import timezone


class DateUtils:
    """
    Utility functions for date operations
    """
    
    @staticmethod
    def get_today() -> datetime:
        """Get today's date"""
        return timezone.now().date()
    
    @staticmethod
    def get_week_ago() -> datetime:
        """Get date from one week ago"""
        return timezone.now().date() - timedelta(days=7)
    
    @staticmethod
    def get_month_ago() -> datetime:
        """Get date from one month ago"""
        return timezone.now().date() - timedelta(days=30)
    
    @staticmethod
    def get_year_ago() -> datetime:
        """Get date from one year ago"""
        return timezone.now().date() - timedelta(days=365)
    
    @staticmethod
    def format_date(date: datetime, format_str: str = "%Y-%m-%d") -> str:
        """Format date to string"""
        return date.strftime(format_str)
    
    @staticmethod
    def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
        """Parse date from string"""
        return datetime.strptime(date_str, format_str).date()
