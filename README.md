<p align="center">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/logo.png" width="500" alt="Comandante Logo">
</p>

Comandante is a toolkit for building command-line interfaces in Python.

### NOTE: Currently the documentation is outdated. It will be updated very soon. Some of the API changes haven't been reflected yet.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Options](#options)
- [Subcommands](#subcommands)

## Installation

**NOTE**: currently PyPI contains an empty implementation to occupy the name. This will be changed very soon (in a week or so). 

To get the latest release simply install it with a `pip`:

```shell
pip3 install --upgrade comandante
```

## Getting Started

In comandante command-line interface is represented 
by the `comandante.Handler` class and its descendants.

Each `Handler`'s method decorated with `@comandante.command()`
will become a CLI command. 

```python
#!/usr/bin/env python3
# content of 'app'

import sys, comandante as cli

class CliApplication(cli.Handler):

    @cli.command()
    def hello(self, name):
        print("Hello wonderful {name}!".format(name=name))
        
    @cli.command()
    def bye(self, name):
        print("Goodbye wonderful {name}!".format(name=name))
        
app = CliApplication()
app.invoke(*sys.argv)
```
Then in shell:
```shell
$ ./app hello world
Hello wonderful world!

$ ./app bye world
 Goodbye wonderful world!

```

Descendants of `Handler` are ordinary classes so that they have all
the abilities of normal python classes:

```python
import sys, comandante as cli

class App(cli.Handler):
    def __init__(self, database):
        super().__init__()
        self._database = database
    
    @cli.command()
    def drop(self, database_name):
        self.helper_method()
        self._database.drop(name=database_name)
            
    
    def helper_method(self):
        # do something extremely useful
        pass

app = App(Database(database_uri))
app.invoke(*sys.argv)
```


## Options
Command options

```python
#!/usr/bin/env python3
# file name is 'database'

import sys, comandante as cli

 
class DatabaseCli(cli.Handler):
    def __init__(self, database):
        super().__init__()
        self._database = database
    
    @cli.option(name='force', short='f', type=bool, default=False)
    @cli.command()
    def drop(self, database_name):
        if self.options.force or self.ask():
            self._database.drop(name=database_name)
            print("Database was deleted")
        else: 
            print("Aborted")
    
    def ask(self):
        question = 'Are you sure? [y/N]: '
        value = input(question)
        while value not in ['', 'n', 'y']:
            print("Please answer 'y' or 'n'")
            value = input(question)
        return value == 'y'
        


app = DatabaseCli(Database(database_uri))
app.invoke(*sys.argv)
```
Then in shell:
```shell
$ ./database drop production
Are you sure? [y/N']: y
Database was deleted

$ ./database drop -f production
Database was deleted

$ ./database drop --force production
Database was deleted
```

Global options
```python
import sys, comandante as cli

class App(cli.Handler):
    def __init__(self):
        super().__init__()
        
        # define options
        self.option(name='verbose', short='v', type=bool, default=False)
    
    @cli.command()
    def say(self, what):
        if self.options.verbose:
            print("> Before saying")
        print(what)
        if self.options.verbose:
            print("> After saying")

app = App()
app.invoke(*sys.argv)
```
Then in shell:
```shell
$ ./app say -v "hello world"
> Before saying
hello world
> After saying
```

## Subcommands

```python
#!/usr/bin/env python3
# file name is 'git'

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
        super().__init__() # this is required
        
        # define subcommands
        self.subcommand(name='remote', handler=Remote())
    
    @cli.command()
    def commit(self):
        print("Committing...")
        
git = Git()
git.invoke(*sys.argv)
```

Then in shell
```shell
$ ./git remote add origin git@github.com:stepan-anokhin/comandante.git
Adding repository origin git@github.com:stepan-anokhin/comandante.git
```
