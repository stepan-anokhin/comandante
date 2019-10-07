import unittest

from comandante.inner.output.markup import Ansi, Markup


class DocstringMarkupTests(unittest.TestCase):
    def assert_process(self, text, expected_output, message=None):
        self.assertEqual(Markup.process(text), expected_output, message)

    def test_normal_text(self):
        self.assert_process("a normal text",
                            "a normal text")

    def test_bold_word(self):
        self.assert_process("a bold *word* inside",
                            "a bold {word} inside".format(word=Ansi.bold("word")))

    def test_unmatched_asterisk(self):
        self.assert_process("unmatched *asterisk",
                            "unmatched *asterisk")

    def test_escaped_before_unmatched_asterisk(self):
        self.assert_process("\\*escaped before *unmatched asterisk",
                            "*escaped before *unmatched asterisk")

    def test_unmatched_before_escaped_asterisk(self):
        self.assert_process("*unmatched before \\*escaped asterisk",
                            "*unmatched before *escaped asterisk")

    def test_escaped_and_matched_asterisk(self):
        self.assert_process("\\*escaped and *matched* asterisk",
                            "*escaped and {matched} asterisk".format(matched=Ansi.bold("matched")))

    def test_matched_before_unmatched_asterisk(self):
        self.assert_process("*matched* before *unmatched",
                            "{matched} before *unmatched".format(matched=Ansi.bold("matched")))

    def test_multiple_bold_before_unmatched_asterisk(self):
        self.assert_process("*first* and *second* before *unmatched",
                            "{first} and {second} before *unmatched".format(first=Ansi.bold("first"),
                                                                            second=Ansi.bold("second")))

    def test_escaped_symbols_in_bold_text(self):
        self.assert_process("escaped *symbols \\\\ \\* inside* bold text",
                            "escaped {symbols_inside} bold text".format(
                                symbols_inside=Ansi.bold("symbols \\ * inside")))

    def test_escaped_backslash_in_front_of_bold(self):
        self.assert_process("escaped \\\\*backslash* before bold",
                            "escaped \\{backslash} before bold".format(backslash=Ansi.bold("backslash")))

    def test_multiple_bold_words(self):
        self.assert_process("multiple *bold* words *inside* text",
                            "multiple {bold} words {inside} text".format(bold=Ansi.bold("bold"),
                                                                         inside=Ansi.bold("inside")))

    def test_non_escaping_backslash(self):
        self.assert_process("non escaping \\backslash",
                            "non escaping \\backslash")

    def test_trailing_spaces(self):
        self.assert_process("with trailing spaces    ",
                            "with trailing spaces")

    def test_paragraph_breaking(self):
        self.assert_process("first  \nparagraph\n\n  \n \nsecond\nparagraph",
                            "first paragraph\n\nsecond paragraph")
