import re

from comandante.inner.helpers import isblank


class Ansi:
    """ANSI-terminal control characters"""
    BOLD = '\033[1m'
    NORMAL = '\033[0m'

    @staticmethod
    def bold(text):
        """Make text bold in terminal output."""
        return "{format}{text}{end}".format(format=Ansi.BOLD, text=text, end=Ansi.NORMAL)


class DocstringMarkup:
    """Docstring markup processor."""

    class Inline:
        """Lexical rules to process inline formatting."""

        # inline formatting tokens
        tokens = [
            r'(?P<escaped_backslash>\\\\)',
            r'(?P<escaped_asterisk>\\\*)',
            r'(?P<non_escaping_backslash>\\[^*\\])',
            r'(?P<bold_text>\*(?:[^*\\]|\\.)+\*)',
            r'(?P<unmatched_asterisk>\*(?:[^*\\]|\\.)+$)',
            r'(?P<normal_text>[^*\\]+)',
        ]
        pattern = re.compile('|'.join(tokens))

        # token-processing rules
        rules = dict(
            escaped_backslash=lambda text: '\\',
            escaped_asterisk=lambda text: '*',
            non_escaping_backslash=lambda text: text,
            bold_text=lambda text: DocstringMarkup.process_bold_body(text[1:-1]),
            unmatched_asterisk=lambda text: '*' + DocstringMarkup.process_inline_formatting(text[1:]),
            normal_text=lambda text: text,
        )

    class BoldBody:
        """Lexical rules to process escaped symbols inside bold text."""

        tokens = [
            r'(?P<escaped_backslash>\\\\)',
            r'(?P<escaped_asterisk>\\\*)',
            r'(?P<non_escaping_backslash>\\[^*\\])',
            r'(?P<normal_text>[^*\\]+)',
        ]
        pattern = re.compile('|'.join(tokens))

        # token-processing rules
        rules = dict(
            escaped_backslash=lambda text: '\\',
            escaped_asterisk=lambda text: '*',
            non_escaping_backslash=lambda text: text,
            normal_text=lambda text: text,
        )

    @staticmethod
    def process_line(line):
        """Process single docstring line."""
        # process leading |
        if line.startswith('|'):
            line = '\n' + line[1:]
        # process escaped leading |
        elif line.startswith('\\|'):
            line = '|' + line[2:]
        # process inline formatting
        line = DocstringMarkup.process_inline_formatting(line)
        # process trailing white spaces
        line = line.rstrip()
        return line

    @staticmethod
    def process_lines(doc_lines):
        """Convert docstring lines into its final representation.

        The following rules are applied:
         * Blank-lines are converted into the new-line character
         * Lines not delimited by a blank line will be merged into a single line
        """
        paragraphs = []
        paragraph = []

        for line in doc_lines:
            if isblank(line) and len(paragraph) == 0:
                continue
            elif isblank(line):
                paragraphs.append(' '.join(paragraph))
                paragraph = []
            else:
                paragraph.append(DocstringMarkup.process_line(line))
        if len(paragraph) > 0:
            paragraphs.append(' '.join(paragraph))
        return '\n\n'.join(paragraphs)

    @staticmethod
    def process(docstring):
        return DocstringMarkup.process_lines(docstring.split('\n'))

    @staticmethod
    def process_inline_formatting(line):
        inline = DocstringMarkup.Inline
        return DocstringMarkup.process_tokens(line, inline.pattern, inline.rules)

    @staticmethod
    def process_bold_body(body):
        unescaped_body = DocstringMarkup.process_tokens(text=body,
                                                        pattern=DocstringMarkup.BoldBody.pattern,
                                                        rules=DocstringMarkup.BoldBody.rules)
        return Ansi.bold(unescaped_body)

    @staticmethod
    def process_tokens(text, pattern, rules):
        result = []
        for token in pattern.finditer(text):
            for token_type, matched_text in token.groupdict().items():
                if matched_text is not None:
                    rule = rules[token_type]
                    chunk = rule(matched_text)
                    result.append(chunk)
        return ''.join(result)

#
# print(DocstringMarkup.process_inline_formatting("a normal text"))
# print(DocstringMarkup.process_inline_formatting("a *bold* word"))
# print(DocstringMarkup.process_inline_formatting("unmatched *asterisk"))
# print(DocstringMarkup.process_inline_formatting("\\* escaped and *unmatched asterisk"))
# print(DocstringMarkup.process_inline_formatting("\\* escaped and *matched* asterisk"))
# print(DocstringMarkup.process_inline_formatting("a *multiple* bold *words* before *unmatched asterisk"))
# print(DocstringMarkup.process_inline_formatting("escaped symbols *inside \\\\ \\* a \\bold* text"))
# print(DocstringMarkup.process_inline_formatting("escaped backslash in front of a \\\\*bold text*"))
# print(DocstringMarkup.process_inline_formatting("multiple *bold* words *inside* text"))
# print(DocstringMarkup.process_inline_formatting("non-escaping \\backslash"))
