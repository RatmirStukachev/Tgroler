import json
import os
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from urllib.parse import parse_qsl
from core.telegram_auth import validate_init_data
from core.models import User

def telegram_auth_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # We expect initData to be passed in the headers or body. Let's use a custom header 'X-TG-INIT-DATA'
        init_data = request.headers.get('X-TG-INIT-DATA')

        if not init_data:
            return JsonResponse({'error': 'Missing initData header'}, status=401)

        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            return JsonResponse({'error': 'Server configuration error'}, status=500)

        if not validate_init_data(init_data, bot_token):
            # For local testing, bypass if init_data is "test_mode"
            if not (settings.DEBUG and init_data == "test_mode"):
                return JsonResponse({'error': 'Invalid Telegram authentication'}, status=403)

        # Extract user info
        try:
            if settings.DEBUG and init_data == "test_mode":
                # Mock user for local testing if needed
                user = User.objects.first()
                if not user:
                    user = User.objects.create(telegram_id=123456789, username='test_user', name='Test User')
                request.tg_user = user
                return view_func(request, *args, **kwargs)

            parsed_data = dict(parse_qsl(init_data))
            user_data_str = parsed_data.get('user', '{}')
            user_data = json.loads(user_data_str)

            tid = user_data.get('id')
            if not tid:
                 return JsonResponse({'error': 'User ID not found in initData'}, status=400)

            # Fetch user from DB. If they don't exist, they should use /start in bot first.
            # Or we create them just in case.
            name = user_data.get('first_name', '')
            if user_data.get('last_name'):
                name += f" {user_data.get('last_name')}"

            user, _ = User.objects.get_or_create(
                telegram_id=tid,
                defaults={'username': user_data.get('username'), 'name': name}
            )

            request.tg_user = user
        except Exception as e:
            return JsonResponse({'error': f'Failed to process user data: {str(e)}'}, status=400)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
