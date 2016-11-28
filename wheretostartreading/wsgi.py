"""
WSGI config for wheretostartreading project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

from django.core.cache.backends.memcached import BaseMemcachedCache

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wheretostartreading.settings")

application = get_wsgi_application()
application = DjangoWhiteNoise(application)

# Fix django closing connection to MemCachier after every request (#11331)
BaseMemcachedCache.close = lambda self, **kwargs: None
