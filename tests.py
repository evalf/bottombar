import bottombar as bb, os, time
import signal

def input(msg):
    print(msg, end='', flush=True)
    while True:
        try:
            signal.pause()
        except KeyboardInterrupt:
            break
    print()

print('\033[{};1H'.format(os.get_terminal_size().lines))
print('====================')
print('BOTTOMBAR UNIT TESTS')
print('--------------------')
print('PRESS CTRL+C TO PROCEED TO THE NEXT TEST')

print('1. basic terminal tests')
input('   a. check that this question shows at the very last line')
input('   b. check that the the last word shows in \033[0;33myellow\033[0m')
input('   c. check that this box [ ] contains the blinking cursor\033[31D')

print('2. basic bottombar tests')
with bb.add('foo...') as item:
    input('   a. check that the bottom line shows the text "foo..."')
    item.text = 'bar!'
    input('   b. check that the bottom line shows "bar!" (and nothing more)')
    input('   c. check that this {}long sentence wraps without overwriting "bar!"'.format('very ' * 40))
input('   d. check that the bar is removed and the last line is open')
input('   e. check that this text appears on the last line')

print('3. formatting tests')
with bb.add('x', label='item1') as item1:
    input('   a. check that the bottom line shows "item1: x"')
    with bb.add('y', label='item2') as item2, bb.add('z', label='item3') as item3:
        input('   b. check that the bottom line shows "item1: x | item2: y | item3: z"')
        item2.text = 'y' * 999
        input('   c. check that the bottom line shows "x | yyyyyyyyyyyyyyyyyyyyyyy.. | z" filling out the terminal')
        item3.text = 'z' * 999
        input('   c. check that the bottom line shows "x | yyyyyyyyyyy.. | zzzzzzzzzzz.."')
        with bb.add('right', right=True):
            input('   d. check that the bottom line shows "x | yyyyyyy.. | zzzzzzz..   right"')

print('4. terminal control tests')
with bb.add('white bar') as item:
    input('   a. check that the bottom line shows "white bar"')
    print('   b. check that \033[0;33m[this entire ', end='', flush=True)
    bb.redraw()
    input('box]\033[0m is yellow but the bar is white')
    print('   c. check that \033[0;33m[this entire ', end='', flush=True)
    item.text = '\033[0;34mblue bar'
    input('box]\033[0m is yellow but the bar is blue')
    print('   d. check that \033[0;33m[this entire ', end='', flush=True)
input('box]\033[0m is yellow and the bar disappeared')

print('5. resize tests')
with bb.add('left'), bb.add('right', right=True):
    input('   a. check that the bottom line shows "left (..) right" over the entire length')
    input('   b. change the window width; check that "left" and "right" move along')
    input('   c. change the window height; check that the bar remains at the bottom')
    input('   e. check that the blinking cursor stays in this box [ ] upon resize\033[14D')

print('6. refresh tests')
class timer:
    def __init__(self) -> None:
        self.t0 = time.perf_counter()
    def __str__(self) -> str:
        return '{:.5f}'.format(time.perf_counter() - self.t0)
with bb.add(timer(), refresh=.5):
    input('   a. check that the time in the bar updates approximately twice every second')
    with bb.add(timer(), refresh=2):
        input('   b. check that the time in the bar still updates approximately twice every second')
with bb.add(timer(), refresh=2):
    input('   c. check that the time in the bar updates approximately every two seconds')
    with bb.add(timer(), refresh=.5):
        input('   d. check that the time in the bar updates approximately twice every second')
    input('   e. check that the time in the bar updates approximately every two seconds')

print('--------------------')
