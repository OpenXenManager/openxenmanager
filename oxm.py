# TODO: this will be the future entry-point

import pygtk
import gobject

def idle(func):
    return lambda *args, **kwargs: gobject.idle_add(lambda: func(*args, **kwargs) and False)
