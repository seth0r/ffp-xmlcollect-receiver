__all__ = []

import pkgutil
import inspect

DEBUG = False

lastn = None
maxtrys = len(list( pkgutil.walk_packages(__path__) ))
while True:
    for loader, mname, is_pkg in pkgutil.walk_packages(__path__):
        try:
            if DEBUG:
                print("Trying to load %s..." % mname, end=" ")
            module = loader.find_module(mname).load_module(mname)
            for name, value in inspect.getmembers(module):
                if name.startswith('__'):
                    continue
                globals()[name] = value
                __all__.append(name)
            if lastn == mname:
                lastn = None
            if DEBUG:
                print("loaded.")
        except NameError as ne:
            if DEBUG:
                print( ne )
            if mname == lastn:
                raise
            lastn = mname
    if lastn is None:
        break
    elif maxtrys <= 0:
        raise
    maxtrys -= 1
