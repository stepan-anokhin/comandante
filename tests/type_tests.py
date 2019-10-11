import unittest

import comandante as cli
from comandante.inner.helpers import getname


class TypeTests(unittest.TestCase):
    """Custom type tests."""

    def test_choice_valid(self):
        valid = ('first', 'second')
        choice = cli.choice(*valid)
        self.assertEqual(choice(valid[0]), valid[0])
        self.assertEqual(choice(valid[1]), valid[1])

    def test_choice_invalid(self):
        choice = cli.choice('a', 'b')
        self.assertRaises(ValueError, choice, 'unknown')

    def test_choice_name(self):
        valid = ('first', 'second')
        choice = cli.choice(*valid)
        self.assertEqual(getname(choice), '|'.join(valid))

    def test_listof_valid(self):
        list_of_int = cli.listof(int)
        self.assertEqual(list_of_int('0,1,2,3,4'), list(range(5)))

    def test_listof_invalid(self):
        list_of_int = cli.listof(int)
        self.assertRaises(ValueError, list_of_int, 'a,b,c')

    def test_listof_name(self):
        list_of_int = cli.listof(int)
        self.assertEqual(getname(list_of_int), 'listof(int)')
