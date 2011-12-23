from functools import wraps

from django.utils.decorators import decorator_from_middleware_with_args

from cache_tags import get_cache, cache
from cache_tags.middleware import CacheMiddleware


def cache_transaction(f):
    """Decorator for any callback,

    that automatically handles database transactions."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        cache_alias = kwargs.pop('cache', None)
        if cache_alias:
            cache = get_cache(cache_alias)
        else:
            cache = globals()['cache']
        cache.transaction_begin()
        result = f(*args, **kwargs)
        cache.transaction_finish()
        return result
    return wrapper


def cache_transaction_all(f):
    """Decorator for any callback,

    that automatically handles database transactions,
    and calls CacheTags.transaction_finish_all() instead of
    CacheTags.transaction_finish().
    So. It will handles all transaction's scopes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        cache_alias = kwargs.pop('cache', None)
        if cache_alias:
            cache = get_cache(cache_alias)
        else:
            cache = globals()['cache']
        cache.transaction_begin()
        result = f(*args, **kwargs)
        cache.transaction_finish_all()
        return result
    return wrapper


def cache_page(*args, **kwargs):
    """
    Decorator for views that tries getting the page from the cache and
    populates the cache if the page isn't in the cache yet.

    The cache is keyed by the URL and some data from the headers.
    Additionally there is the key prefix that is used to distinguish different
    cache areas in a multi-site setup. You could use the
    sites.get_current().domain, for example, as that is unique across a Django
    project.

    Additionally, all headers from the response's Vary header will be taken
    into account on caching -- just like the middleware does.
    """
    # We need backwards compatibility with code which spells it this way:
    #   def my_view(): pass
    #   my_view = cache_page(my_view, 123)
    # and this way:
    #   my_view = cache_page(123)(my_view)
    # and this:
    #   my_view = cache_page(my_view, 123, key_prefix="foo")
    # and this:
    #   my_view = cache_page(123, key_prefix="foo")(my_view)
    # and possibly this way (?):
    #   my_view = cache_page(123, my_view)
    # and also this way:
    #   my_view = cache_page(my_view)
    # and also this way:
    #   my_view = cache_page()(my_view)

    # We also add some asserts to give better error messages in case people are
    # using other ways to call cache_page that no longer work.
    cache_alias = kwargs.pop('cache', None)
    key_prefix = kwargs.pop('key_prefix', None)
    # patch start
    tags = kwargs.pop('tags', ())
    assert not kwargs, "The only keyword arguments are cache and key_prefix"
    def warn():
        import warnings
        warnings.warn('The cache_page decorator must be called like: '
                      'cache_page(timeout, [cache=cache name], [key_prefix=key prefix]). '
                      'All other ways are deprecated.',
                      PendingDeprecationWarning)

    if len(args) > 1:
        assert len(args) == 2, "cache_page accepts at most 2 arguments"
        warn()
        if callable(args[0]):
            return decorator_from_middleware_with_args(CacheMiddleware)(cache_timeout=args[1], cache_alias=cache_alias, key_prefix=key_prefix, tags=tags)(args[0])
        elif callable(args[1]):
            return decorator_from_middleware_with_args(CacheMiddleware)(cache_timeout=args[0], cache_alias=cache_alias, key_prefix=key_prefix, tags=tags)(args[1])
        else:
            assert False, "cache_page must be passed a view function if called with two arguments"
    elif len(args) == 1:
        if callable(args[0]):
            warn()
            return decorator_from_middleware_with_args(CacheMiddleware)(cache_alias=cache_alias, key_prefix=key_prefix, tags=tags)(args[0])
        else:
            # The One True Way
            return decorator_from_middleware_with_args(CacheMiddleware)(cache_timeout=args[0], cache_alias=cache_alias, key_prefix=key_prefix, tags=tags)
    else:
        warn()
        # patch end
        return decorator_from_middleware_with_args(CacheMiddleware)(cache_alias=cache_alias, key_prefix=key_prefix, tags=tags)
