"""Provides a simple command-line interface for your Python programs.

Apropos reinventing the wheel, Python already has the "cmd" library.
But that requires subclassing.  A good way would be to replace this library
with one that wraps "cmd", so that

    CLI(commands={"add": add})

produces an instance of the class

    class __foo(cmd):
      def do_add(*args, **kw):
        return ddd(*args, **kw)

Written by Christian Stigen Larsen
2014-05-01

Placed in the public domain by the author.
"""

import pydoc
import re
import sys

class StopCLI(Exception):
  """Exception used to stop the CLI loop."""
  def __init__(self, print_newline = False):
    Exception.__init__(self)
    self.newline = print_newline

# Some default commands
def quit():
  """Exits the command loop."""
  raise StopCLI()

class CLI(object):
  """Class that supports a command line interface (CLI).

  To exit the command loop from one of your own commands, raise a StopCLI.

  Example:
    >>> def add(a,b):
    ...   '''Adds a and b.'''
    ...   return int(a) + int(b)
    ...
    >>> CLI(prompt="foo> ", commands={"add": add}).start()

    foo> help add
    add - Adds a and b.
    foo> add 1 2
    3
    foo> help
    Known commands:

    ? - Prints help.
    add - Adds a and b.
    help - Prints help.
    quit - Exits the command line interface.

    Type "help command" to get help on "command."
    foo> quit
  """
  def __init__(self,
               prompt = "> ",
               commands = {},
               infile = sys.stdin,
               outfile = sys.stdout,
               add_default_commands = True,
               print_command_result = True):
    """Initializes CLI."""

    self.prompt = prompt
    self.commands = commands
    self.infile = infile
    self.outfile = outfile
    self.print_result = print_command_result

    if add_default_commands:
      self._add_if_new("help", self._help)
      self._add_if_new("quit", quit)

  def _add_if_new(self, name, function):
    """Adds command if it doesn't already exist."""
    if name not in self.commands:
      self.commands[name] = function

  def _print(self, *args):
    """Print joined string arguments to output file."""
    self.outfile.write("".join(args) + "\n")
    self.outfile.flush()

  def _quit(self):
    """Exits the command line interface."""
    raise StopCLI(print_newline=False)

  def _help(self, *args):
    """Prints help."""
    if len(args) == 0:
      self._print("Known commands:")
      self._print()

      for command, func in sorted(self.commands.items()):
        doc = ""
        if hasattr(func, "__doc__"):
          doc = " - " + func.__doc__.split("\n")[0]
        self._print("{}{}".format(command, doc))

      self._print()
      self._print('Type "help command" to get help on "command."')
    else:
      cmd = args[0]
      func = self.commands[cmd]
      self._print(pydoc.render_doc(func, title="%s"))

  def _unknown(self, *args):
    """Default handler for unknown commands."""
    self._print("Unknown command '{}'".format(args[0]))
    self._print("Try: help")

  def start(self):
    """Starts the REPL."""
    try:
      while True:
        # Read command
        parts = self._readcommand()

        # Skip empty lines
        if len(parts) == 0:
          continue

        # Run command
        result = self._dispatch(parts[0], *parts[1:])

        # Optionally print result
        if self.print_result:
          if result is not None and len(str(result)) > 0:
            self._print(str(result))

    except StopCLI, e:
      if e.newline:
        self._print()
      return

  def _dispatch(self, command, *args):
    """Dispatch a command with given arguments."""
    # Skip empty lines
    if len(command) == 0:
      return

    # Dispatch
    if command not in self.commands:
      self._print("Unknown command '{}'".format(command))
      if "help" in self.commands:
        self._print("Try: help")
      return

    try:
      return self.commands[command](*args)
    except StopCLI:
      raise
    except Exception, e:
      # If the arguments don't match the function
      self._print("Error in {}: {}".format(command, e))

  def _readcommand(self):
    """Prompt and read one command."""
    self.outfile.write(self.prompt)
    self.outfile.flush() # required
    line = self.infile.readline()

    # Stop on CTRL+D (no trailing newline)
    if len(line) == 0:
      raise StopCLI(print_newline=True)

    # Sanitize spaces and return parts
    return re.sub("[ \t]+", " ", line.strip()).split(" ")

if __name__ == "__main__":
  # Start the example
  def add(a,b):
    """Adds a and b."""
    return int(a) + int(b)
  CLI(prompt="foo> ", commands={"add": add}).start()
