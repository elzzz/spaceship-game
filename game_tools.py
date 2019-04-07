from curses_tools import get_frame_size


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


def get_spaceship_animation_size(spaceship_1, spaceship_2):
    spaceship_1_rows, spaceship_1_columns = get_frame_size(spaceship_1)
    spaceship_2_rows, spaceship_2_columns = get_frame_size(spaceship_2)
    return max(spaceship_1_rows, spaceship_2_rows), max(spaceship_1_columns, spaceship_2_columns)
