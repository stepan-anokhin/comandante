
<p align="center">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/logo.png" width="500" alt="Comandante Logo">
</p>

Comandante is a toolkit for building command-line interfaces in Python.

[![Build Status](https://travis-ci.org/stepan-anokhin/comandante.svg?branch=master)](https://travis-ci.org/stepan-anokhin/comandante)
[![Coverage Status](https://coveralls.io/repos/github/stepan-anokhin/comandante/badge.svg?branch=master)](https://coveralls.io/github/stepan-anokhin/comandante?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/stepan-anokhin/comandante/blob/master/LICENSE)

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Example](#Example)
  - [Just a Normal Classes and Methods!](#just-a-normal-classes-and-methods)
- [Options](#options)
  - [Command Options](#command-options)
  - [Class Options](#class-options)
- [Subcommands](#subcommands)
- [Arguments](#arguments)
  - [Type Library](#type-library)
  - [Python 2](#python-2)
- [Printing Help](#printing-help)
- [Error Handling](#error-handling)
- [Testing Your CLI](#testing-your-cli)

## Installation

To get the latest release simply install it with a `pip`:

```shell
pip3 install --upgrade comandante
```

## Getting Started

Some command-line interfaces (like `pip`, `git`, `go`, etc.) 
have a rich hierarchy of subcommands. Each subcommand may have
its own set of arguments and options. Consider for example 
`git commit`, `git remote add <repo>`, `git remote rename <old> <new>`
etc. *Comandante* is a Python library that makes building
rich command-line interfaces (CLI) in Python extremely simple 
and straightforward. 

### Example
Here is a simple example:
```python
#!/usr/bin/env python3
import sys, comandante as cli

# Define a new CLI handler as a `cli.Handler` subclass
class CliTool(cli.Handler):

    # define CLI commands as methods decorated with `@cli.command()` 
    @cli.command()
    def repeat(self, message, times: int):
        for i in range(times):
            print(message)
           
    @cli.command() 
    def sum(self, a: int, b: int):
        result = a + b
        print(result)
        return result
            
# Then simply pass command-line arguments to the CliTool#invoke
CliTool().invoke(sys.argv[1:])
```

That's it! 

To execute `repeat` command simply run `./tool repeat` with its required arguments:
```shell
$ ./tool repeat "Hello world" 2
Hello world
Hello world
```

The same goes for any defined command-methods: 
```shell
$ ./tool sum 21 21
42
```
So in other words to create a command-line interface you simply:
 * define a normal Python class (inherited from the `comandante.Handler`)
 * equip your class methods with a minimal amount of metadata (via decorators)
 * call `invoke(sys.argv[1:])` method on your class instance
 * **comandante** will inspect metadata and decide how to parse 
 command-line arguments and which method to call.  


### Just a Normal Classes and Methods
No surprises! Handlers and commands are just a normal classes and methods.

## Options
Command options are declared with `@comandante.option(...)` decorator. 

Each command-method receives options as `**kwargs` parameters (if present). 

Each command-method has a convenience method `Command#options(kwargs)` to 
merge default values with specified command-line options.

### Command Options

Example below demonstrates how to define command option:

```python
#!/usr/bin/env python3
import sys, comandante as cli

 
class DatabaseCli(cli.Handler):

    @cli.option(name='force', short='f', type=bool, default=False)
    @cli.command()
    def drop(self, database_name, **specified_options):
        # merge specified options with default values
        options = self.drop.options(specified_options)
        
        # merged options provides attribute-like element access
        if options.force or self.confirm():
            print("Database '{name}' was deleted".format(name=database_name))
        else: 
            print("Aborted")
            
    @staticmethod        
    def confirm():
        question = 'Are you sure? [y/N]: '
        value = input(question).lower()
        while value not in ['', 'n', 'y']:
            print("Please answer 'y' or 'n'")
            value = input(question)
        return value == 'y'


database_cli = DatabaseCli()
database_cli.invoke(sys.argv[1:])
```
Then in shell:
```shell
$ ./database drop production
Are you sure? [y/N]: y
Database 'production' was deleted
```
The following two examples are identical:
```shell
$ ./database drop -f production
Database 'production' was deleted
```
```shell
$ ./database drop --force production
Database 'production' was deleted
```

### Class Options

Options could be declared on handler itself with `Handler#declare_option` method. 

Options declared on handler will be declared on each of its command and subcommand recursively. 
```python
#!/usr/bin/env python3
import sys, comandante as cli

class CliTool(cli.Handler):
    def __init__(self):
        super().__init__()
        
        # define options
        self.declare_option('verbose', 'v', bool, False)
    
    @cli.command()
    def first(self, **specified_options):
        if 'verbose' in specified_options:
            print("Hello from the first!")
    
    @cli.command()
    def second(self, **specified_options):
        if 'verbose' in specified_options:
            print("Hello from the second!")
        

tool = CliTool()
tool.invoke(sys.argv[1:])
```
Then in shell:
```shell
$ ./tool first --verbose
Hello from the first!
```
```shell
$ ./tool second -v
Hello from the second!
```

## Subcommands

As your CLI becomes more complex and harder to maintain, you might want to 
have commands that have its own set of commands handled by separate class. 
In Comandante to compose handlers into hierarchy you may simply 
use `Handler#declare_command` method. 

Here is a simple example:
```python
#!/usr/bin/env python3

import sys, comandante as cli

class Remote(cli.Handler):
    @cli.command()
    def add(self, name, uri):
        print("Adding repository", name, uri)
    
    @cli.command()
    def rename(self, old, new):
        print("Renaming repository", old, new) 
        
class Git(cli.Handler):
    def __init__(self):
        super().__init__() 
        
        # define subcommands
        self.declare_command(name='remote', handler=Remote())
    
    @cli.option('message', 'm', str, '')
    @cli.command()
    def commit(self, **specified_options):
        options = self.commit.options(specified_options)
        print("Committing changes with message '{}'".format(options.message))
        
git = Git()
git.invoke(sys.argv[1:])
```

Then in shell
```shell
$ ./git commit -m "Initial commit"
Committing changes with message 'Initial commit' 
```
```shell
$ ./git remote add origin git@github.com:stepan-anokhin/comandante.git
Adding repository origin git@github.com:stepan-anokhin/comandante.git
```
```shell
$ ./git remote rename origin destination
Renaming repository origin destination
```
## Arguments

In python3 command argument types are declared using annotations:
```python
import comandante as cli

class CliTool(cli.Handler):

    @cli.command()
    def do_something(self, a: int, b: float, c: str):
        print(a + b, c)
```
Type could be any callable. This callable will be simply called with 
a command-line string as the only argument. A result will be passed
to the *command-method* as argument. The same is true for option types. 
 
The only exception is `bool` arguments and options. Bool option doesn't 
receive any value, if specified it is considered to be `True` otherwise 
default value is used. 

If no argument type is specified, then `str` is assumed by default. 
Type's `__name__` attribute is used in automatic help output to 
represent argument/option type. 

Comandante honors default argument values and varargs:
```python
#!/usr/bin/env python3
import sys, comandante as cli

class CliTool(cli.Handler):

    @cli.command()
    def sum(self, *values: int):
        print(sum(values))
        
    @cli.command()
    def repeat(self, message, times: int = 2):
        for i in range(times):
            print(message)

CliTool().invoke(sys.argv[1:])
```
```shell
$ ./tool sum 1 2 3 4 5
15
```
```shell
$ ./tool repeat "Hello world!"
Hello world!
Hello world!
```
### Type Library

Comandante also provides several higher-order types:
 * `comandante.types.choice` - to make sure argument value is one of the specified options
 * `comandante.types.listof` - to parse comma-separated lists (e.g. `listof(int)` will parse `"1,2,3,4"` into `[1, 2, 3, 4]`)
 
You may take a look into the
[comandante.types](https://github.com/stepan-anokhin/comandante/blob/master/comandante/types.py)
to get some additional insights.  
 
### Python 2

Python 2 doesn't support parameter annotations. 
To specify argument types use `@comandante.signature()`
```python
import comandante as cli

class CliTool(cli.Handler):

    @cli.signature(a=int, b=float)
    @cli.command()
    def do_something(self, a, b, c):
        print(a + b, c)
```

## Printing Help

Comandante provides predefined `help` command for you which will print
formatted help information to the stdout. Command and handler descriptions
are taken from the corresponding docstrings. 

Example:
```python
import sys
import comandante as cli


class Git(cli.Handler):
    """The stupid content tracker.

    Git is a fast, scalable, distributed revision control system with
    an unusually *rich command* set that provides both high-level operations
    and full access to internals.

    See *gittutorial*(7) to get started, then see *giteveryday*(7) for a useful
    minimum set of commands. The *Git User’s Manual*[1] has a more in-depth
    introduction.
    """

    @cli.option(name='message', short='m', type=str, default='', descr="""
    Use the given <msg> as the commit message. If multiple *-m* options are 
    given, their values are concatenated as separate paragraphs.
    """)
    @cli.command()
    def commit(self):
        """Record changes to the repository

        Create a new commit containing the current contents
        of the index and the given log message describing
        the changes. The new commit is a direct child of HEAD,
        usually the tip of the current branch, and the branch
        is updated to point to it (unless no branch is associated
        with the working tree, in which case HEAD is "detached"
        as described in *git-checkout*(1)).
        """
        print("Committing...")

    @cli.command()
    def clone(self, repository, directory=None):
        """Clone a repository into a new directory

        Clones a repository into a newly created directory, creates
        remote-tracking branches for each branch in the cloned
        repository (visible using git branch *-r*), and creates and
        checks out an initial branch that is forked from the cloned
        repository’s currently active branch.
        """
        print("Cloning...")
        
Git().invoke(sys.argv[1:])
``` 
`./git` output:
<p align="left">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/docs/images/help_git.png" alt="git">
</p>

`./git help clone` output:
<p align="left">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/docs/images/help_clone.png" alt="git help clone">
</p>

`./git help commit` output:
<p align="left">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/docs/images/help_commit.png" alt="git help commit">
</p>


## Error Handling

Successful calls to `Handler#invoke` and `Command#invoke` methods return 
the same value as the corresponding *command-method*. 

By design Comandante doesn't hide any exceptions raised in the course of 
`invoke` call. The only special case is subclasses of 
`comandnate.errors.CliSyntaxException` which results in help printing 
before being re-raised.

So it is up to the caller to decide how to handle exceptions. 

A reasonable error handling may look like this:
```python
import sys, logging, comandante as cli

# ... initialize handler and logger ... 

try: 
    handler.invoke(sys.argv[1:])
except cli.errors.CliSyntaxException:
    sys.exit(1)
except:
    logger.exception('Unexpected exception')
    sys.exit(1)
    
```  

## Testing Your CLI

Handlers and commands could be tested just like 
[any other](#just-a-normal-classes-and-methods) classes and methods. 

Example cli:
```python
import comandante as cli


class DatabaseCli(cli.Handler):
    def __init__(self, database):
        super().__init__()
        self._database = database

    @cli.option('force', 'f', bool, False)
    @cli.command()
    def drop(self, database_name, **specified_options):
        options = self.drop.options(specified_options)
        if options.force or self.confirm():
            self._database.drop(database_name)

    def confirm(self):
        question = 'Are you sure? [y/N]: '
        value = input(question).lower()
        while value not in ['', 'n', 'y']:
            print("Please answer 'y' or 'n'")
            value = input(question)
        return value == 'y'

``` 
Example tests:
```python
from unittest import TestCase
from unittest.mock import MagicMock as Mock


class DatabaseCliTests(TestCase):
    def test_forced_database_drop(self):
        fake_database = Mock()
        database_cli = DatabaseCli(database=fake_database)

        database_cli.drop('production', force=True)

        fake_database.drop.assert_called_with('production')

    def test_database_drop(self):
        fake_database = Mock()
        database_cli = DatabaseCli(database=fake_database)
        database_cli.confirm = Mock(return_value=True)  # confirm

        database_cli.drop('production')

        fake_database.drop.assert_called_with('production')

    def test_rejected_database_drop(self):
        fake_database = Mock()
        database_cli = DatabaseCli(database=fake_database)
        database_cli.confirm = Mock(return_value=False)  # reject

        database_cli.drop('production')

        fake_database.drop.assert_not_called()
```
