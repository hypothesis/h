"""
Filters for logging.
"""


import logging

class FilterExceptions(logging.Filter):
    def __init__(self, ignore_exceptions):
        """
        Filters exceptions from getting logged.

        ignore_exceptions: a tuple of tuples ((exception type, loglevel))
                           example: (("requests.exceptions.ReadTimeout","WARNING"),)
        """
        logging_level_names = {level_name: (getattr(logging, level_name) if type(level_name) is str else level_name)
                                 for level_name in logging._levelNames}
        self._ignore_exceptions = []
        for (exc_type, exc_level) in ignore_exceptions:
            exception_idx = exc_type.rfind('.')
            module, exception = exc_type[:exception_idx], exc_type[exception_idx+1:]
            try:
                self._ignore_exceptions.append((logging_level_names[exc_level], getattr(__import__(module), exception)))
            except KeyError:
                raise ValueError('The logging level provided ({}) is invalid. Valid options: {}'.format(exc_level,logging_level_names.keys()))
            except (ImportError,AttributeError):
                raise ValueError('The exception path does not exist ({}.{}).'.format(module, exception))

    def filter(self, record):
        if record.exc_info:
            exc_info = record.exc_info[1]
            for filter_level, filter_exc in self._ignore_exceptions:
                if record.exc_info[0] is filter_exc and record.levelno == filter_level:
                    print "********* filtering exception"
                    return False
        return True

