import os.path
import re
from itertools import filterfalse, takewhile, islice, chain

from comandante.inner.helpers import isblank, getname


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


class TechWriter:
    """Documentation composer for handlers and commands."""

    def __init__(self, markup=DocstringMarkup, indent=' ' * 4):
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
        lines = text.split('\n')
        indent_width = len(TechWriter.indentation(islice(lines, 1, None)))
        unindented_lines = map(lambda line: line[indent_width:], islice(lines, 1, None))
        return '\n'.join(chain(islice(lines, 0, 1), unindented_lines))

    @staticmethod
    def indentation(lines):
        """Get common blank prefix of all non-blank lines."""
        non_blank_lines = list(filterfalse(isblank, lines))
        common_prefix = os.path.commonprefix(non_blank_lines)
        return ''.join(takewhile(isblank, common_prefix))

    def document_handler(self, handler):
        sections = list()
        sections.append(self.name_section(handler))
        sections.append(self.commands_section(handler))
        sections.append(self.description_section(handler))
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

        lines = list()
        pattern = "{name:<{width}}{indent}#{indent}{brief}"
        for name, brief in zip(names, briefs):
            entry = pattern.format(name=name, brief=brief, width=name_column_width, indent=self._indent_unit)
            lines.append(entry)
        text = '\n'.join(lines)
        return self.section(heading="commands", body=text)

    def description_section(self, element):
        """Get formatted description for cli element."""
        if not element.descr:
            return

        text = self.markup(element.descr)
        return self.section(heading="description", body=text)

    def section(self, heading, body):
        heading = Ansi.bold(heading.upper())
        body = self.indent(body)
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

    @staticmethod
    def option_pattern(option):
        """Get option synopsis pattern."""
        if option.type is bool:
            return "-{short}, --{long}"
        return "-{short} <{type}>, --{long} <{type}>"
