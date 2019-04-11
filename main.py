import datetime
import time
import asyncio
import curses
import random

from kombu import uuid

from curses_tools import draw_frame, read_controls, get_frame_size
from game_tools import can_spaceship_move, has_collision, get_garbage_animation_size, get_time_played_delay, \
    Garbage, CollisionHasOccured
from physics import update_speed, _limit

TIC_TIMEOUT = 0.1
coroutines = []
obstacles = []
obstacles_coroutines = {}
spaceship_frame = None
TRASH_ANIMATION_FILE_NAMES = [
    'trash_large.txt',
    'trash_small.txt'
]
EXPLOSION_FRAMES = [
    """\
           (_) 
       (  (   (  (
      () (  (  )
        ( )  ()
    """,
    """\
           (_) 
       (  (   (   
         (  (  )
          )  (
    """,
    """\
            (  
          (   (   
         (     (
          )  (
    """,
    """\
            ( 
              (
            (  
    """,
]


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', delay=0):
    while True:
        await sleep(delay)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if has_collision((obstacle.row, obstacle.column), (obstacle.rows_size, obstacle.columns_size), (row, column)):
                try:
                    obstacles_coroutines[obstacle.id].throw(CollisionHasOccured())
                except StopIteration:
                    coroutines.remove(obstacles_coroutines[obstacle.id])
                finally:
                    obstacles.remove(obstacle)
                    return
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def run_spaceship(canvas, start_row, start_column, spaceship_1, spaceship_2, row_speed=-.5, column_speed=0):

    while True:
        await animate_spaceship(spaceship_1, spaceship_2)
        rows_direction, columns_directions, space_pressed = read_controls(canvas)
        animation_row_size, animation_column_size = get_frame_size(spaceship_frame)
        max_rows, max_columns = canvas.getmaxyx()

        if can_spaceship_move(canvas, start_row, start_column, rows_direction, columns_directions, animation_row_size,
                              animation_column_size):
            start_row += rows_direction
            start_column += columns_directions

        draw_frame(canvas, start_row, start_column, spaceship_frame)
        canvas.refresh()
        draw_frame(canvas, start_row, start_column, spaceship_frame, negative=True)

        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_directions)

        start_row = _limit(start_row + row_speed, 1, max_rows - animation_row_size)
        start_column = _limit(start_column + column_speed, 1, max_columns - animation_column_size)

        if space_pressed:
            coroutines.append(fire(canvas, start_row, start_column + 2, -2, 0))


async def animate_spaceship(spaceship_1, spaceship_2):
    global spaceship_frame

    if spaceship_frame == spaceship_1:
        spaceship_frame = spaceship_2
    else:
        spaceship_frame = spaceship_1

    await sleep()


async def fly_garbage(canvas, column, garbage_frame, id, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    garbage_rows_size, garbage_columns_size = get_frame_size(garbage_frame)
    garbage = Garbage(id, row, column, garbage_rows_size, garbage_columns_size)

    if column > columns_number - garbage_columns_size - 1:
        column = columns_number - garbage_columns_size - 1

    while row < rows_number:
        try:
            obstacles.append(garbage)

            draw_frame(canvas, row, column, garbage_frame)
            draw_frame(canvas, row, column, f'{(garbage.row, garbage.column)}')

            await sleep()

            obstacles.remove(garbage)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            draw_frame(canvas, row, column, f'{(garbage.row, garbage.column)}', negative=True)
            row += speed
            garbage.row = row
        except CollisionHasOccured:
            garbage.health -= 1
            if garbage.can_be_broken:
                draw_frame(canvas, row, column, garbage_frame, negative=True)
                draw_frame(canvas, row, column, f'{(garbage.row, garbage.column)}', negative=True)
                await explode(canvas, garbage.center_row, garbage.center_column)
                break
            else:
                continue


async def fill_orbit_with_garbage(canvas, garbage_animations):
    while True:
        await sleep(get_time_played_delay(start_time))

        _, max_columns = canvas.getmaxyx()
        _, garbage_max_columns = get_garbage_animation_size(*garbage_animations)

        id = uuid()
        fly_garbage_coroutine = fly_garbage(canvas, random.randint(1, max_columns - garbage_max_columns),
                                            random.choice(garbage_animations), id)

        obstacles_coroutines[id] = fly_garbage_coroutine
        coroutines.append(fly_garbage_coroutine)


async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in EXPLOSION_FRAMES:
        draw_frame(canvas, corner_row, corner_column, frame)

        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)


def draw(canvas):
    garbage_animations = []
    max_rows, max_columns = canvas.getmaxyx()
    star_symbols = ['+', '*', '.', ':']
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)
    global start_time
    start_time = datetime.datetime.now()

    with open('animations/rocket_frame_1.txt', 'r') as spaceship_file_1:
        spaceship_1 = spaceship_file_1.read()

    with open('animations/rocket_frame_2.txt', 'r') as spaceship_file_2:
        spaceship_2 = spaceship_file_2.read()

    for trash_animation_file_name in TRASH_ANIMATION_FILE_NAMES:
        with open(f'animations/{trash_animation_file_name}', 'r') as trash_animation_file:
            garbage_animations.append(trash_animation_file.read())

    coroutines.append(fire(canvas, max_rows // 2, max_columns // 2))
    coroutines.append(run_spaceship(canvas, max_rows // 2, max_columns // 2, spaceship_1, spaceship_2))
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_animations))

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
            except AttributeError:
                coroutines.remove(coroutine)

        if len(coroutines) == 0:
            break

  
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    time.sleep(1)
