from distutils.version import StrictVersion

import django
from django.core.management.base import BaseCommand

from optparse import make_option


class ProxyParser(object):
    """Faux parser object that will ferry our arguments into options."""

    def __init__(self, command):
        self.command = command

    def add_argument(self, *args, **kwargs):
        self.command.option_list += (make_option(*args, **kwargs),)


class CompatibilityBaseCommand(BaseCommand):
    """Provides a compatibility between optparse and argparse transition.

    Starting in Django 1.8, argparse is used. In Django 1.9, optparse support
    will be removed.

    For optparse, you append to the option_list class attribute.
    For argparse, you must define add_arguments(self, parser).
    BaseCommand uses the presence of option_list to decide what course to take.
    """

    def __init__(self, *args, **kwargs):
        if StrictVersion(django.get_version()) < StrictVersion('1.8') and hasattr(self, 'add_arguments'):
            self.option_list = BaseCommand.option_list
            parser = ProxyParser(self)
            self.add_arguments(parser)
        super(CompatibilityBaseCommand, self).__init__(*args, **kwargs)
