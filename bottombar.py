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

import sys, os, signal


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
    self.size = None

  def __bytes__(self):
    return self.format(*self.args, ncols=self.size.columns)[:self.size.columns].encode(self.encoding)

  def resize(self, *dummy):
    self.size = os.get_terminal_size(self.fileno)
    os.write(self.fileno,
      b'\033E' # scroll to make sure there is at least one open line below cursor
      b'\033[A' # return cursor to former position
      b'\033[J' # erase to end of screen
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'%s' # print bar
      b'\033[1;%dr' # set scroll region
      b'\0338' # restore cursor position
      % (self.size.lines, self, self.size.lines-1))

  def __enter__(self):
    if self.size is not None:
      raise RuntimeError('BottomBar is not reentrant')
    self.resize()
    self._oldhandler = signal.signal(signal.SIGWINCH, self.resize)
    return self

  def __call__(self, *args):
    self.args = args
    os.write(self.fileno,
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'%s' # print bar
      b'\033[K' # clear line from cursor to end
      b'\0338' # restore cursor position
      % (self.size.lines, self))

  def __exit__(self, *exc):
    if self.size is None:
      raise RuntimeError('BottomBar has not yet been entered')
    signal.signal(signal.SIGWINCH, self._oldhandler)
    os.write(self.fileno,
      b'\0337' # save cursor position
      b'\033[%d;1H' # move cursor to bottom row, first column
      b'\033[K' # clear entire line
      b'\033[r' # reset scroll region
      b'\0338' # restore cursor position
      % self.size.lines)
    self.size = None


# vim:sw=2:sts=2:et
