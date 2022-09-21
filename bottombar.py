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

__version__ = '2.0.2'


import sys, os, atexit, signal
from contextlib import ExitStack, ContextDecorator
from dataclasses import dataclass
from typing import Any, Optional, List, Callable, Type, Union
from types import TracebackType, FrameType


if os.getenv('BOTTOMBAR_DEBUG'):

    def _debug(s: str) -> None:
        print('[bottombar]', s, file=sys.stderr)

else:

    def _debug(s: str) -> None:
        pass


_debug('initializing ...')


@dataclass
class _BarItem:
    '''Text, label combination to populate _BottomBar.

    Dataclass consisting of the mutable fields text and label.'''

    text: Any
    label: Optional[str]


class _BottomBar:
    '''Container for bar items.

    The _BottomBar class maintains and formats the bar's content. Items can be
    added to the right or left, stacking from the outside inward. Truthiness
    signals if the bar presently contains any items.'''

    def __init__(self) -> None:
        self.__nleft = 0
        self.__items: List[_BarItem] = []

    def __bool__(self) -> bool:
        return bool(self.__items)

    def add(self, text: Any, *, right: bool, label: Optional[str]) -> _BarItem:
        '''Create a bar item and add it to the bar.

        The new item is added to the left or right stack depending on the
        `right` argument. The new _BarItem instance is returned for in place
        modification and removal.'''

        c = _BarItem(text, label)
        self.__items.insert(self.__nleft, c)
        if not right:
            self.__nleft += 1
        return c

    def remove(self, item: _BarItem) -> None:
        '''Remove a bar item.'''

        index = self.__items.index(item)
        del self.__items[index]
        if index < self.__nleft:
            self.__nleft -= 1

    def format(self, length: int) -> str:
        '''Generate bar string of given length.

        Depending on the total size of the bar items and the target bar length,
        the formatted string will show labeled items as | label: text | if
        there is sufficient space, or simply | text | if there is there is
        sufficient space for all text, or | t.. | if (some) items require
        shortening. The returned string always matches the requested length.'''

        itemsep = ' | '
        labelsep = ': '
        nitems = len(self.__items)
        maxchars = length - len(itemsep) * (nitems - 1)
        if maxchars <= 2 * nitems:
            return '#' * length
        texts = [str(item.text) for item in self.__items]
        whitespace = maxchars - sum(map(len, texts))
        if whitespace < 0:
            # not all items fit; shorten the longest ones
            for i in sorted(range(nitems), key=lambda i: len(texts[i])): # argsort
                maxlen = maxchars // nitems # >= 2 since maxchars > 2 * nitems
                if len(texts[i]) >= maxlen:
                    texts[i] = texts[i][:maxlen-2] + '..'
                maxchars -= len(texts[i])
                nitems -= 1
        elif whitespace >= sum(len(item.label) + len(labelsep) for item in self.__items if item.label):
            # labels fit; prepend to texts
            texts = [labelsep.join((item.label, text)) if item.label else text for item, text in zip(self.__items, texts)]
        left = itemsep.join(texts[:self.__nleft])
        right = itemsep.join(texts[self.__nleft:])
        return left.ljust(length - len(right)) + right


class _Terminal:
    '''Terminal state and manipulation.

    The _Terminal class is in charge of printing data on screen. It keeps track
    of whether a status bar is currently drawn and if the screen size changed
    since last update, and provides methods for setting and resetting the
    scroll region and printing a status line using VT100 control sequences.'''

    def __init__(self) -> None:
        self.__size: Optional[os.terminal_size] = None # a None value signifies that the scroll region is not set
        self.__stdout = open(sys.stdout.fileno(), mode='wb', buffering=0, closefd=False)

        # make sure we can query the terminal size
        size = os.get_terminal_size()
        _debug(f'terminal size: {size.columns}x{size.lines}')

    def prepare_bar(self) -> int:
        '''Create open line and set scroll region.

        If the scroll region is not currently set, scroll by one line if the
        cursor is at the bottom of the terminal to make place for a status bar,
        and set the scroll region to exclude the bottom line. The width of the
        terminal is returned for formatting purposes.'''

        size = os.get_terminal_size()
        if size != self.__size:
            scroll = size.lines - 1
            _debug(f'setting scroll region to {scroll} lines')
            self.__stdout.write(
                b'\0337' # save cursor and attributes
                b'\033[r' # reset scroll region (moves cursor)
                b'\0338' # restore cursor and attributes
                b'\033D' # move/scroll down
                b'\033M' # move up
                b'\0337' # save cursor and attributes
                b'\033[1;%dr' # set scroll region
                b'\0338' # restore cursor and attributes
                % scroll)
            self.__size = size
        return size.columns

    def print_bar(self, bar: str) -> None:
        '''Print string at the bottom line of the terminal.

        This method assumes that prepare_bar was already called.'''

        assert self.__size, 'print_bar requires prepare_bar'

        self.__stdout.write(
            b'\0337' # save cursor and attributes
            b'\033[%d;1H' # move cursor to bottom row, first column
            b'\033[?7l' # disable line wrap
            b'\033[0m' # clear attributes
            b'%s' # print bar
            b'\033[?7h' # enable line wrap
            b'\0338' # restore cursor and attributes
            % (self.__size.lines, bar.encode()))

    def remove_bar(self) -> None:
        '''Clear bottom line and reset scroll region.

        If the scroll region is currently set, clear the bottom line and reset
        the scroll region to include the entire terminal.'''

        if self.__size is not None:
            _debug('restoring scroll region')
            self.__stdout.write(
                b'\0337' # save cursor position
                b'\033[%d;1H' # move cursor to bottom row, first column
                b'\033[K' # clear entire line
                b'\033[r' # reset scroll region
                b'\0338' # restore cursor position
                % self.__size.lines)
            self.__size = None


