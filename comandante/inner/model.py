"""Comandante domain model.

Description:
-----------

This module contains classes that describes notions
defined by the comandante toolkit: Commands, Options, etc.

This model classes are more or less declarations needed
for parsers and executors to interpret command line
arguments and execute the corresponding logic.
"""

import inspect
import itertools
import re

from comandante.inner.helpers import describe
from comandante.inner.output.help_writer import HelpWriter
from comandante.inner.parser import Parser


class _Empty:
    """Marker object for Argument.empty"""


class Option:
    """Command option descriptor.

    Option must have a valid name and a valid short name.
    Option with name='long' and short-name='s' will have
    the following syntax:

        --long [value]

    The same using the short name will be:

        -s [value]

    Option value will be parsed according to the option.type.
    The type must be a callable accepting a single argument. It
    will be called with the option value from the command-line.
    The only exception is when option.type=bool. In this case
    no value is supposed. Option value is supposed to be default
    when it is not specified and supposed to be True when option
    is specified (without any value):

        --boolean_option # NOTE: there is no option value

    All options must have a default value by design. If some option
    must be specified it should be a command argument instead -
    not an option.
    """

    # Regex-pattern of valid option name.
    # Valid option name starts with alphabetic character and
    # its tail contain any number of alpha-numeric characters.
    _name_pattern = re.compile(r'[a-zA-Z]\w+')

    @staticmethod
    def is_valid_name(name):
        """Validate otion name.

        :param name: option name to be validated
        :return: True iff name is a valid option name
        """
        return isinstance(name, str) and bool(Option._name_pattern.fullmatch(name))

    def __init__(self, name, short, type, default, descr=""):
        """Initialize an instance.

        :param name: option long name
        :param short: option short name
        :param type: option type
        :param default: option default value
        :param descr: option description
        """
        if not Option.is_valid_name(name):
            raise ValueError("Not a valid option name: " + str(name))

        self._name = name
        self._short = short
        self._type = type
        self._default = default
        self._descr = descr

    @property
    def name(self):
        """Get option long name."""
        return self._name

    @property
    def short(self):
        """Get option short name."""
        return self._short

    @property
    def type(self):
        """Get option type."""
        return self._type

    @property
    def default(self):
        """Get option default value."""
        return self._default

    @property
    def descr(self):
        """Get option description."""
        return self._descr


class Argument:
    """Argument descriptor.

    Argument is a command parameter that is essential to what
    command will actually do.

    Each argument must have a valid name derived from the
    corresponding function (or method) parameter name.

    Each argument must have a type. Argument.type will is a callable
    that will be used to parse the corresponding string value from
    the command-line. The only exception is the argument.type=bool,
    in which case argument name is interpreted as a True (all other
    values are interpreted as not relevant to the argument).
    """

    @staticmethod
    def from_param(param):
        """Create a new Argument from the given inspect.Parameter.

        :param param: inspect.Parameter from which to derive argument attributes
        :return: a new Argument instance initialized from the parameter
        """
        return Argument(
            name=param.name,
            type=Argument._param_type(param),
            default=Argument._param_default(param)
        )

    @staticmethod
    def _param_default(param):
        """Derive argument default value from the inspect.Parameter default value."""
        if param.default is inspect.Parameter.empty:
            return Argument.empty
        return param.default

    @staticmethod
    def _param_type(param):
        """Derive argument type from the parameter annotation"""
        if param.annotation is inspect.Parameter.empty:
            return str
        return param.annotation

    # Marker value indicating that default value is not specified.
    empty = _Empty

    def __init__(self, name, type, default):
        """Initialize instance.

        :param name: argument name
        :param type: argument type
        :param default: default value (Argument.empty if not present)
        """
        self._name = name
        self._type = type
        self._default = default

    @property
    def name(self):
        """Get argument name."""
        return self._name

    @property
    def type(self):
        """Get argument type."""
        return self._type

    @property
    def default(self):
        """Get argument default value."""
        return self._default

    def is_required(self):
        """Check if argument is required."""
        return self.default is Argument.empty


