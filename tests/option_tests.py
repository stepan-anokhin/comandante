import unittest

import comandante as cli
import comandante.errors as error
from comandante.inner.test import capture_output, suppress_output


class App(cli.Handler):
    @cli.option('some', 's', int, 0)
    @cli.option('flag', 'f', bool, False)
    @cli.command()
    def test(self, **specified_options):
        return specified_options

    @cli.option('some', 's', int, 0)
    @cli.option('flag', 'f', bool, False)
    @cli.command()
    def test_merge(self, **specified_options):
        return self.test_merge.options(specified_options)


class OptionTests(unittest.TestCase):
    """Integration tests for cli-options."""

    def test_empty_options(self):
        result = App().invoke(['test'])
        self.assertEqual(result, {})

    def test_option_value(self):
        result = App().invoke('test --some 42'.split())
        self.assertEqual(result, {'some': 42})

    def test_boolean_option(self):
        result = App().invoke('test --flag'.split())
        self.assertEqual(result, {'flag': True})

    def test_short_option_value(self):
        result = App().invoke('test -s 42'.split())
        self.assertEqual(result, {'some': 42})

    def test_short_bool_value(self):
        result = App().invoke('test -f'.split())
        self.assertEqual(result, {'flag': True})

    def test_mixed_syntax(self):
        result = App().invoke('test -f --some 42'.split())
        self.assertEqual(result, {'flag': True, 'some': 42})

    def test_merge_options_default_only(self):
        result = App().invoke(['test_merge'])
        self.assertEqual(result, App.test_merge.default_options())

    def test_merge_options_some_specified(self):
        result = App().invoke('test_merge --some 42'.split())
        default = App.test_merge.default_options()
        self.assertEqual(result, {'some': 42, 'flag': default.flag})

    def test_merge_options_all_specified(self):
        result = App().invoke('test_merge --some 42 --flag'.split())
        self.assertEqual(result, {'some': 42, 'flag': True})

    def test_merge_options_attr_access(self):
        options = App().invoke('test_merge --some 42 --flag'.split())
        self.assertEqual(options.some, 42)
        self.assertEqual(options.flag, True)

    def test_merge_options_is_specified(self):
        options = App().invoke('test_merge --some 42'.split())
        self.assertTrue(options.is_specified('some'))
        self.assertFalse(options.is_specified('flag'))

    def test_unknown_are_not_specified(self):
        options = App.test.options({})
        self.assertFalse(options.is_specified('unknown'))

    def test_merge_options_default_attr_access(self):
        options = App().invoke(['test_merge'])
        default = App.test_merge.default_options()
        self.assertEqual(options.some, default.some)
        self.assertEqual(options.flag, default.flag)

    def test_default_options(self):
        default = App.test_merge.default_options()
        self.assertEqual(default, {'flag': False, 'some': 0})

    def test_unknown_long_option(self):
        with suppress_output():
            self.assertRaises(error.UnknownOption, App().test_merge.invoke, ['--unknown'])

    def test_unknown_short_option(self):
        with suppress_output():
            self.assertRaises(error.UnknownOption, App().test_merge.invoke, ['-u'])

    def test_invalid_option_value(self):
        with suppress_output():
            self.assertRaises(error.InvalidValue, App().test_merge.invoke, '--some invalid-value'.split())

    def test_missing_option_value(self):
        with suppress_output():
            self.assertRaises(error.MissingOptionValue, App().test_merge.invoke, ['--some'])

    def test_duplicate_option(self):
        with suppress_output():
            self.assertRaises(error.DuplicateOption, App().test_merge.invoke, '-f --flag'.split())

    def test_error_output(self):
        try:
            with capture_output() as (out, err):
                App().test_merge.invoke(['--unknown'])
        except error.UnknownOption as e:
            self.assertIn(str(e), out.getvalue())
            self.assertIn('--unknown', str(e))

    def test_help_on_option_error(self):
        try:
            with capture_output() as (out, err):
                App().test_merge.invoke(['--unknown'])
        except error.UnknownOption as e:
            self.assertIn(App.test_merge.full_doc(), out.getvalue())
