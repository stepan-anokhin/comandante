[![Build Status](https://travis-ci.org/stepan-anokhin/comandante.svg?branch=master)](https://travis-ci.org/stepan-anokhin/comandante)
[![Coverage Status](https://coveralls.io/repos/github/stepan-anokhin/comandante/badge.svg?branch=master)](https://coveralls.io/github/stepan-anokhin/comandante?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/stepan-anokhin/comandante/blob/master/LICENSE)

<p align="center">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/logo.png" width="500" alt="Comandante Logo">
</p>

Comandante is a toolkit for building command-line interfaces in Python.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Example](#Example)
  - [Just a Normal Classes and Methods!](#just-a-normal-classes-and-methods)
- [Options](#options)
  - [Command Options](#command-options)
  - [Class Options](#class-options)
- [Subcommands](#subcommands)
- [Argument Types](#argument-types)
- [Printing Help](#printing-help)
- [Error Handling](#error-handling)
- [Testing Your CLI](#testing-your-cli)
- [Design Considerations](#design-considerations)
- [API Reference](#api-reference)
  - [Handler](#handler)
  - [Command](#command)
  - [Decorators](#decorators)
- [Contributing](#contributing)

## Installation

### **NOTE**: Currently PyPI contains an empty implementation to occupy the name. This will be changed very soon (in a week or so). 

To get the latest release simply install it with a `pip`:

```shell
pip3 install --upgrade comandante
```

### Python 2 Support

Python 2 support will be added very soon.

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
No surprises! In Comandante handlers and commands are just a normal 
classes and methods!
 
Handlers may have any methods, fields, subclasses, decorations, 
constructor arguments, etc.  
All methods decorated with `@comandante.command()` (let's call them 
*command-methods*) are *almost* ordinary Python methods (they are
methods wrapped into `comandante.Command` class). Command-methods
could be used just like a normal Python methods. 

So in the example above you may simply call `CliTool#sum`: 
```python
tool = CliTool()
result = tool.sum(1, 2)
assert result == 3
```

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
## Argument Types

## Printing Help

## Error Handling

## Testing Your CLI

## Design Considerations

## API Reference

### Handler

### Command

### Decorators

## Contributing