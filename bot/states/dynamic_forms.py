"""
Dynamic form states generated from bot configuration.
"""
from typing import Dict, Any, Optional
from aiogram.fsm.state import State, StatesGroup
from bot.utils.form_builder import parse_form_config, create_form_states


# Cache for form state classes
_form_state_classes: Dict[str, type[StatesGroup]] = {}


def get_form_states(form_name: str, form_config: Dict[str, Any]) -> type[StatesGroup]:
    """
    Get or create FSM States class for a form.
    
    Args:
        form_name: Name of the form
        form_config: Form configuration
        
    Returns:
        StatesGroup class
    """
    # Check cache
    if form_name in _form_state_classes:
        return _form_state_classes[form_name]
    
    # Parse and create states
    parsed_config = parse_form_config(form_config)
    states_class = create_form_states(parsed_config)
    
    # Cache it
    _form_state_classes[form_name] = states_class
    
    return states_class


def clear_form_state_cache(form_name: Optional[str] = None):
    """
    Clear form state cache.
    
    Args:
        form_name: Form name to clear, or None to clear all
    """
    if form_name:
        _form_state_classes.pop(form_name, None)
    else:
        _form_state_classes.clear()

