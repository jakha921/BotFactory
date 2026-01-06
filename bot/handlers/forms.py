"""
Handlers for dynamic forms based on bot configuration.
"""
from typing import Dict, Any, Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
from bot.utils.form_builder import validate_form_step, parse_form_config
from bot.states.dynamic_forms import get_form_states, clear_form_state_cache
from bot.services.ui_config_service import get_ui_config_service
from bot.integrations.django_orm import get_bot_by_token

forms_router = Router()


class FormModeFilter(BaseFilter):
    """Filter to check if user is in form mode."""
    
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        """Check if user is in form mode."""
        try:
            data = await state.get_data()
            is_in_form = 'form_name' in data and 'form_config' in data
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"FormModeFilter: user={message.from_user.id}, is_in_form={is_in_form}, data_keys={list(data.keys())}")
            return is_in_form
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"FormModeFilter error: {e}")
            return False


async def start_form(
    message: Message,
    state: FSMContext,
    bot_token: str,
    form_name: str
):
    """
    Start a dynamic form based on configuration.
    
    Args:
        message: Telegram message
        state: FSM context
        bot_token: Bot token
        form_name: Name of the form
    """
    bot = await get_bot_by_token(bot_token)
    if not bot:
        await message.answer("Бот не найден или не активирован.")
        return
    
    ui_service = get_ui_config_service()
    form_config = await ui_service.get_form(str(bot.id), form_name)
    
    if not form_config:
        await message.answer(f"Форма '{form_name}' не найдена.")
        return
    
    try:
        parsed_config = parse_form_config(form_config)
    except ValueError as e:
        await message.answer(f"Ошибка конфигурации формы: {str(e)}")
        return
    
    # Get form states
    FormStates = get_form_states(form_name, parsed_config)
    
    # Get first step
    first_step = parsed_config['steps'][0]
    
    # Set state to first step
    state_data = {
        'form_name': form_name,
        'current_step': 0,
        'form_data': {},
        'form_config': parsed_config
    }
    await state.update_data(**state_data)
    
    # Set FSM state to first step
    first_field = first_step['field']
    state_name = ''.join(word.capitalize() for word in first_field.split('_'))
    await state.set_state(getattr(FormStates, state_name))
    
    # Send prompt for first step
    prompt = first_step['prompt']
    await message.answer(prompt)


@forms_router.message(F.text, FormModeFilter())
async def handle_form_input(message: Message, state: FSMContext):
    """
    Handle form input for dynamic forms.
    Only processes messages when user is in form mode.
    Uses FormModeFilter to ensure this handler only runs when user is in form mode.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[FORMS_ROUTER] Processing form input: text={message.text}, from_user={message.from_user.id}")
    
    data = await state.get_data()
    
    form_config = data['form_config']
    current_step = data['current_step']
    form_data = data.get('form_data', {})
    
    steps = form_config['steps']
    
    if current_step >= len(steps):
        # Form completed
        await handle_form_submission(message, state, form_data, form_config)
        return
    
    # Get current step
    step = steps[current_step]
    user_input = message.text or ''
    
    # Validate step
    is_valid, error_message = validate_form_step(step, user_input)
    
    if not is_valid:
        await message.answer(f"{error_message}")
        return
    
    # Save form data
    form_data[step['field']] = user_input
    await state.update_data(form_data=form_data)
    
    # Move to next step
    next_step_index = current_step + 1
    
    if next_step_index >= len(steps):
        # Form completed
        await handle_form_submission(message, state, form_data, form_config)
    else:
        # Continue to next step
        next_step = steps[next_step_index]
        FormStates = get_form_states(data['form_name'], form_config)
        
        next_field = next_step['field']
        state_name = ''.join(word.capitalize() for word in next_field.split('_'))
        await state.set_state(getattr(FormStates, state_name))
        
        await state.update_data(current_step=next_step_index)
        
        prompt = next_step['prompt']
        await message.answer(prompt)


async def handle_form_submission(
    message: Message,
    state: FSMContext,
    form_data: Dict[str, Any],
    form_config: Dict[str, Any]
):
    """
    Handle form submission.
    
    Args:
        message: Telegram message
        state: FSM context
        form_data: Collected form data
        form_config: Form configuration
    """
    form_name = form_config.get('name', 'Form')
    submit_handler = form_config.get('submit_handler')
    
    # Clear form state
    await state.clear()
    
    # Format form data for display
    form_text = f"Форма '{form_name}' заполнена:\n\n"
    for field, value in form_data.items():
        form_text += f"• {field}: {value}\n"
    
    await message.answer(form_text)
    
    # Call submit handler if specified
    # This could be a webhook URL, database save, or other action
    if submit_handler:
        import logging
        logger = logging.getLogger(__name__)

        # Check if it's a webhook URL
        if submit_handler.startswith('http://') or submit_handler.startswith('https://'):
            try:
                import httpx
                async with httpx.AsyncClient() as http_client:
                    payload = {
                        'form_name': form_name,
                        'form_data': form_data,
                        'user_id': message.from_user.id,
                        'username': message.from_user.username or message.from_user.first_name,
                    }
                    response = await http_client.post(submit_handler, json=payload, timeout=10)
                    if response.status_code == 200:
                        await message.answer("✅ Форма успешно отправлена")
                    else:
                        await message.answer("⚠️ Ошибка при отправке формы")
            except ImportError:
                logger.error("httpx not installed for webhook support")
                await message.answer("⚠️ Webhook не настроен")
            except Exception as e:
                logger.error(f"Webhook error for {submit_handler}: {e}")
                await message.answer("⚠️ Ошибка соединения")
        else:
            # Handler name (could be mapped to database save or other action)
            logger.info(f"Form '{form_name}' submitted with handler: {submit_handler}")
            logger.info(f"Form data: {form_data}")
            await message.answer(f"✅ Данные сохранены (handler: {submit_handler})")

