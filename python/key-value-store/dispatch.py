def do_nothing(*args, **kw):
  """A function that takes any arguments and does nothing."""
  pass

class Dispatcher(object):
  """A dispatcher class that forwards function calls based on a key."""
  def __init__(self, functions, default=do_nothing):
    """
    Args:
      functions: Key -> function map
      default: Function to call if key not found
    """
    self.funcs = functions
    self.default = default

  def lookup(self, key):
    """Look up function based on key, or default function if not found."""
    if key in self.funcs:
      return self.funcs[key]
    return self.default

  def dispatch(self, key, *args, **kwargs):
    """Lookup function and call it with given arguments."""
    func = self.lookup(key)
    return func(*args, **kwargs)
