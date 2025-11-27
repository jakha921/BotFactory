"""
Form builder utilities for generating dynamic forms from JSON configuration.
"""
from typing import Dict, Any, List, Optional
from aiogram.fsm.state import State, StatesGroup


def parse_form_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse form configuration and validate structure.
    
    Args:
        config: Form configuration dict with 'steps' field
        
    Returns:
        Parsed and validated form config
    """
    if 'steps' not in config:
        raise ValueError("Form config must have 'steps' field")
    
    if not isinstance(config['steps'], list):
        raise ValueError("Form 'steps' must be a list")
    
    # Validate each step
    for i, step in enumerate(config['steps']):
        if not isinstance(step, dict):
            raise ValueError(f"Step {i} must be a dictionary")
        
        required_fields = ['field', 'type', 'prompt']
        for field in required_fields:
            if field not in step:
                raise ValueError(f"Step {i} must have '{field}' field")
        
        # Validate field type
        valid_types = ['text', 'number', 'choice', 'file', 'textarea', 'email', 'phone']
        if step['type'] not in valid_types:
            raise ValueError(f"Step {i} has invalid type '{step['type']}'. Valid types: {valid_types}")
    
    return config


def create_form_states(form_config: Dict[str, Any]) -> type[StatesGroup]:
    """
    Create FSM States class from form configuration.
    
    Args:
        form_config: Parsed form configuration
        
    Returns:
        StatesGroup class with states for each step
    """
    steps = form_config['steps']
    
    # Create state names from step field names
    state_names = {}
    for step in steps:
        field_name = step['field']
        # Convert field_name to PascalCase for state name
        state_name = ''.join(word.capitalize() for word in field_name.split('_'))
        state_names[field_name] = State()
    
    # Create dynamic StatesGroup class
    class_name = form_config.get('name', 'FormStates').replace(' ', '').replace('-', '')
    
    # Create StatesGroup dynamically
    FormStates = type(
        class_name,
        (StatesGroup,),
        state_names
    )
    
    return FormStates


def validate_form_step(step: Dict[str, Any], value: str) -> tuple[bool, Optional[str]]:
    """
    Validate form step value.
    
    Args:
        step: Step configuration
        value: User input value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    field_type = step['type']
    validation = step.get('validation', {})
    
    # Required check
    if step.get('required', False) and not value.strip():
        return False, f"{step.get('prompt', 'This field')} is required."
    
    # Type-specific validation
    if field_type == 'text' or field_type == 'textarea':
        min_length = validation.get('min_length', 0)
        max_length = validation.get('max_length', float('inf'))
        
        if len(value) < min_length:
            return False, f"Minimum length is {min_length} characters."
        if len(value) > max_length:
            return False, f"Maximum length is {max_length} characters."
    
    elif field_type == 'number':
        try:
            num_value = float(value)
            min_value = validation.get('min_value')
            max_value = validation.get('max_value')
            
            if min_value is not None and num_value < min_value:
                return False, f"Minimum value is {min_value}."
            if max_value is not None and num_value > max_value:
                return False, f"Maximum value is {max_value}."
        except ValueError:
            return False, "Please enter a valid number."
    
    elif field_type == 'choice':
        options = step.get('options', [])
        if value not in options:
            return False, f"Please choose one of: {', '.join(options)}"
    
    elif field_type == 'email':
        if '@' not in value or '.' not in value.split('@')[1]:
            return False, "Please enter a valid email address."
    
    elif field_type == 'phone':
        # Basic phone validation (digits, spaces, +, -, parentheses)
        import re
        if not re.match(r'^[\d\s\+\-\(\)]+$', value):
            return False, "Please enter a valid phone number."
    
    return True, None

