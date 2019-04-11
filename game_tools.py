from dataclasses import dataclass

from curses_tools import get_frame_size


@dataclass
class Obstacle:
    row: float
    column: float
    rows_size: int = 1
    columns_size: int = 1
    uid: str = None

    def __init__(self, row, column, rows_size=1, columns_size=1, uid=None):
        self.row = row
        self.column = column
        self.rows_size = rows_size
        self.columns_size = columns_size
        self.uid = uid

    @property
    def center_row(self):
        return self.row + self.rows_size / 2

    @property
    def center_column(self):
        return self.column + self.columns_size / 2

    def get_bounding_box_frame(self):
        # increment box size to compensate obstacle movement
        rows, columns = self.rows_size + 1, self.columns_size + 1
        return '\n'.join(_get_bounding_box_lines(rows, columns))

    def get_bounding_box_corner_pos(self):
        return self.row - 1, self.column - 1

    def dump_bounding_box(self):
        row, column = self.get_bounding_box_corner_pos()
        return row, column, self.get_bounding_box_frame()

    def has_collision(self, obj_corner_row, obj_corner_column, obj_size_rows=1, obj_size_columns=1):
        """Determine if collision has occured. Return True or False."""
        return has_collision(
            (self.row, self.column),
            (self.rows_size, self.columns_size),
            (obj_corner_row, obj_corner_column),
            (obj_size_rows, obj_size_columns),
        )

    def __str__(self):
        return f'r{self.row} r{self.column}'


def _get_bounding_box_lines(rows, columns):
    yield ' ' + '-' * columns + ' '
    for _ in range(rows):
        yield '|' + ' ' * columns + '|'
    yield ' ' + '-' * columns + ' '


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


def get_garbage_delay_tics(year):
    if year < 1961:
        return 25
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2
