def do_nothing(*args, **kw):
  """A function that takes any arguments and does nothing."""
  pass

class Dispatcher(object):
  """A dispatcher class that forwards function calls based on a key."""
  def __init__(self, dispatch_table={}, default_dispatch=do_nothing):
    """
    Args:
      functions: Key -> function map
      default: Function to call if key not found
    """
    self.dispatch_table = dispatch_table
    self.default_dispatch = default_dispatch

  def lookup(self, key):
    """Look up function based on key, or default_dispatch function if not found."""
    if key in self.dispatch_table:
      return self.dispatch_table[key]
    return self.default_dispatch

  def dispatch(self, key, *args, **kwargs):
    """Lookup function and call it with given arguments."""
    func = self.lookup(key)
    return func(*args, **kwargs)
