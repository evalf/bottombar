# Copyright (c) 2020 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''Print and maintain a status line at the bottom of a VT100 terminal.'''

__version__ = '1.1'


import sys, os, signal, threading, time


class _ontime(threading.Thread):
  def __init__(self, interval, callback, *args):
    super().__init__()
    self.interval = interval
    self.callback = callback
    self.args = args
    self.stopped = threading.Event()
    self.start()
  def run(self):
    interval = abs(self.interval)
    precise = self.interval > 0
    while not self.stopped.wait(interval - (precise and time.perf_counter() % interval)):
      self.callback(*self.args)
  def close(self):
    self.stopped.set()
    self.join()


class _onevent:
  def __init__(self, signalnum, callback, *args):
    self.callback = callback
    self.args = args
    self.signalnum = signalnum
    self.oldhandler = signal.signal(signalnum, self.handler)
    signal.siginterrupt(signalnum, False) # restart any interrupted system calls
  def handler(self, sig, tb):
    self.callback(*self.args)
  def close(self):
    signal.signal(self.signalnum, self.oldhandler)


def _format(*args, width):
  return ' '.join(map(str, args))


class BottomBar:
  '''Bar drawing context.

  The BottomBar context is created with a single string argument, which is
  displayed for the duration that the context remains entered.

  >>> with BottomBar('bar text'):
  ...     print('regular output')

  To change the bar text without having to create a new context, the BottomBar
  context returns an update method upon entry.

  >>> with bottombar.BottomBar('bar text') as bb:
  ...     bb('new bar text')

  The optional keyword argument `format` determines how the bottom bar is drawn.
  In addition to any number of positional arguments, this callable must also be
  able to receive the keyword argument `width` for the present number of columns.
  In the following example this argument is used to center the bar text.

  >>> def center(text, width):
  ...     return text.center(width)
  >>> with bottombar.BottomBar('bar text', format=center) as bb:
  ...     print('regular output')

  The optional keyword argument `interval` causes BottomBar to automatically call
  its formatter at set intervals. This is useful for formatters that (partly)
  generate their own content. For example, the following adds a right-aligned
  clock to the bar text, updated every second:

  >>> import time
  >>> def myformat(text, width):
  ...     return text + time.ctime().rjust(width - len(text))
  >>> with bottombar.BottomBar('bar text', format=myformat, interval=1) as bb:
  ...     bb('new bar text')'''

  def __init__(self, *args, output=sys.stdout, format=_format, interval=None):
    self.args = args
    self.encoding = output.encoding
    self.fileno = output.fileno()
    self.format = format
    self.interval = interval
    self.size = None
    self.handles = []

  def __enter__(self):
    if self.size is not None:
      raise RuntimeError('BottomBar is not reentrant')
    self.redraw(True)
    if hasattr(signal, 'SIGWINCH'):
      self.handles.append(_onevent(signal.SIGWINCH, self.redraw, False))
    elif not self.interval:
      self.handles.append(_ontime(-1, self.redraw, False))
    if self.interval:
      self.handles.append(_ontime(self.interval, self.redraw, True))
    return self.update

  def write(self, data):
    while data:
      n = os.write(self.fileno, data)
      data = data[n:]

  def update(self, *args):
    self.args = args
    self.redraw(True)

  def redraw(self, force):
    size = os.get_terminal_size(self.fileno)
    if size != self.size:
      self.write(
        b'\0337' # save cursor and attributes
        b'\033[r' # reset scroll region (moves cursor)
        b'\0338' # restore cursor and attributes
        b'\033D' # move/scroll down
        b'\033M' # move up
        b'\0337' # save cursor and attributes
        b'\033[1;%dr' # set scroll region
        b'\0338' # restore cursor and attributes
        % (size.lines-1))
      self.size = size
      force = True
    if force:
      self.write(
        b'\0337' # save cursor and attributes
        b'\033[%d;1H' # move cursor to bottom row, first column
        b'\033[2K' # clear entire line
        b'\033[?7l' # disable line wrap
        b'\033[0m' # clear attributes
        b'%s' # print bar
        b'\033[?7h' # enable line wrap
        b'\0338' # restore cursor and attributes
        % (size.lines, self.format(*self.args, width=size.columns).encode(self.encoding)))

  def __exit__(self, *exc):
    if self.size is None:
      raise RuntimeError('BottomBar has not yet been entered')
    while self.handles:
      self.handles.pop().close()
    self.write(
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'\033[K' # clear entire line
      b'\033[r' # reset scroll region
      b'\0338' # restore cursor position
      % self.size.lines)
    self.size = None


# vim:sw=2:sts=2:et
