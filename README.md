BottomBar
=========

BottomBar is a context manager for Python that prints a status line at the
bottom of a terminal window. Deliberately narrow in scope, it strives to do
[one thing well][1].


How it works
------------

The status line is positioned, and kept in position, using [VT100 escape
sequences][2]. In a nutshell, upon entry a scroll region is set that excludes
the bottom line, causing regular output to scroll freely above it. At every bar
update the cursor is moved to the bottom left corner, the line is redrawn, and
the position and attributes are reset to their previous value. Upon exit the
status line is cleared and the scroll region is reset to span all lines.


Requirements
------------

The use of escape sequences implies that a VT100-capable terminal is required.
Most Linux terminals qualify, including xterm, rxvt, and gnome-terminal. On
Microsoft Windows the new [Windows Terminal][3] is recommended.

Other than this BottomBar has no dependencies beyond Python version 3.3.


How to use it
-------------

In its simplest form, the `BottomBar` can be created with a string argument,
which will then be printed at the bottom line of the terminal for the duration
of the context.

```python
import bottombar

with bottombar.BottomBar('bar text'):
  print('regular output')
  ...

# bar text                                                                    #
```

The text "bar text" will show for the duration that the context remains
entered. To change the bar text without having to create a new context,
`BottomBar` returns an update method upon entry.

```python
with bottombar.BottomBar('bar text') as bb:
  ...
  bb('new bar text')
  ...

# new bar text                                                                #
```

If a line is longer than the width of the window it will silently be truncated.
Resizing the window will automatically increase or reduce the truncation to
match the new width, without further intervention required from the user.


The format argument
-------------------

BottomBar has an optional keyword argument `format` which determines how the
bottom bar is drawn. In addition to any number of positional arguments, this
callable must also be able to receive the keyword argument `width` for the
present number of columns. In the following example this argument is used to
center the bar text.

```python
def center(text, width):
  return text.center(width)

with bottombar.BottomBar('bar text', format=center) as bb:
  ...

#                                   bar text                                  #
```

Like with truncation, upon window resize the bar is automatically redrawn to
keep the text centered. When the text is updated using the `bb` method, the new
argument is also drawn using the specified formatter.

A formatter can receive any number of positional arguments. It is initially
called with the (positional) constructor arguments, then during manual update
with the new arguments, and upon every window resize with the stored arguments
but a different width.

The default formatter, in fact, allows any number of arguments of any type,
which are then converted to strings and string-joined in similar fashion to
the built-in print function. Hence, the following is allowed:

```python
with bottombar.BottomBar('foo', 123, ['bar']):
  ...

# foo 123 ['bar']                                                             #
```


The interval argument
---------------------

The other optional argument is `interval` which, if specified, causes BottomBar
to automatically call its formatter at set intervals. This is useful for
formatters that (partly) generate their own content. For example, the following
adds a right-aligned clock to the bar text, updated every second:

```python
import time

def myformat(text, width):
  return text + time.ctime().rjust(width - len(text))

with bottombar.BottomBar('bar text', format=myformat, interval=1) as bb:
  ...
  bb('new bar text')
  ...

# new bar text                                       Fri Apr  3 16:52:13 2020 #
```

Similar to window redraws, the formatter is called with the most recently
stored set of arguments, starting with the constructor arguments.

The use of interval requires a thread to perform callbacks in the background.
For platforms that do not support resize signals (most notably Microsoft
Windows) this thread replaces the one that would otherwise poll the window size
at one second intervals. In that situation it is important not to set the
interval too large as this directly affects the window resize response time.

Finally, intervals can be negative values. Both `+n` and `-n` represent an
interval of `n` seconds, but where the former aims to make a callback at the
exact interval, accounting for time spent in the callback, the latter, negative
version simply sleeps for the duration, allowing it to drift. Which mode is
more appropriate depends on the nature of the formatter, though in most
situations either choice is fine.


Examples
--------

BottomBar is intentionally minimalistic and does not provide any off-the-shelf
mechanisms for specialized use cases. However, the following code snippets can
be used as a starting point for further implementation.


A simple progress bar and percentage indicator:

```python
def progressbar(fraction=0, *, width):
  nbar = width - 17
  bar = '>'.rjust(int(fraction*nbar), '-').ljust(nbar)
  return 'progress: [{}] {:3.0f}%'.format(bar, 100 * fraction)

with bottombar.BottomBar(format=progressbar) as setprogress:
  for i in range(99):
    setprogress(i/99)
    ...

# progress: [------------->                                            ]  25% #
```

A system load monitor, showing the currently used memory and time spent in user mode:

```python
import resource

def sysload(width):
  r = resource.getrusage(resource.RUSAGE_SELF)
  m, s = divmod(int(r.ru_utime), 60) # minutes, seconds
  h, m = divmod(m, 60) # hours, minutes
  M = r.ru_maxrss // 1024 # size in MB
  status = 'memory: {:,}M | runtime: {}:{:02d}:{:02d}'.format(M, h, m, s)
  return status.rjust(width)

with bottombar.BottomBar(format=sysload, interval=1):
  ...

#                                               memory: 5M | runtime: 0:12:10 #
```

A stack trace showing the current activity of the calling thread:

```python
import sys, threading

def fmtstack(threadid, sep=' > ', *, width):
  items = []
  frame = sys._current_frames()[threadid]
  while frame.f_back:
    items.append(frame.f_code.co_name)
    frame = frame.f_back
  bar = 'STACK: ' + sep.join(reversed(items))
  if len(bar) > width:
    n = bar.find(sep, 12 - width)
    bar = 'STACK: ({})'.format(bar[:n].count(sep)) + bar[n:]
  return bar

with bottombar.BottomBar(threading.get_ident(), format=fmtstack, interval=-.1):
  ...

# STACK: main > do_work > some_task                                           #
```


[1]: https://en.wikipedia.org/wiki/Unix_philosophy
[2]: https://vt100.net/docs/vt100-ug/
[3]: https://aka.ms/windowsterminal
