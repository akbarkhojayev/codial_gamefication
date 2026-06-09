import json
from typing import Any, Dict


class ResponseFormatter:
    """
    Format AI responses in consistent JSON structure
    """
    
    @staticmethod
    def format_success(data: Any, message: str = "Success") -> Dict:
        """Format successful response"""
        return {
            'status': 'success',
            'message': message,
            'data': data
        }
    
    @staticmethod
    def format_error(error: str, code: str = "ERROR") -> Dict:
        """Format error response"""
        return {
            'status': 'error',
            'code': code,
            'message': error
        }
    
    @staticmethod
    def format_analytics(analytics_data: Dict) -> Dict:
        """Format analytics data"""
        return ResponseFormatter.format_success(
            analytics_data,
            "Analytics retrieved successfully"
        )
    
    @staticmethod
    def format_conversation(question: str, answer: str) -> Dict:
        """Format conversation response"""
        return ResponseFormatter.format_success(
            {
                'question': question,
                'answer': answer
            },
            "Conversation saved successfully"
        )
    
    @staticmethod
    def parse_json_response(response: str) -> Dict:
        """Parse JSON response from AI"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return ResponseFormatter.format_error(
                "Invalid JSON response from AI",
                "PARSE_ERROR"
            )
