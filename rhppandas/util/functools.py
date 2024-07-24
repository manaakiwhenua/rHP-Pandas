from functools import partial, update_wrapper


def wrapped_partial(func, *args, **kwargs):
    """
    Properly wrapped partial function

    Appropriated from h3pandas.util package
    """
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func
