#coding=utf-8


from qtexample.translation import ugettext as _

__author__ = 'flanker'


"""Core shell application.
Parse arguments and logger, use translated strings.
"""

import argparse

__all__ = ['main']


def main():
    """Main function, intended for use as command line executable.

    Args:
        None
    Returns:
      * :class:`int`: 0 in case of success, != 0 if something went wrong

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help=_('print more messages'), default=False)
    parser.add_argument('-d', '--debug', action='store_true', help=_('print debug messages'), default=False)
    options, args = parser.parse_args()
    
    return_code = 0  # 0 = success, != 0 = error
    # complete this function
    print(_('Hello, world!'))
    return return_code

if __name__ == '__main__':
    import doctest
    doctest.testmod()