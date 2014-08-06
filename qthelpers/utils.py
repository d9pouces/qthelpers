# coding=utf-8
from PySide import QtCore
import threading

__author__ = 'flanker'


def p(obj):
    from qthelpers.application import application
    if obj is None:
        return None
    return application.parent


class ThreadedCalls(object):
    _generic_signal = QtCore.Signal(list)

    def __init__(self):
        """ A subclass of GenericSignal must also be a subclass of QObject.
        This superclass helps for calling method through signals, without creating many different signals.
        It also allows to design methods in two parts:
            * a part in a different thread (which can take a long time)
            * a part in the main thread (to display the result to the user)
        :return:
        """
        # noinspection PyUnresolvedReferences
        self._generic_signal.connect(self._generic_slot)
        self._call_counters = {}

    # noinspection PyMethodMayBeStatic
    def _generic_slot(self, arguments: list):
        """
        Generic slot, connected to self.generic_signal
        :param arguments: list of [callable, args: list, kwargs: dict]
        :return: nothing

        Never do it static! Segfault on the exit otherwise…
        """
        my_callable = arguments[0]
        my_callable(*(arguments[1]), **(arguments[2]))

    def _thread_caller(self, thread_callable, result_callable, counter, args, kwargs):
        result = thread_callable(*args, **kwargs)
        if counter is not None and self._call_counters[thread_callable.__name__] != counter:
            return
        values = [result] + list(args)
        # noinspection PyUnresolvedReferences
        self._generic_signal.emit([result_callable, values, kwargs])

    def signal_call(self, my_callable, *args, **kwargs):
        """ Call `my_callable`(*args, **kwargs) in the main thread (GUI) thanks to a generic signal.
         Designed to be called from a secondary thread.
        :param my_callable:
        :param args:
        :param kwargs:
        :return:
        """
        # noinspection PyUnresolvedReferences
        self._generic_signal.emit([my_callable, args, kwargs])

    def threaded_call(self, thread_callable, result_callable,  *args, **kwargs):
        """
        Call result = `thread_callable`(*args, **kwargs) in a different (non-GUI) thread,
        then call `result_callable`(result, *args, **kwargs) in the main (GUI) thread.
        :param result_callable:
        :param args:
        :param kwargs:
        :param thread_callable:
        :return:
        """
        thread_args = (thread_callable, result_callable, None, args, kwargs)
        t = threading.Thread(target=self._thread_caller, group=None, args=thread_args)
        t.start()

    def cancellable_call(self, thread_callable, result_callable, *args, **kwargs):
        """
        Call result = `thread_callable`(*args, **kwargs) in a different (non-GUI) thread,
        then call `result_callable`(result, *args, **kwargs) in the main (GUI) thread.
        The call to `result_callable` can be automatically cancelled, in the following case:

            - call to `thread_callable`(*args1, **kwargs1)
            - call to `thread_callable`(*args2, **kwargs2)
            - the result of `thread_callable`(*args2, **kwargs2) is available
            - call to `result_callable`(result2, *args2, **kwargs2)
            - the result of `thread_callable`(*args1, **kwargs1) is available
            - the call to `result_callable`(result1, *args1, **kwargs1) is cancelled

        :param thread_callable:
        :param result_callable:
        :param args:
        :param kwargs:
        :return:
        """
        self._call_counters.setdefault(thread_callable.__name__, 0)
        self._call_counters[thread_callable.__name__] += 1
        thread_args = (thread_callable, result_callable, self._call_counters[thread_callable.__name__], args, kwargs)
        t = threading.Thread(target=self._thread_caller, group=None, args=thread_args)
        t.start()


if __name__ == '__main__':
    import doctest

    doctest.testmod()