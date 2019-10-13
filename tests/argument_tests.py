import unittest

import comandante as cli
import comandante.errors as error
from comandante.inner.test import suppress_output, capture_output


class App(cli.Handler):
    @cli.signature(int_arg=int)
    @cli.command()
    def test_int(self, int_arg):
        return int_arg

    @cli.signature(bool_arg=bool, int_arg=int)
    @cli.command()
    def test_types(self, str_arg, bool_arg, int_arg):
        return str_arg, bool_arg, int_arg

    @cli.command()
    def test_default(self, required, optional='default'):
        return required, optional

    @cli.command()
    def test_no_arguments(self):
        return 'success'

    @cli.signature(vararg=int)
    @cli.command()
    def test_vararg(self, required, optional='default', *vararg):
        return required, optional, vararg


class ArgumentTests(unittest.TestCase):
    """Integration tests for cli-argument passing."""

    def test_return_value(self):
        result = App().invoke(['test_no_arguments'])
        self.assertEqual(result, 'success')

    def test_argument_types(self):
        result = App().invoke('test_types string bool_arg 42'.split())
        self.assertEqual(result, ('string', True, 42))

    def test_argument_default_value(self):
        result = App().invoke('test_default required'.split())
        self.assertEqual(result, ('required', 'default'))

    def test_argument_override_default(self):
        result = App().invoke('test_default required override'.split())
        self.assertEqual(result, ('required', 'override'))

    def test_argument_vararg_zero_values(self):
        result = App().invoke('test_vararg required override'.split())
        self.assertEqual(result, ('required', 'override', ()))

    def test_argument_vararg_one_value(self):
        result = App().invoke('test_vararg required override 1'.split())
        self.assertEqual(result, ('required', 'override', (1,)))

    def test_argument_vararg_multiple_values(self):
        result = App().invoke('test_vararg required override 1 2 3 4'.split())
        self.assertEqual(result, ('required', 'override', (1, 2, 3, 4)))

    def test_argument_vararg_no_optional(self):
        result = App().invoke('test_vararg required '.split())
        self.assertEqual(result, ('required', 'default', ()))

    def test_argument_invalid_value(self):
        with suppress_output():
            self.assertRaises(error.InvalidArgumentValue, App().test_int.invoke, 'test_int invalid'.split())

    def test_argument_missing_value(self):
        with suppress_output():
            self.assertRaises(error.ArgumentMissing, App().test_default.invoke, ())

    def test_too_many_arguments(self):
        with suppress_output():
            self.assertRaises(error.TooManyArguments, App().test_default.invoke, 'required optional extra'.split())

    def test_argument_error_message(self):
        try:
            with capture_output() as (out, err):
                App().test_int.invoke('invalid'.split())
        except error.InvalidArgumentValue as e:
            self.assertIn(str(e), out.getvalue())
            self.assertIn('int_arg', str(e))

    def test_help_on_argument_error(self):
        try:
            with capture_output() as (out, err):
                App().test_int.invoke('invalid'.split())
        except error.InvalidArgumentValue as e:
            self.assertIn(App().test_int.full_doc(), out.getvalue())
