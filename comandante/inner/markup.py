import re
import textwrap

from comandante.inner.helpers import isblank, getname
from comandante.inner.terminal import Terminal
from comandante.inner.token_processor import TokenProcessor


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
        leading_pipe=(r'^\|', const('\n')),
        escaped_leading_pipe=(r'^\\\|', const('|')),
        trailing_spaces=(r'\s+$', const('')),
        new_line=(r'\n', const(' ')),
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


class Paragraph:
    @staticmethod
    def list(text, delimiter='\n\n'):
        return list(map(Paragraph, text.split(delimiter)))

    def __init__(self, text, initial_indent='', subsequent_indent=''):
        self._text = text
        self._initial_indent = initial_indent
        self._subsequent_indent = subsequent_indent

    def indent(self, indent=' ' * 4):
        self._initial_indent = indent + self._initial_indent
        self._subsequent_indent = indent + self._subsequent_indent
        return self

    @property
    def text(self):
        return self._text

    @property
    def initial_indent(self):
        return self._initial_indent

    @property
    def subsequent_indent(self):
        return self._subsequent_indent


class HelpWriter:
    """Documentation composer for handlers and commands."""

    def __init__(self, markup=Markup, indent=' ' * 4):
        self._terminal = Terminal.detect()
        self._markup = markup
        self._indent_unit = indent

    def markup(self, text):
        return self._markup.process(text)

    def indent(self, text, amount=1):
        """Indent entire text with the given amount of indentation units."""
        lines = text.split('\n')
        indent = self._indent_unit * amount
        return '\n'.join(map(indent.__add__, lines))

    @staticmethod
    def unindent(text):
        """Remove common indent."""
        if text.startswith('\n') or '\n' not in text:
            return textwrap.dedent(text)
        first, rest = text.split('\n', maxsplit=1)
        rest = textwrap.dedent(rest)
        return '\n'.join((first, rest))

    def document_handler(self, handler):
        sections = list()
        sections.append(self.name_section(handler))
        sections.append(self.commands_section(handler))
        sections.append(self.description_section(handler))
        sections.append(self.options_section(handler))
        return self.compose_sections(sections)

    def document_command(self, command):
        sections = list()
        sections.append(self.name_section(command))
        sections.append(self.synopsis_section(command))
        sections.append(self.description_section(command))
        sections.append(self.options_section(command))
        return self.compose_sections(sections)

    def name_section(self, element):
        """Create name section for the cli element."""
        if not element.brief:
            return None

        text = "{name} - {brief}".format(name=element.name, brief=element.brief)
        return self.section(heading="name", body=text)

    def commands_section(self, handler):
        """Get summary for all defined commands."""
        if not handler.declared_commands:
            return

        names, briefs = list(), list()
        for name in sorted(handler.declared_commands.keys()):
            command = handler.declared_commands[name]
            names.append(command.name)
            briefs.append(command.brief)
        name_column_width = max(map(len, names))

        paragraphs = list()
        for name, brief in zip(names, briefs):
            name_entry = "{name:<{width}}".format(name=name, width=name_column_width)
            paragraph = self.comment(what=name_entry, comment=brief)
            paragraphs.append(paragraph)
        return self.section_paragraphs(heading="commands", paragraphs=paragraphs, delimiter='\n')

    def description_section(self, element):
        """Get formatted description for cli element."""
        if not element.descr:
            return

        text = self.markup(element.descr)
        return self.section_paragraphs(heading="description", paragraphs=Paragraph.list(text))

    def section_paragraphs(self, heading, paragraphs, delimiter='\n\n'):
        heading = Ansi.bold(heading.upper())

        body = list()
        for paragraph in paragraphs:
            paragraph.indent(self._indent_unit)
            body.append(self.wrap(paragraph))
        body = delimiter.join(body)
        return "{heading}\n{body}".format(heading=heading, body=body)

    def wrap(self, paragraph):
        wrapper = textwrap.TextWrapper(
            initial_indent=paragraph.initial_indent,
            subsequent_indent=paragraph.subsequent_indent,
            width=self._terminal.width)
        return '\n'.join(wrapper.wrap(paragraph.text))

    def section(self, heading, body):
        heading = Ansi.bold(heading.upper())
        # body = self.indent(body)

        result = list()
        wrapper = textwrap.TextWrapper(initial_indent=self._indent_unit,
                                       subsequent_indent=self._indent_unit,
                                       width=self._terminal.width)
        for line in body.split('\n'):
            if isblank(line):
                result.append(line)
                continue
            result.extend(wrapper.wrap(line))
        body = '\n'.join(result)

        return "{heading}\n{body}".format(heading=heading, body=body)

    @staticmethod
    def compose_sections(sections):
        sections = filter(bool, sections)
        return '\n\n'.join(sections)

    def synopsis_section(self, command):
        """Get formatted usage."""
        synopsis = list()
        synopsis.append(command.name)
        if command.declared_options:
            synopsis.append("[OPTIONS]")
        for argument in command.signature.arguments:
            pattern = self.argument_pattern(argument)
            synopsis.append(pattern.format(name=argument.name))
        synopsis = ' '.join(synopsis)

        return self.section(heading="synopsis", body=synopsis)

    @staticmethod
    def argument_pattern(argument):
        """Get argument pattern."""
        if argument.is_required:
            return "<{name}>"
        return "[{name}]"

    def options_section(self, element):
        """Get cli element options summary."""
        if not element.declared_options:
            return

        summarized_options = map(self.summarize_option, element.declared_options.values())
        summarized_options = '\n\n'.join(summarized_options)
        return self.section(heading="options", body=summarized_options)

    def summarize_option(self, option):
        """Get option summary."""
        pattern = self.option_pattern(option)
        synopsis = pattern.format(long=option.name, short=option.short, type=getname(option.type))
        summary = [synopsis]

        if option.descr:
            description = self.markup(self.unindent(option.descr))
            summary.append(self.indent(description))
        return '\n'.join(summary)

    def comment(self, what, comment):
        if not comment:
            return Paragraph(what)
        initial = "{text}{indent}#{indent}".format(text=what, indent=self._indent_unit)
        subsequent = " " * len(initial)
        return Paragraph(text=comment, initial_indent=initial, subsequent_indent=subsequent)

    @staticmethod
    def option_pattern(option):
        """Get option synopsis pattern."""
        if option.type is bool:
            return "-{short}, --{long}"
        return "-{short} <{type}>, --{long} <{type}>"
