<p align="left">
    <img src="https://raw.githubusercontent.com/stepan-anokhin/comandante/master/logo.png" width="200" alt="Comandante Logo">
</p>

Comandante is a toolkit for building command-line interfaces in Python.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Options](#options)
- [Subcommands](#subcommands)

## Installation
## Getting Started

```python
import comandante, sys

# create a new command-line application
app = comandante.Application()

@app.command.name('hello')
@app.command.argument.name(type=str, required=True)
@app.command.description(usage='[WHO]', brief='Say hello')
def hello(name):
    print('Hello {who}!'.format(who=name))

app.start(sys.argv)
```
## Options
Command options

```python
@app.command.name('hello')
@app.command.argument('name', type=str, required=True)
@app.command.option('scream', type=bool, required=False)
def hello(name, scream=False):
    message = 'Hello {name}'.format(name=name)
    if scream:
        message = message.upper()
    print(message)
```

Global options
```python
import comandante, sys

# create a new command-line application
app = comandante.Application()
app.option('verbose', type=bool)

# define commands

app.start(sys.argv)
```

## Subcommands

```python
import comandante, sys

git = comandante.Application()
remote = comandante.Application()

git.subcommand(name='remote', command=remote)

git.start(sys.argv)
```