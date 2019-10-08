import unittest

from comandante.inner.helpers import describe


class DescribeTests(unittest.TestCase):
    def test_empty_doc(self):
        def no_docs():
            pass

        brief, descr = describe(no_docs)
        self.assertEqual(brief, '')
        self.assertEqual(descr, '')

    def test_func_doc(self):
        def brief_and_long(self):
            """Brief description

            Long description
            """

        brief, descr = describe(brief_and_long)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "Long description")

    def test_class_doc(self):
        class BriefAndLong:
            """Brief description

            Long description
            """

        brief, descr = describe(BriefAndLong)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "Long description")

    def test_brief_only(self):
        def brief_only():
            """Brief description"""

        brief, descr = describe(brief_only)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "")

    def test_brief_only_empty_lines(self):
        def brief_only():
            """Brief description


            """

        brief, descr = describe(brief_only)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "")

    def test_empty_lines(self):
        def with_empty_lines():
            """Brief description



            Long description
            """

        brief, descr = describe(with_empty_lines)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "Long description")

    def test_multiline(self):
        def multiline():
            """Brief description

            First

            Second
            """

        brief, descr = describe(multiline)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "First\n\nSecond")

    def test_multiline_brief(self):
        def multiline_brief():
            """Multiline
            brief description

            Multiline

            long
            description
            """

        brief, descr = describe(multiline_brief)
        self.assertEqual(brief, "Multiline\nbrief description")
        self.assertEqual(descr, "Multiline\n\nlong\ndescription")

    def test_leading_spaces(self):
        def leading_spaces():
            """      Brief description

            Long description
            """

        brief, descr = describe(leading_spaces)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "Long description")

    def test_leading_blank_lines(self):
        def leading_blank_lines():
            """

            Brief description

            Long description
            """

        brief, descr = describe(leading_blank_lines)
        self.assertEqual(brief, "Brief description")
        self.assertEqual(descr, "Long description")
