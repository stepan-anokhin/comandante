import unittest

from comandante.inner.bind import ImmutableDict, AttributeDict
from comandante.inner.proxy import Proxy


class ProxyTests(unittest.TestCase):
    def test_proxy_comparison_operations(self):
        value = 42
        proxy = Proxy(value)
        self.assertEqual(proxy, value)
        self.assertNotEqual(proxy, value + 1)
        self.assertTrue(proxy <= value)
        self.assertTrue(proxy >= value)
        self.assertTrue(proxy <= value + 1)
        self.assertTrue(proxy >= value - 1)
        self.assertTrue(proxy < value + 1)
        self.assertTrue(proxy > value - 1)

    def test_proxy_element_access(self):
        value = {'key': 42}
        proxy = Proxy(value)
        self.assertEqual(len(proxy), len(value))
        self.assertEqual(proxy['key'], value['key'])
        self.assertIn('key', proxy)

    def test_proxy_element_assign(self):
        value = {}
        proxy = Proxy(value)
        proxy['new_key'] = 'new_value'
        self.assertIn('new_key', proxy)
        self.assertIn('new_key', value)
        self.assertTrue(proxy['new_key'] == value['new_key'] == 'new_value')

    def test_proxy_element_delete(self):
        value = {'key': 42}
        proxy = Proxy(value)
        del proxy['key']
        self.assertNotIn('key', proxy)
        self.assertNotIn('key', value)
        self.assertTrue(proxy == value == {})

    def test_proxy_builtin_methods(self):
        value = "some-string"
        proxy = Proxy(value)

        self.assertEqual(str(proxy), str(value))
        self.assertEqual(repr(proxy), repr(value))
        self.assertEqual(hash(proxy), hash(value))

    def test_immutable_dict_reject_mutating_operations(self):
        data = {'key': 42}
        proxy = ImmutableDict(data)

        def assign():
            proxy['new_key'] = 'new_value'

        def delete():
            del proxy['key']

        self.assertRaises(TypeError, proxy.clear)
        self.assertRaises(TypeError, proxy.pop, 'key')
        self.assertRaises(TypeError, proxy.popitem)
        self.assertRaises(TypeError, proxy.update, {'new_key': 'new_value'})
        self.assertRaises(TypeError, assign)
        self.assertRaises(TypeError, delete)

    def test_attribute_dict_attribute_access(self):
        data = {'key': 42}
        proxy = AttributeDict(data)

        self.assertEqual(proxy.key, data['key'])

    def test_attribute_dict_unknown_attribute_access(self):
        data = {'key': 42}
        proxy = AttributeDict(data)

        self.assertRaises(AttributeError, lambda: proxy.unknown)
