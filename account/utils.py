import os
from django.conf import settings
import random
import string


def generate_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{instance.first_name}_{instance.custom_id}.{ext}'
    return f'profile_pics/{filename}'


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(request):
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    if 'mobile' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent:
        return 'tablet'
    else:
        return 'desktop'

