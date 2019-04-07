import time
import asyncio
import curses
import random

from curses_tools import draw_frame, read_controls
from game_tools import can_spaceship_move, get_spaceship_animation_size


TIC_TIMEOUT = 0.1
coroutines = []


async def blink(canvas, row, column, symbol='*', delay=0):
    while True:
        for times in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for times in range(int(2 / TIC_TIMEOUT) + 1):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for times in range(int(0.3 / TIC_TIMEOUT) + 1):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for times in range(int(0.5 / TIC_TIMEOUT) + 1):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for times in range(int(0.3 / TIC_TIMEOUT) + 1):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, start_row, start_column, spaceship_1, spaceship_2):
    while True:
        rows_direction, columns_directions, space_pressed = read_controls(canvas)
        animation_row_size, animation_column_size = get_spaceship_animation_size(spaceship_1, spaceship_2)

        if can_spaceship_move(canvas, start_row, start_column, rows_direction, columns_directions, animation_row_size,
                              animation_column_size):
            start_row += rows_direction
            start_column += columns_directions

        draw_frame(canvas, start_row, start_column, spaceship_1)
        canvas.refresh()
        draw_frame(canvas, start_row, start_column, spaceship_1, negative=True)

        await asyncio.sleep(0)

        draw_frame(canvas, start_row, start_column, spaceship_2)
        canvas.refresh()
        draw_frame(canvas, start_row, start_column, spaceship_2, negative=True)

        await asyncio.sleep(0)


def draw(canvas):
    
    max_rows, max_columns = canvas.getmaxyx()
    star_symbols = ['+', '*', '.', ':']
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)

    with open('animations/rocket_frame_1.txt', 'r') as spaceship_file_1:
        spaceship_1 = spaceship_file_1.read()

    with open('animations/rocket_frame_2.txt', 'r') as spaceship_file_2:
        spaceship_2 = spaceship_file_2.read()

    coroutines.append(fire(canvas, max_rows // 2, max_columns // 2))
    coroutines.append(animate_spaceship(canvas, max_rows // 2, max_columns // 2, spaceship_1, spaceship_2))

    for i in range(1, 101):
        coroutines.append(blink(canvas, random.randint(1, max_rows - 2), random.randint(1, max_columns - 1),
                                random.choice(star_symbols), i))
    
    while True:
        time.sleep(TIC_TIMEOUT)
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
      
        if len(coroutines) == 0:
            break

  
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    time.sleep(1)