class Signature:
    """Command signature descriptor.

    Signature represents a sequence of required
    and optional command arguments.
    """

    @staticmethod
    def from_function(func, is_method=False):
        """Derive a new `Signature` from the given callable object.

        :param func: a callable object from which to derive signature
        :param is_method: indicates whether the first argument is `self`
        :return: a new `Signature` derived from the `func`
        """
        sig = inspect.signature(func)
        required = []
        optional = []
        vararg = None
        accepts_options = False

        params = sig.parameters.items()
        if is_method:
            params = itertools.islice(params, 1, None)

        for name, param in params:
            if param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                argument = Argument.from_param(param)
                category = Signature._determine_category(argument, required, optional)
                category.append(argument)
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                vararg = Argument.from_param(param)
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                accepts_options = True
        return Signature(
            required=required,
            optional=optional,
            vararg=vararg,
            accepts_options=accepts_options,
            is_method=is_method
        )

    @staticmethod
    def _determine_category(argument, required, optional):
        """Determine argument category from its default value."""
        if argument.default is Argument.empty:
            return required
        return optional

    @staticmethod
    def _params(func, is_method):
        """Extract parameters from the `func` honoring its nature (method or procedure)."""
        parameters = inspect.signature(func).parameters.items()
        if is_method:
            return itertools.islice(parameters, 1, None)
        return parameters.items()

    def __init__(self, required, optional, vararg=None, accepts_options=False, is_method=False):
        """Initialize instance.

        :param required: a sequence of required arguments
        :param optional: a sequence of optional arguments
        :param vararg: a variable quantity argument descriptor
        :param accepts_options: indicates whether the underlying python function accepts options as kwargs
        :param is_method: indicates whether the underlying python function accepts `self` as a first argument
        """
        self._required = tuple(required)
        self._optional = tuple(optional)
        self._vararg = vararg
        self._accepts_options = accepts_options
        self._is_method = is_method

    @property
    def required(self):
        """Get required arguments."""
        return self._required

    @property
    def optional(self):
        """Get optional arguments."""
        return self._optional

    @property
    def arguments(self):
        """Get all arguments iterator (required, then optional)."""
        return itertools.chain(self.required, self.optional)

    @property
    def vararg(self):
        """Get var-arg descriptor."""
        return self._vararg

    @property
    def accepts_options(self):
        """Check if the underlying python function accepts options as kwargs."""
        return self._accepts_options

    @property
    def is_method(self):
        """Check if the underlying python function is method accepting `self` as a first argument."""
        return self._is_method


class Command:
    """Cli-command.

    Command represents a single command-line interface method.
    In comandante `Command` is a wrapper around ordinary
    python function, method (or any callable object).

    Command may have arguments. Arguments are parameters
    essential to the command logic.

    Command may have options. Options are parameters that
    are not directly involved in command logic, but may
    affect it's operation in some way.
    """

    @staticmethod
    def from_function(func, name, is_method):
        """Create a new command from the given callable object.

        :param func: a callable object to wrap command around
        :param name: override command name
        :param is_method: indicates whether the underlying `func` accepts `self` as a first argument
        :return: a new Command initialized from the given `func`
        """
        name = name or func.__name__
        brief, descr = describe(func)
        return Command(
            func=func,
            name=name,
            signature=Signature.from_function(func, is_method),
            brief=brief,
            descr=descr
        )

    def __init__(self, func, name, signature, brief, descr):
        """Initialize instance.

        :param func: underlying callable object
        :param name: command name
        :param signature: command signature
        :param brief: command brief description
        :param descr: command long description
        """
        self._func = func
        self._name = name
        self._signature = signature
        self._brief = brief
        self._descr = descr
        self._declared_options = {}
        self._declared_options_short = {}

    def declare_option(self, name, short, type, default, descr=""):
        """Declare a new option for the given command.


        :param name: option name
        :param short: option short name
        :param type: option type
        :param default: option default value
        :param descr: option description
        """
        option = Option(name=name, short=short, type=type, default=default, descr=descr)
        self._declared_options[option.name] = option
        self._declared_options_short[option.short] = option

    @property
    def func(self):
        """Get underlying callable object."""
        return self._func

    @property
    def name(self):
        """Get command name."""
        return self._name

    @property
    def signature(self):
        """Get command signature."""
        return self._signature

    @property
    def brief(self):
        """Get command brief description."""
        return self._brief

    @property
    def descr(self):
        """Get command long description."""
        return self._descr

    @property
    def declared_options(self):
        """Get command options."""
        return self._declared_options  # TODO: use immutable proxy

    def __call__(self, *args, **kwargs):
        """Redirect function-like calls to the underlying function/method."""
        return self.func(*args, **kwargs)

    def invoke(self, handler, *argv):
        """Invoke command with the raw command-line arguments."""
        parser = Parser(self._all_options(handler), self.signature.arguments, self.signature.vararg)
        options, arguments = parser.parse(argv)
        return self._do_invoke(handler, arguments, options)

    def _all_options(self, handler):
        """Merge all declared options."""
        options = {}
        options.update(handler.declared_options)
        options.update(self.declared_options)
        return options.values()

    def _do_invoke(self, handler, arguments, options):
        """Do invoke command with parsed arguments and option values."""
        if self.signature.is_method:
            arguments = (handler.with_options(**options),) + tuple(arguments)
        if self.signature.accepts_options:
            return self.func(*arguments, **options)
        return self.func(*arguments)

    def full_doc(self):
        """Get command full formatted documentation."""
        help_writer = HelpWriter()
        return help_writer.document_command(self)
