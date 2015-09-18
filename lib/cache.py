from functools import wraps
from flask import request
from werkzeug.contrib.cache import MemcachedCache, NullCache
from pylibmc import Client
from time import time
import email.utils
import os


# cache connection retry max attempts
MAX_CACHE_RETRIES = 3


def _setup_cache(app):
    """
    If a test is being run or we don't want cache, NullCache will be initialized just as a dummy.
    If running locally without the 'DISABLE_CACHE' env variable and without a memcached instance running,
    MemcachedCache and it's underlying pylibmc will give no warning on connection, but will throw
    exceptions when trying to work with the cache. A few connection retires will be made in that
    scenario, and eventually the cache will be replaced with a NullCache. Binary communications must
    be used for SASL.
    """

    # initialize the retry count if it's our first time here
    if not hasattr(app, 'cache_retry'):
        app.cache_retry = 0

    # Setup cache
    if app.config['TESTING'] or os.environ.get('DISABLE_CACHE', None) is not None:
        app.cache = NullCache()
        app.logger.debug('Cache initialized as NullCache')
    else:
        MEMCACHED_SERVERS = os.environ.get('MEMCACHEDCLOUD_SERVERS', '127.0.0.1:11211')

        try:
            memcached_client = Client(servers=MEMCACHED_SERVERS.split(','),
                                      username=os.environ.get('MEMCACHEDCLOUD_USERNAME'),
                                      password=os.environ.get('MEMCACHEDCLOUD_PASSWORD'),
                                      binary=True)
            app.cache = MemcachedCache(memcached_client)
            app.logger.debug('Cache initialized as MemcachedCache with servers: %s', MEMCACHED_SERVERS)
        except Exception as e:
            # very unlikely to have an exception here. pylibmc mostly throws when trying to communicate, not connect
            app.logger.error('Error initializing MemcachedCache: %s', e);
            app.logger.error('Initializing cache as NullCache. Fix ASAP!');
            app.cache = NullCache()


def cached(app, timeout=3600, cache_key=None, set_expires=True):
    """
    Caching decorator for Flask routes

    Provides both caching and setting of relevant "Expires" header if appropriate.
    Adapted from http://flask.pocoo.org/docs/patterns/viewdecorators/
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if cache_key is None:
                ck = 'view:%s?%s' % (request.path, request.query_string)
            else:
                ck = cache_key
            ek = '%s.expires' % ck
            response = None
            expires = None

            # pylibmc will throw an error when trying to communicate with memcached, not upon a bad connection
            try:
                cached = app.cache.get_many(ck, ek)
                if cached[0] is not None:
                    response = cached[0]
                    app.logger.debug('Cache hit for %s, returning cached content, expires=%d', ck, cached[1])
                    if cached[1] is not None and set_expires:
                        expires = cached[1]
                else:
                    response = f(*args, **kwargs)
                    expires = int(time() + timeout)
                    app.cache.set_many({ck: response, ek: expires}, timeout=timeout)
                    app.logger.debug('Cache miss for %s, refreshed content and saved in cache, expires=%d', ck, expires)

                if set_expires and expires is not None:
                    response.headers['Expires'] = email.utils.formatdate(expires)
            except Exception as e:
                app.logger.error('Cache error, returning miss: %s', e)
                if response is None:
                    response = f(*args, **kwargs)

                if (type(app.cache) is not NullCache):
                    if (app.cache_retry < MAX_CACHE_RETRIES):
                        app.cache_retry += 1
                        app.logger.error('Attempting to restore cache')
                        _setup_cache(app)
                    else:
                        app.logger.error('Exhausted retry attempts. Converting cache to NullCache. Fix ASAP!')
                        app.cache = NullCache()

            return response

        return decorated_function

    return decorator
