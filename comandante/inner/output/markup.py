import re

from comandante.inner.output.token_processor import TokenProcessor


class Ansi:
    """ANSI-terminal control characters"""
    BOLD = '\033[1m'
    NORMAL = '\033[0m'

    @staticmethod
    def bold(text):
        """Make text bold in terminal output."""
        return "{format}{text}{end}".format(format=Ansi.BOLD, text=text, end=Ansi.NORMAL)


def const(value):
    return lambda _: value


class Markup:
    """Docstring markup processor."""

    paragraph_break = re.compile(r'\n\s*\n', re.MULTILINE)

    paragraph_format = TokenProcessor(
        escaped_backslash=(r'\\\\', const('\\')),
        escaped_asterisk=(r'\\\*', const('*')),
        leading_pipe=(r'\n\|', const('\n')),
        escaped_leading_pipe=(r'^\\\|', const('|')),
        trailing_spaces=(r'\s+$', const('')),
        new_line=(r'\n(?=[^|])', const(' ')),
        bold_text=(
            r'\*(?:[^*\\\n]|\\.)+\*',
            lambda text: Ansi.bold(Markup.bold_format.process(text[1:-1]))
        ),
    )

    bold_format = TokenProcessor(
        escaped_backslash=(r'\\\\', const('\\')),
        escaped_asterisk=(r'\\\*', const('*')),
    )

    @staticmethod
    def paragraphs(text):
        paragraphs = Markup.paragraph_break.split(text)
        return map(Markup.paragraph_format.process, paragraphs)

    @staticmethod
    def process(text, delimiter='\n\n'):
        return delimiter.join(Markup.paragraphs(text))
