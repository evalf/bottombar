BottomBar
=========

Bottombar is a Python module that facilitates printing a status line at the
bottom of a terminal window. The module functions as a state machine, and
allows multiple, individually submitted status items to be displayed
simultaneously.


Requirements
------------

A VT100-capable terminal is required. Most Linux terminals qualify, including
Xterm, Rxvt, Gnome terminal, Kitty terminal, and Alacritty. On MS Windows the
new [Windows Terminal](https://aka.ms/windowsterminal) is recommended.

Other than this BottomBar has no dependencies beyond Python version 3.3.


How to use it
-------------

A bar entry is created using the module's `add` context, and displayed for the
duration that the context is entered. It also activates an event handler that
reformats and redraws the bar whenever the terminal window is resized.

```python
>>> import bottombar as bb
>>> 
>>> with bb.add('bottom bar', label='powered by'):
...     print('regular output')
# regular output                                                              #
# powered by: bottom bar                                                      #
```

Labels are optional, and multiple items can be stacked:

```python
...     with bb.add('more bar text'):
# regular output                                                              #
# powered by: bottom bar | more bar text                                      #
```

Items can be right-aligned:

```python
...         with bb.add('12:00', label='time', right=True):
# regular output                                                              #
# powered by: bottom bar | more bar text                          time: 12:00 #
```

If items no longer fit the bar then labels are dropped to make room:

```python
...             with bb.add('more right-aligned bar text', right=True):
# regular output                                                              #
# bottom bar | more bar text              more right-aligned bar text | 12:00 #
```

If this is not enough, long text entries are truncated:

```python
...                 with bb.add('this is getting too much'):
# regular output                                                              #
# bottom bar | more bar text | this is getting..   more right-align.. | 12:00 #
```


Redrawing content
-----------------

Manual redraws are required when a bar item is modified in place:

```python
>>> with bb.add('initial text') as item:
...     item.text = 'updated text'
# initial text                                                                #
...     bb.redraw()
# updated text                                                                #
```

For dynamic content it is more convenient to configure an auto-redraw rate:

```python
>>> import time
>>> class Clock:
...     def __str__(self):
...         return time.strftime('%H:%M:%S')
>>> with bb.add(Clock(), label='time', right=True), bb.auto_redraw(1):
#                                                              time: 12:00:00 #
#                                                              time: 12:00:01 #
#                                                              time: 12:00:02 #
```

In case multiple auto-redraws are configured simultaneously, the fastest rate
prevails.


Technical details
-----------------

The status line is positioned, and kept in position, using [VT100 escape
sequences](https://vt100.net/docs/vt100-ug/). By configuring a scroll region
that excludes the bottom line, regular output will scroll above it without
further intervention.

The implementaton of automatic redrawing depends on the platform. On Unix-like
systems both resize events and the redraw rate are handled using signals:
`SIGWINCH` and `SIGALRM`. Consequently, previously active handlers for these
signals are temporarily replaced for the duration that a bar is active. On
other platforms a thread is spawned that polls the terminal size once every
second, as well as redraws the bar at the configured interval.