class Auto:
    '''Register handler function for resize and time events.

    The implementation of this class is platform and situation dependent. On
    Unix systems, it relies on the operating system's signal mechanism to watch
    for SIGWINCH and SIGALRM events, if no handlers for these signals are
    active at the time of activation.

    On other platforms, or if signal handlers are already in place, the class
    creates a thread upon first registration, from which the handler is called
    at a given refresh rate, and the screen size is polled every second.'''

    __active: Optional[Union['__thread_based', '__signal_based']]

    def __init__(self, handler: Callable[[], None]) -> None:
        self.__handler = handler
        self.__active = None
        self.__refresh = float('inf')

    def __call__(self, refresh: float) -> ExitStack:
        restore = ExitStack()
        if not self.__active:
            self.__activate()
            restore.callback(self.__deactivate)
        if refresh < self.__refresh:
            restore.callback(self.__set_refresh, self.__refresh)
            self.__set_refresh(refresh)
        return restore

    def __activate(self) -> None:
        assert not self.__active, 'handler is already active'
        try:
            if os.getenv('BOTTOMBAR_THREAD_BASED', False):
                raise RuntimeError('variable BOTTOMBAR_THREAD_BASED is set')
            self.__active = self.__signal_based(self.__handler)
        except Exception as e:
            _debug(f'not selecting signal based auto-redraw handler: {e}')
            self.__active = self.__thread_based(self.__handler)

    def __deactivate(self) -> None:
        assert self.__active, 'handler is not yet active'
        self.__active.close()
        self.__active = None

    def __set_refresh(self, refresh: float) -> None:
        assert self.__active, 'handler is not yet active'
        _debug(f'set refresh interval to {refresh}')
        self.__active.set(refresh)
        self.__refresh = refresh

    class __signal_based:
        def __init__(self, handler: Callable[[], None]) -> None:
            for sig in signal.SIGALRM, signal.SIGWINCH:
                if signal.getsignal(sig) != signal.SIG_DFL:
                    raise RuntimeError(f'signal {sig.name} is in use')
                signal.signal(sig, lambda sig, frame: handler())
                signal.siginterrupt(sig, False) # restart any interrupted system calls
            signal.setitimer(signal.ITIMER_REAL, 0.)
            _debug('started signal based auto-redraw handler')
        def set(self, refresh: float) -> None:
            if refresh < float('inf'):
                signal.setitimer(signal.ITIMER_REAL, refresh, refresh)
            else:
                signal.setitimer(signal.ITIMER_REAL, 0.)
        def close(self) -> None:
            for sig in signal.SIGALRM, signal.SIGWINCH:
                signal.signal(sig, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_REAL, 0.)
            _debug('stopped signal based auto-redraw handler')

    class __thread_based:
        def __init__(self, handler: Callable[[], None]) -> None:
            import _thread
            self.lock = _thread.allocate_lock()
            self.lock.acquire()
            self.refresh = float('inf')
            _thread.start_new_thread(self.__run, (handler,))
        def set(self, refresh: float) -> None:
            self.refresh = refresh
            if self.lock.locked():
                self.lock.release()
        def close(self) -> None:
            self.set(0.)
        def __run(self, handler: Callable[[], None]) -> None:
            _debug('started thread based auto-redraw handler')
            timeout = self.refresh
            poll_rate = 1.
            size = os.get_terminal_size()
            while timeout:
                if not self.lock.acquire(timeout=min(timeout, poll_rate)):
                    # timed out
                    if poll_rate < timeout:
                        old_size = size
                        size = os.get_terminal_size()
                        if size == old_size:
                            timeout -= poll_rate
                            continue
                        # size changed
                    handler()
                timeout = self.refresh
            _debug('stopped thread based auto-redraw handler')


_bbar = _BottomBar()


# Public API

redraw: Callable[[], None]
auto_redraw: Callable[[float], ExitStack]

try:

    _term = _Terminal()

except:

    _debug('DISABLED: no capable terminal detected')

    def redraw() -> None:
        pass

    def auto_redraw(refresh: float = float('inf')) -> ExitStack:
        return ExitStack()

else:

    def redraw() -> None:
        '''Redraw the bottom bar.'''

        if _bbar:
            _term.print_bar(_bbar.format(_term.prepare_bar()))
        else:
            _term.remove_bar()

    auto_redraw = Auto(redraw)

    atexit.register(_term.remove_bar)


class add(ContextDecorator):
    '''Add bar item and register event handler.

    This context adds a bar item upon entering, redraws the bar, and registers
    the redraw method to handle resize events. Upon exit, the item is removed,
    the bar is redrawn, and the original event handler is restored.'''

    def __init__(self, text: Any, *, right: bool = False, label: Optional[str] = None, refresh: float = float('inf')) -> None:
        self.__item = _bbar.add(text, right=right, label=label)
        self.__redraw_handle = auto_redraw(refresh)
        redraw()

    @property
    def text(self) -> Any:
        return self.__item.text

    @text.setter
    def text(self, value: Any) -> None:
        self.__item.text = value
        redraw()

    @property
    def label(self) -> Optional[str]:
        return self.__item.label

    @label.setter
    def label(self, value: Optional[str]) -> None:
        self.__item.label = value
        redraw()

    def __enter__(self) -> 'add':
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        self.pop()

    def pop(self) -> None:
        _bbar.remove(self.__item)
        self.__redraw_handle.close()
        redraw()


_debug('initialization complete.')
