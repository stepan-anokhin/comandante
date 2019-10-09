import textwrap
from itertools import chain

from comandante.inner.helpers import getname
from comandante.inner.output.markup import Markup, Ansi
from comandante.inner.output.terminal import Terminal


class Paragraph:
    @staticmethod
    def list(text, delimiter='\n\n'):
        return list(map(Paragraph, text.split(delimiter)))

    def __init__(self, text, initial_indent='', subsequent_indent=None):
        self._text = text
        self._initial_indent = initial_indent
        self._subsequent_indent = subsequent_indent if subsequent_indent is not None else initial_indent

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

    def paragraphs(self, text):
        return map(Paragraph, self._markup.paragraphs(text))

    def indent(self, text, amount=1):
        """Indent entire text with the given amount of indentation units."""
        lines = text.split('\n')
        indent = self._indent_unit * amount
        return '\n'.join(map(indent.__add__, lines))

    @staticmethod
    def dedent(text):
        """Remove common indent."""
        if text.startswith('\n') or '\n' not in text:
            return textwrap.dedent(text)
        first, rest = text.split('\n', maxsplit=1)
        rest = textwrap.dedent(rest)
        return '\n'.join((first, rest))

    def name_section(self, element):
        """Create name section for the cli element."""
        if not element.brief:
            return None

        text = "{name} - {brief}".format(name=element.name, brief=element.brief)
        return self.section(heading="name", paragraphs=[Paragraph(text)])

    def synopsis_section(self, command):
        """Get formatted usage."""
        synopsis = list()
        synopsis.append(command.name)
        if command.declared_options:
            synopsis.append("[OPTIONS]")
        for argument in command.signature.arguments:
            pattern = self.argument_pattern(argument)
            synopsis.append(pattern.format(name=argument.name))
        if command.signature.vararg is not None:
            pattern = "[{name} ... ]"
            synopsis.append(pattern.format(name=command.signature.vararg.name))
        synopsis = ' '.join(synopsis)

        return self.section(heading="synopsis", paragraphs=[Paragraph(synopsis)])

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
            paragraph.margin_bottom = 0
            paragraphs.append(paragraph)
        return self.section(heading="commands", paragraphs=paragraphs, delimiter='\n')

    def description_section(self, element):
        """Get formatted description for cli element."""
        if not element.descr:
            return

        paragraphs = self.paragraphs(element.descr)
        return self.section(heading="description", paragraphs=paragraphs)

    def options_section(self, element):
        """Get cli element options summary."""
        if not element.declared_options:
            return

        declared_options = element.declared_options.values()
        summarized_options = map(self.summarize_option, declared_options)
        return self.section(heading="options", paragraphs=chain(*summarized_options))

    def section(self, heading, paragraphs, delimiter='\n\n'):
        heading = Ansi.bold(heading.upper())

        body = list()
        for paragraph in paragraphs:
            paragraph.indent(self._indent_unit)
            body.append(self.wrap(paragraph))
        body = delimiter.join(body)
        return "{heading}\n{body}".format(heading=heading, body=body)

    def wrap(self, paragraph):
        # first line wrapper
        first = textwrap.TextWrapper(
            initial_indent=paragraph.initial_indent,
            subsequent_indent=paragraph.subsequent_indent,
            width=self._terminal.width)

        # subsequent lines wrapper
        subsequent = textwrap.TextWrapper(
            initial_indent=paragraph.subsequent_indent,
            subsequent_indent=paragraph.subsequent_indent,
            width=self._terminal.width)

        paragraph_lines = paragraph.text.split('\n')
        wrapped_lines = first.wrap(paragraph_lines[0])
        for line in paragraph_lines[1:]:
            wrapped_lines.extend(subsequent.wrap(line))
        return '\n'.join(wrapped_lines)

    @staticmethod
    def compose_sections(sections):
        sections = filter(bool, sections)
        return '\n\n'.join(sections)

    @staticmethod
    def argument_pattern(argument):
        """Get argument pattern."""
        if argument.is_required():
            return "<{name}>"
        return "[{name}]"

    def summarize_option(self, option):
        """Get option summary."""
        paragraphs = []
        descr_paragraphs = self.paragraphs(self.dedent(option.descr))

        pattern = self.option_pattern(option)
        synopsis = pattern.format(long=option.name, short=option.short, type=getname(option.type))
        first_paragraph_text = "{synopsis}\n{text}".format(synopsis=synopsis, text=next(descr_paragraphs).text)
        first_paragraph = Paragraph(first_paragraph_text, initial_indent='', subsequent_indent=self._indent_unit)

        paragraphs.append(first_paragraph)
        for paragraph in descr_paragraphs:
            paragraph.indent(self._indent_unit)
            paragraphs.append(paragraph)

        return paragraphs

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