import re
import textwrap

from comandante.inner.helpers import isblank, getname
from comandante.inner.terminal import Terminal


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


class TechWriter:
    """Documentation composer for handlers and commands."""

    def __init__(self, markup=DocstringMarkup, indent=' ' * 4):
        self._terminal = Terminal.detect(max_width=30)
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
