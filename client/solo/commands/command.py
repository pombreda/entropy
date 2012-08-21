# -*- coding: utf-8 -*-
"""

    @author: Fabio Erculiani <lxnay@sabayon.org>
    @contact: lxnay@sabayon.org
    @copyright: Fabio Erculiani
    @license: GPL-2

    B{Entropy Command Line Client}.

"""
from entropy.i18n import _
from entropy.output import darkgreen, print_error
from entropy.exceptions import PermissionDenied
from entropy.client.interfaces import Client
from entropy.core.settings.base import SystemSettings

import entropy.tools

class SoloCommand(object):
    """
    Base class for Solo commands
    """

    # Set this to the command name from where this object
    # gets triggered (for equo help, "help" is the NAME
    # that should be set).
    NAME = None
    # Set this to a list of aliases for NAME
    ALIASES = []
    # Set this to True if command is a catch-all (fallback)
    CATCH_ALL = False
    # Allow unprivileged access ?
    ALLOW_UNPRIVILEGED = False

    # If True, the command is not shown in the help output
    HIDDEN = False

    # These two class variables are used in the man page
    # generation. You also need to override man()
    INTRODUCTION = "No introduction available"
    SEE_ALSO = ""

    def __init__(self, args):
        self._args = args

    def _get_parser(self):
        """
        This is the argparse parser setup method, it shall return
        the ArgumentParser object that will be used by parse().
        """
        raise NotImplementedError()

    def parse(self):
        """
        Parse the actual arguments and return
        the function that should be called and
        its arguments. The function signature is:
          int function([list of args])
        The return value represents the exit status
        of the "command"
        """
        raise NotImplementedError()

    def bashcomp(self, last_arg):
        """
        Print to standard output the bash completion outcome
        for given arguments (self._args).
        Raise NotImplementedError() if not supported.

        @param last_arg: last argument in the argv. Useful
        for allowing its automagic completion.
        Can be None !!
        @type last_arg: string or None
        """
        raise NotImplementedError()

    def man(self):
        """
        Return a dictionary containing the following man
        entries (in a2x format), excluding the entry title:
        name, synopsis, introduction, options.
        Optional keys are: seealso.
        All of them are mandatory.
        """
        raise NotImplementedError()

    def _man(self):
        """
        Standard man page outcome generator that can be used
        to implement class-specific man() methods.
        You need to provide your own INTRODUCTION and
        SEE_ALSO class fields (see class-level variables).
        """
        parser = self._get_parser()
        prog = "%s %s" % ("equo", self.NAME)
        formatter = parser.formatter_class(prog=prog)
        usage = formatter._format_usage(parser.usage,
                            parser._actions,
                            parser._mutually_exclusive_groups,
                            "").rstrip()

        options_txt = []
        action_groups = parser._action_groups
        if action_groups:
            options_header = "\"equo " + self.NAME + "\" "
            options_header += "supports the following options which "
            options_header += "alters its behaviour.\n\n"
            options_txt.append(options_header)

        for group in action_groups:
            if group._group_actions:
                options_txt.append(group.title.upper())
                options_txt.append("~" * len(group.title))
            for action in group._group_actions:
                action_name = action.metavar

                option_strings = action.option_strings
                if not option_strings:
                    # positional args
                    if action_name is None:
                        # SubParsers
                        action_lst = []
                        for sub_action in action._get_subactions():
                            sub_action_str = "*" + sub_action.dest + "*::\n"
                            sub_action_str += "    " + sub_action.help + "\n"
                            action_lst.append(sub_action_str)
                        action_str = "\n".join(action_lst)
                    else:
                        action_str = "*" + action_name + "*::\n"
                        action_str += "    " + action.help + "\n"
                else:
                    action_str = ""
                    for option_str in option_strings:
                        action_str = "*" + option_str + "*"
                        if action_name:
                            action_str += "=" + action_name
                        action_str += "::\n"
                        action_str += "    " + action.help + "\n"
                options_txt.append(action_str)

        data = {
            'name': self.NAME,
            'description': parser.description,
            'introduction': self.INTRODUCTION,
            'seealso': self.SEE_ALSO,
            'synopsis': usage,
            'options': "\n".join(options_txt),
        }
        return data

    def _entropy(self, *args, **kwargs):
        """
        Return the Entropy Client object.
        This method is not thread safe.
        """
        return Client(*args, **kwargs)

    def _call_locked(self, func, repo):
        """
        Execute the given function at func after acquiring Entropy
        Resources Lock, for given repository at repo.
        The signature of func is: int func(entropy_server).
        """
        server = None
        acquired = False
        try:
            try:
                server = self._entropy(default_repository=repo)
            except PermissionDenied as err:
                print_error(err.value)
                return 1
            acquired = entropy.tools.acquire_entropy_locks(server)
            if not acquired:
                server.output(
                    darkgreen(_("Another Entropy is currently running.")),
                    level="error", importance=1
                )
                return 1
            return func(server)
        finally:
            if server is not None:
                if acquired:
                    entropy.tools.release_entropy_locks(server)
                server.shutdown()

    def _call_unlocked(self, func, repo):
        """
        Execute the given function at func after acquiring Entropy
        Resources Lock in shared mode, for given repository at repo.
        The signature of func is: int func(entropy_server).
        """
        server = None
        acquired = False
        try:
            try:
                server = self._entropy(default_repository=repo)
            except PermissionDenied as err:
                print_error(err.value)
                return 1
            # use blocking mode to avoid tainting stdout
            acquired = entropy.tools.acquire_entropy_locks(
                server, blocking=True, shared=True)
            if not acquired:
                server.output(
                    darkgreen(_("Another Entropy is currently running.")),
                    level="error", importance=1
                )
                return 1
            return func(server)
        finally:
            if server is not None:
                if acquired:
                    entropy.tools.release_entropy_locks(server)
                server.shutdown()

    def _settings(self):
        """
        Return a SystemSettings instance.
        """
        return SystemSettings()