import unittest

import comandante as cli
import comandante.errors as error
from comandante.inner.test import suppress_output, capture_output


class SubCommand(cli.Handler):
    @cli.command()
    def command(self, **specified_options):
        return specified_options


class App(cli.Handler):
    def __init__(self):
        super(App, self).__init__()

        self.declare_option('global', 'g', bool, False)
        self.declare_command('subcommand', SubCommand())

    @cli.option('local', 'l', int, 0)
    @cli.command()
    def command(self, **specified_options):
        return specified_options


class BasicTests(unittest.TestCase):
    """Integration tests for basic Handler and Command properties."""

    def test_print_help_by_default(self):
        app = App()
        with capture_output() as (out, err):
            app.invoke([])
        self.assertEqual(app.full_doc(), out.getvalue().rstrip())

    def test_unknown_command(self):
        with suppress_output():
            self.assertRaises(error.UnknownCommand, App().invoke, ['unknown'])

    def test_help_subcommand(self):
        app = App()
        with capture_output() as (out, err):
            app.invoke('help subcommand command'.split())
        output = out.getvalue().rstrip()
        full_name = 'app subcommand command'.split()
        self.assertEqual(output, app.subcommand.command.full_doc(full_name))

    def test_help_on_unknown_subcommand(self):
        app = App()
        try:
            with capture_output() as (out, err):
                app.invoke('subcommand unknown'.split())
        except error.UnknownCommand as e:
            subcommand_doc = app.subcommand.full_doc(full_name='app subcommand'.split())
            self.assertIn(str(e), out.getvalue())
            self.assertIn(subcommand_doc, out.getvalue())

    def test_help_of_command_subcommand(self):
        app = App()
        with capture_output() as (out, err):
            app.invoke('help subcommand command unknown'.split())
        full_name = 'app subcommand command'.split()
        command_doc = app.subcommand.command.full_doc(full_name)
        self.assertIn(command_doc, out.getvalue())

    def test_forward_global_options(self):
        app = App()
        self.assertEqual(set(app.declared_options.keys()), {'global'})
        self.assertEqual(set(app.command.declared_options.keys()), {'global', 'local'})
        self.assertEqual(set(app.subcommand.declared_options.keys()), {'global'})
        self.assertEqual(set(app.subcommand.command.declared_options.keys()), {'global'})

    def test_subcommand_use_global_option(self):
        result = App().invoke('subcommand command -g'.split())
        self.assertEqual(result, {'global': True})

    def test_command_use_global_option(self):
        result = App().invoke('command -g -l 42'.split())
        self.assertEqual(result, {'global': True, 'local': 42})

    def test_handler_has_empty_doc(self):
        handler = cli.Handler()
        self.assertEqual(handler.brief, '')
        self.assertEqual(handler.descr, '')

    def test_duplicate_command(self):
        self.assertRaises(RuntimeError, App().declare_command, 'subcommand', SubCommand())

    def test_duplicate_global_option_long_name(self):
        self.assertRaises(RuntimeError, App().declare_option, 'global', 'unique', int, 0)

    def test_duplicate_global_option_short_name(self):
        self.assertRaises(RuntimeError, App().declare_option, 'unique', 'g', int, 0)

    def test_duplicate_local_option_long_name(self):
        self.assertRaises(RuntimeError, App().command.declare_option, 'local', 'unique', int, 0)

    def test_duplicate_local_option_short_name(self):
        self.assertRaises(RuntimeError, App().command.declare_option, 'unique', 'l', int, 0)
