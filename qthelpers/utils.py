# coding=utf-8

__author__ = 'flanker'


def p(obj):
    from qthelpers.application import application
    if obj is None:
        return None
    return application.parent


if __name__ == '__main__':
    import doctest

    doctest.testmod()