import re
from typing import Any


class AIValidator:
    """
    Validators for AI inputs and outputs
    """
    
    @staticmethod
    def validate_question(question: str) -> bool:
        """Validate question format"""
        if not question or len(question) < 3:
            return False
        if len(question) > 5000:
            return False
        return True
    
    @staticmethod
    def validate_model_name(model_name: str) -> bool:
        """Validate model name"""
        valid_models = ['Student', 'Mentor', 'Group', 'Course', 'Book']
        return model_name in valid_models
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove potentially harmful characters
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
        return text.strip()
    
    @staticmethod
    def validate_json_response(data: Any) -> bool:
        """Validate JSON response structure"""
        if not isinstance(data, dict):
            return False
        
        required_keys = ['status', 'message']
        return all(key in data for key in required_keys)
