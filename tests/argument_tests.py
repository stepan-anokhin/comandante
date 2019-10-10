import unittest

import comandante as cli


class ComandanteBasicIntegrationTests(unittest.TestCase):
    def test_return_value(self):
        expected = 42

        class Application(cli.Handler):
            @cli.command()
            def test(self):
                return expected

        actual = Application().invoke('test')
        self.assertEqual(actual, expected)

    def test_string_arguments(self):
        arguments = ('hello', 'world')

        class Application(cli.Handler):
            @cli.command()
            def test(self, first, second):
                return first, second

        result = Application().invoke('test', *arguments)
        self.assertEqual(result, arguments)

    def test_argument_types(self):
        class Application(cli.Handler):
            @cli.command()
            def test(self, argument: int):
                return argument

        result = Application().invoke('test', '42')
        self.assertEqual(result, 42)
