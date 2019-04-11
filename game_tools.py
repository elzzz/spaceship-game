from dataclasses import dataclass
import datetime

from curses_tools import get_frame_size


@dataclass
class Garbage:
    id: str
    row: float
    column: float
    rows_size: int
    columns_size: int
    health: int = 1

    def __init__(self, id, row, column, rows_size, columns_size, health=1):
        self.id = id
        self.row = row
        self.column = column
        self.rows_size = rows_size
        self.columns_size = columns_size
        self.health = health

    @property
    def center_row(self):
        return self.row + self.rows_size / 2

    @property
    def center_column(self):
        return self.column + self.columns_size / 2

    @property
    def can_be_broken(self):
        return self.health == 0


class CollisionHasOccured(Exception):
    pass


def can_spaceship_move(canvas, row, column, rows_offset, columns_offset, animation_row_size, animation_column_size):
    """Check if spaceship can move. Returns bool"""
    max_rows, max_columns = canvas.getmaxyx()

    conditions = [
        0 < row + rows_offset < max_rows,
        0 < row + rows_offset + animation_row_size < max_rows,
        0 < column + columns_offset < max_columns,
        0 < column + columns_offset + animation_column_size < max_columns
    ]

    return all(conditions)


def get_garbage_animation_size(*garbage_animations):
    rows, columns = [], []
    for garbage_animation in garbage_animations:
        garbage_animation_rows, garbage_animation_columns = get_frame_size(garbage_animation)
        rows.append(garbage_animation_rows)
        columns.append(garbage_animation_columns)

    return max(rows), max(columns)


def _is_point_inside(corner_row, corner_column, size_rows, size_columns, point_row, point_row_column):
    rows_flag = corner_row <= point_row < corner_row + size_rows
    columns_flag = corner_column <= point_row_column < corner_column + size_columns

    return rows_flag and columns_flag


def has_collision(obstacle_corner, obstacle_size, obj_corner, obj_size=(1, 1)):
    """Determine if collision has occured. Return True or False."""

    opposite_obstacle_corner = (
        obstacle_corner[0] + obstacle_size[0] - 1,
        obstacle_corner[1] + obstacle_size[1] - 1,
    )

    opposite_obj_corner = (
        obj_corner[0] + obj_size[0] - 1,
        obj_corner[1] + obj_size[1] - 1,
    )

    return any([
        _is_point_inside(*obstacle_corner, *obstacle_size, *obj_corner),
        _is_point_inside(*obstacle_corner, *obstacle_size, *opposite_obj_corner),

        _is_point_inside(*obj_corner, *obj_size, *obstacle_corner),
        _is_point_inside(*obj_corner, *obj_size, *opposite_obstacle_corner),
    ])


def get_time_played_delay(start_time):
    time_now = datetime.datetime.now()
    if time_now - start_time < datetime.timedelta(seconds=30):
        return 50
    elif time_now - start_time < datetime.timedelta(seconds=60):
        return 15
    elif time_now - start_time < datetime.timedelta(seconds=90):
        return 10
    else:
        return 5
