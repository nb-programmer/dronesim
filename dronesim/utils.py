
import time

_last_check_time = {}
def callevery(check_every : float):
    def timed_func_call_wrap(func):
        _last_check_time[func.__qualname__] = [0.0, check_every, None]
        def _needs_call(name):
            return (len(_last_check_time[name]) < 3) or (time.time() - _last_check_time[name][0] > _last_check_time[name][1])
        def timed_func_call(*args, **kwargs):
            f_name = func.__qualname__
            if _needs_call(f_name):
                _last_check_time[f_name][2] = func(*args, **kwargs)
                _last_check_time[f_name][0] = time.time()
                return _last_check_time[f_name][2]
            return _last_check_time[f_name][2]
        return timed_func_call
    return timed_func_call_wrap
