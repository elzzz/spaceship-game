import itertools
import time
import asyncio
import curses
import random

from curses_tools import draw_frame, read_controls, get_frame_size
from game_tools import get_garbage_animation_size, get_garbage_delay_tics, Obstacle
from physics import update_speed, _limit

TIC_TIMEOUT = 0.1
coroutines = []
obstacles = []
hit_obstacles = []
TRASH_ANIMATION_FILE_NAMES = [
    'trash_large.txt',
    'trash_small.txt',
    'trash_large.txt',
    'lamp.txt',
    'hubble.txt',
    'trash_xl.txt'
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
GAME_OVER = '''
   _____                         ____                 
  / ____|                       / __ \                
 | |  __  __ _ _ __ ___   ___  | |  | |_   _____ _ __ 
 | | |_ |/ _` | '_ ` _ \ / _ \ | |  | \ \ / / _ \ '__|
 | |__| | (_| | | | | | |  __/ | |__| |\ V /  __/ |   
  \_____|\__,_|_| |_| |_|\___|  \____/  \_/ \___|_|   
'''
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}
year = 1957


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', delay=0):
    while True:
        await sleep(delay)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(int(2 / TIC_TIMEOUT))

        canvas.addstr(row, column, symbol)
        await sleep(int(0.3 / TIC_TIMEOUT))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(int(5 / TIC_TIMEOUT))

        canvas.addstr(row, column, symbol)
        await sleep(int(0.3 / TIC_TIMEOUT))


async def fire(canvas, start_row, start_column, rows_speed=0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    draw_frame(canvas, row, column, '*')
    await sleep()
    draw_frame(canvas, row, column, 'O')
    await sleep()
    draw_frame(canvas, row, column, 'O', negative=True)
    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                hit_obstacles.append(obstacle)
                return

        draw_frame(canvas, row, column, symbol)
        await sleep()
        draw_frame(canvas, row, column, symbol, negative=True)
        row += rows_speed
        column += columns_speed


async def run_spaceship(canvas, start_row, start_column, spaceship_1, spaceship_2, row_speed=-.5, column_speed=0):
    spaceship_frames = itertools.cycle([spaceship_1, spaceship_2])
    spaceship_frame = next(spaceship_frames)
    animation_row_size, animation_column_size = get_frame_size(spaceship_frame)
    max_rows, max_columns = canvas.getmaxyx()
    min_animation_row, max_animation_row = 1, max_rows - animation_row_size - 1
    min_animation_column, max_animation_column = 1, max_columns - animation_column_size - 1

    while True:
        spaceship_frame = next(spaceship_frames)
        rows_direction, columns_directions, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_directions)

        start_row = _limit(start_row + row_speed, min_animation_row, max_animation_row)
        start_column = _limit(start_column + column_speed, min_animation_column, max_animation_column)

        draw_frame(canvas, start_row, start_column, spaceship_frame)
        await sleep()
        draw_frame(canvas, start_row, start_column, spaceship_frame, negative=True)

        if space_pressed and year >= 2020:
            coroutines.append(fire(canvas, start_row, start_column + 2, -2, 0))

        for obstacle in obstacles:
            if obstacle.has_collision(start_row, start_column, animation_row_size, animation_column_size):
                game_over_coroutine = show_game_over(canvas)
                coroutines.append(game_over_coroutine)
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number)

    row = 0

    garbage_rows_size, garbage_columns_size = get_frame_size(garbage_frame)

    obstacle = Obstacle(row, column, garbage_rows_size, garbage_columns_size)
    obstacles.append(obstacle)

    try:

        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await sleep()
            draw_frame(canvas, row, column, garbage_frame, negative=True)

            if obstacle in hit_obstacles:
                await explode(canvas, obstacle.center_row, obstacle.center_column)
                return

            row += speed
            obstacle.row = row
    finally:
        obstacles.remove(obstacle)
        if obstacle in hit_obstacles:
            hit_obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_animations):
    while True:
        delay = get_garbage_delay_tics(year)
        if not delay:
            await sleep()
            continue

        await sleep(delay)

        _, max_columns = canvas.getmaxyx()
        _, garbage_max_columns = get_garbage_animation_size(*garbage_animations)

        coroutines.append(fly_garbage(canvas, random.randint(1, max_columns - garbage_max_columns),
                                      random.choice(garbage_animations)))


async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in EXPLOSION_FRAMES:
        draw_frame(canvas, corner_row, corner_column, frame)

        await sleep()
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await sleep()


async def show_obstacles(canvas):
    """Display bounding boxes of every obstacle in a list"""

    while True:
        boxes = []

        for obstacle in obstacles:
            boxes.append(obstacle.dump_bounding_box())

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame)

        await asyncio.sleep(0)

        for row, column, frame in boxes:
            draw_frame(canvas, row, column, frame, negative=True)


async def show_game_over(canvas):
    max_rows, max_columns = canvas.getmaxyx()
    frame_rows_size, frame_columns_size = get_frame_size(GAME_OVER)
    center_phrase_row = max_rows / 2 - frame_rows_size / 2
    center_phrase_column = max_columns / 2 - frame_columns_size / 2

    while True:
        draw_frame(canvas, center_phrase_row, center_phrase_column, GAME_OVER)

        await sleep()
        draw_frame(canvas, center_phrase_row, center_phrase_column, GAME_OVER, negative=True)


async def count_years(canvas):
    rows, columns = canvas.getmaxyx()
    global year

    while True:
        phrase = PHRASES.get(year, '')
        message = f'Year {year}. {phrase}'
        phrase_row, phrase_column = rows - 2, columns // 2 - len(message) // 2

        draw_frame(canvas, phrase_row, phrase_column, message)
        await sleep(int(2 / TIC_TIMEOUT))
        draw_frame(canvas, phrase_row, phrase_column, message, negative=True)
        year += 1


def draw(canvas):
    garbage_animations = []
    max_rows, max_columns = canvas.getmaxyx()
    rows_inside_border, columns_inside_border = (1, max_rows - 1), (1, max_columns - 1)
    center_row, center_column = max_rows // 2, max_columns // 2
    star_symbols = ['+', '*', '.', ':']
    curses.curs_set(False)
    canvas.nodelay(True)

    with open('animations/rocket_frame_1.txt', 'r') as spaceship_file_1:
        spaceship_1 = spaceship_file_1.read()

    with open('animations/rocket_frame_2.txt', 'r') as spaceship_file_2:
        spaceship_2 = spaceship_file_2.read()

    for trash_animation_file_name in TRASH_ANIMATION_FILE_NAMES:
        with open(f'animations/{trash_animation_file_name}', 'r') as trash_animation_file:
            garbage_animations.append(trash_animation_file.read())

    for i in range(1, 101):
        coroutines.append(blink(canvas, random.randint(*rows_inside_border), random.randint(*columns_inside_border),
                                random.choice(star_symbols), i))

    coroutines.append(count_years(canvas))
    coroutines.append(run_spaceship(canvas, center_row, center_column, spaceship_1, spaceship_2))
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_animations))

    while coroutines:
        canvas.border()
        time.sleep(TIC_TIMEOUT)
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        canvas.refresh()

  
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    time.sleep(1)
