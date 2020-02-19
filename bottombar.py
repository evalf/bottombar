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

import sys, os, struct, fcntl, termios, signal


def default_formatter(*args, ncols):
  bar = ' '.join(map(str, args))
  if len(bar) > ncols:
    bar = bar[:ncols-3] + '/..'
  return bar


class BottomBar:

  def __init__(self, *args, output=sys.stdout, format=default_formatter):
    self.args = args
    self.encoding = output.encoding
    self.fileno = output.fileno()
    self.format = format

  def __bytes__(self):
    return self.format(*self.args, ncols=self.ncols)[:self.ncols].encode(self.encoding)

  def resize(self, *dummy):
    s = struct.pack('HHHH', 0, 0, 0, 0)
    t = fcntl.ioctl(self.fileno, termios.TIOCGWINSZ, s)
    self.nrows, self.ncols, ws_xpixel, ws_ypixel = struct.unpack('HHHH', t)
    os.write(self.fileno,
      b'\033E' # scroll to make sure there is at least one open line below cursor
      b'\033[A' # return cursor to former position
      b'\033[J' # erase to end of screen
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'%s' # print bar
      b'\033[1;%dr' # set scroll region
      b'\0338' # restore cursor position
      % (self.nrows, self, self.nrows-1))

  def __enter__(self):
    if hasattr(self, '_oldhandler'):
      raise RuntimeError('This context manager is not reentrant.')
    self._oldhandler = signal.signal(signal.SIGWINCH, self.resize)
    self.resize()
    return self

  def __call__(self, *args):
    self.args = args
    os.write(self.fileno,
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'%s' # print bar
      b'\033[K' # clear line from cursor to end
      b'\0338' # restore cursor position
      % (self.nrows, self))

  def __exit__(self, *exc):
    if not hasattr(self, '_oldhandler'):
      raise RuntimeError('This context manager is not yet entered.')
    os.write(self.fileno,
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'\033[K' # clear entire line
      b'\033[r' # reset scroll region
      b'\0338' # restore cursor position
      % self.nrows)
    signal.signal(signal.SIGWINCH, self._oldhandler)
    del self._oldhandler


# vim:sw=2:sts=2:et
