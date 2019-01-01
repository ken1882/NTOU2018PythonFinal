import builtins
import collections

class Util:
  def __init__(self):
    raise Exception('This is a static class')
  
  @classmethod
  def flatten(self, ar, parent = []):
    for el in ar:
      if el is ar or el in parent:
        pass
      elif isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
        parent.append(ar)
        yield from self.flatten(el, parent)
      else:
        yield el