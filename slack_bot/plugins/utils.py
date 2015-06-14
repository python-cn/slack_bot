# coding=utf-8


def check_cache(cache, fn, *args, **kwargs):
    return (cache.cached(fn) if cache is not None else fn)(*args, **kwargs)
