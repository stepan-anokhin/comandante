"""Comandante domain model.

Description:
-----------

This module contains classes that describes notions
defined by the comandante toolkit: Commands, Options, etc.

This model classes are more or less declarations needed
for parsers and executors to interpret command line
arguments and execute the corresponding logic.
"""

from __future__ import print_function

import inspect
import itertools
import re
import sys

from comandante.errors import CliSyntaxException
from comandante.inner.bind import ImmutableDict, AttributeDict
from comandante.inner.helpers import describe
from comandante.inner.output.help_writer import HelpWriter
from comandante.inner.parser import Parser


class _Empty:
    """Marker object for Argument.empty"""


class Option(object):
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
    _name_pattern = re.compile(r'^[a-zA-Z]\w+$')

    @staticmethod
    def is_valid_name(name):
        """Validate otion name.

        :param name: option name to be validated
        :return: True iff name is a valid option name
        """
        return isinstance(name, str) and bool(Option._name_pattern.match(name))

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


class Argument(object):
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

    def __init__(self, name, type, default=empty):
        """Initialize instance.

        :param name: argument name
        :param type: argument type
        :param default: default value (Argument.empty if not present)
        """
        self.type = type
        self._name = name
        self._default = default

    @property
    def name(self):
        """Get argument name."""
        return self._name

    @property
    def default(self):
        """Get argument default value."""
        return self._default

    def is_required(self):
        """Check if argument is required."""
        return self.default is Argument.empty


class Signature(object):
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
        if sys.version_info > (3, 0):
            sig = inspect.signature(func)
            return Signature._from_signature(sig, is_method)
        else:
            spec = inspect.getargspec(func)
            return Signature._from_argspec(spec, is_method)

    @staticmethod
    def _from_argspec(spec, is_method):
        vararg = None
        accepts_options = spec.keywords is not None
        if spec.varargs is not None:
            vararg = Argument(name=spec.varargs, type=str, default=Argument.empty)
        argument_names = spec.args
        if is_method:
            argument_names = argument_names[1:]

        defaults = spec.defaults or ()
        required_count = len(argument_names) - len(defaults)
        required_names = argument_names[:required_count]
        optional_names = argument_names[required_count:]
        required = []
        optional = []
        for name in required_names:
            required.append(Argument(name, str))
        for name, value in zip(optional_names, defaults):
            optional.append(Argument(name, str, default=value))
        return Signature(
            required=required,
            optional=optional,
            vararg=vararg,
            accepts_options=accepts_options,
            is_method=is_method
        )

    @staticmethod
    def _from_signature(sig, is_method):
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

    def copy(self):
        """Create a fresh copy of the Signature instance."""
        return Signature(
            required=self.required,
            optional=self.optional,
            vararg=self.vararg,
            accepts_options=self.accepts_options,
            is_method=self.is_method)

    def set_types(self, types):
        for argument in self.arguments:
            if argument.name in types:
                argument.type = types[argument.name]
        if self.vararg is not None and self.vararg.name in types:
            self.vararg.type = types[self.vararg.name]


class Command(object):
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
        self._declared_options_short = set()

    def declare_option(self, name, short, type, default, descr=""):
        """Declare a new option for the given command.


        :param name: option name
        :param short: option short name
        :param type: option type
        :param default: option default value
        :param descr: option description
        """
        if name in self._declared_options:
            raise RuntimeError("Duplicate option '--{option}' for command '{name}'".format(option=name, name=self.name))
        if short in self._declared_options_short:
            raise RuntimeError("Duplicate option '-{option}' for command '{name}'".format(option=short, name=self.name))
        option = Option(name=name, short=short, type=type, default=default, descr=descr)
        self._declared_options[option.name] = option
        self._declared_options_short.add(short)

    def use_option(self, option):
        """Declare identical option."""
        self.declare_option(
            name=option.name,
            short=option.short,
            type=option.type,
            default=option.default,
            descr=option.descr)

    def use_options(self, options):
        """Declare identical options."""
        for option in options:
            self.use_option(option)

    def default_options(self):
        """Get default option values."""
        return Options({}, self.declared_options.values())

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
        return ImmutableDict(self._declared_options)

    @property
    def declared_commands(self):
        """Always return empty dict"""
        return dict()

    def options(self, specified_options):
        """Get merged options values."""
        return Options(specified_options, self.declared_options.values())

    def __call__(self, *args, **kwargs):
        """Redirect function-like calls to the underlying function/method."""
        return self.func(*args, **kwargs)

    def invoke(self, handler, argv, context=None):
        """Invoke command with the raw command-line arguments."""
        context = context or (self.name,)
        try:
            parser = Parser(self.declared_options.values(), self.signature.arguments, self.signature.vararg)
            options, arguments = parser.parse(argv)
        except CliSyntaxException as e:
            print(e)
            print(self.full_doc(full_name=context))
            raise
        return self._do_invoke(handler, arguments, options)

    def _do_invoke(self, handler, arguments, options):
        """Do invoke command with parsed arguments and option values."""
        if self.signature.is_method:
            arguments = (handler,) + tuple(arguments)
        if self.signature.accepts_options:
            return self.func(*arguments, **options)
        return self.func(*arguments)

    def full_doc(self, full_name=None):
        """Get command full formatted documentation."""
        help_writer = HelpWriter()
        return help_writer.document_command(self, full_name)

    def copy(self):
        """Create a fresh copy of the command instance."""
        copy = Command(
            func=self.func,
            name=self.name,
            signature=self.signature.copy(),
            brief=self.brief,
            descr=self.descr)
        copy.use_options(self.declared_options.values())
        return copy


class Options(AttributeDict):
    def __init__(self, specified, declared):
        super(Options, self).__init__(dict())
        self._set('_specified', set(specified.keys()))
        for option in declared:
            self._target[option.name] = option.default
        self._target.update(specified)

    def is_specified(self, name):
        """Check if option is specified."""
        return name in self._specified
