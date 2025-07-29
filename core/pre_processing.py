import numpy as np

class PreProcessing(object):

    def __init__(self, sudoku):

        self.sudoku = sudoku
        self.candidates_matrix = np.full((9, 9), None)
        self.checked_naked_pairs = []
        self.map_initial_candidates()

    def map_initial_candidates(self):

        for row in range(9):
            for col in range(9):
                if self.sudoku[row, col] == 0:
                    self.candidates_matrix[row, col] = self.get_candidates(row, col)
                else:
                    self.candidates_matrix[row, col] = set()

    def get_candidates(self, row, col):

        all_numbers = set(range(1, 10))
        used_numbers = set(self.sudoku[row, :]) | set(self.sudoku[:, col])
        grid_row = (row // 3) * 3
        grid_col = (col // 3) * 3
        used_numbers |= set(self.sudoku[grid_row:grid_row+3, grid_col:grid_col+3].flatten())
        candidates = all_numbers - used_numbers
        return candidates

    def analyze_cell(self, row, col):

        sudoku_updated = False

        candidates = self.candidates_matrix[row, col]

        # Naked Single/Obvious Single
        if len(candidates) == 1:
            self.sudoku[row, col] = candidates.pop()
            self.update_candidates(row, col)
            sudoku_updated = True

        if sudoku_updated:
            return True

        # Naked Pair/Obvius Pairs
        for group_type, group_indice in [
            ("row", [(row, i) for i in range(9)]),
            ("col", [(i, col) for i in range(9)]),
            ("subgrid", [(row // 3 * 3 + r, col // 3 * 3 + c) for r in range(3) for c in range(3)])
        ]:
            pairs = {}
            for r, c in group_indice:
                if self.sudoku[r, c] == 0 and len(self.candidates_matrix[r, c]) == 2:
                    candidates_tuple = tuple(sorted(self.candidates_matrix[r, c]))
                    if candidates_tuple in pairs:
                        pairs[candidates_tuple].append((r, c))
                    else:
                        pairs[candidates_tuple] = [(r, c)]

            for candidates_tuple, cells in pairs.items():
                if len(cells) == 2:
                    r1, c1 = cells[0]
                    r2, c2 = cells[1]
                    is_naked_pair = True
                    if [(r1,c1), (r2,c2)] not in self.checked_naked_pairs:
                        for r, c in group_indice:
                            if (r, c) not in cells and len(self.candidates_matrix[r, c]) == 2:
                                if all(candidate in self.candidates_matrix[r, c] for candidate in candidates_tuple):
                                    is_naked_pair = False
                                    break
                        if is_naked_pair:
                            self.checked_naked_pairs.append([(r1,c1), (r2,c2)])
                            for r, c in group_indice:
                                if (r, c) not in cells and self.candidates_matrix[r, c]:
                                    self.candidates_matrix[r, c] -= set(candidates_tuple)
                                    sudoku_updated = True

        if sudoku_updated:
            return True

        # Hidden Single
        for group_type in ["row", "col", "subgrid"]:

            for index in range(9):
                if group_type == "row":
                    group_indice = [(index, i) for i in range(9)]
                elif group_type == "col":
                    group_indice = [(i, index) for i in range(9)]
                elif group_type == "subgrid":
                    row_start, col_start = (index // 3) * 3, (index % 3) * 3
                    group_indice = [(row_start + r, col_start + c) for r in range(3) for c in range(3)]
                
                for candidate in range(1, 10):
                    count = 0
                    last_position = None
                    for r, c in group_indice:
                        if self.sudoku[r, c] == 0 and candidate in self.candidates_matrix[r, c]:
                            count += 1
                            last_position = (r, c)

                    if count == 1 and last_position:
                        self.sudoku[last_position[0], last_position[1]] = candidate
                        self.update_candidates(last_position[0], last_position[1])
                        sudoku_updated = True

        if sudoku_updated:
            return True
        else:
            return False

    # X-Wings
    def x_wing(self):

        updated_in_x_wing = False

        for number in range(1, 10):
            row_pairs = {}
            for r in range(9):
                cols_with_num = [c for c in range(9) if self.sudoku[r, c] == 0 and number in self.candidates_matrix[r, c]]
                if len(cols_with_num) == 2:
                    cols_tuple = tuple(cols_with_num)
                    if cols_tuple not in row_pairs:
                        row_pairs[cols_tuple] = []
                    row_pairs[cols_tuple].append(r)

            for cols, rows in row_pairs.items():
                if len(rows) == 2:
                    col1, col2 = cols
                    row1, row2 = rows
                    for r_idx in range(9):
                        if r_idx not in rows:
                            if self.sudoku[r_idx, col1] == 0 and number in self.candidates_matrix[r_idx, col1]:
                                self.candidates_matrix[r_idx, col1].remove(number)
                                updated_in_x_wing = True
                            if self.sudoku[r_idx, col2] == 0 and number in self.candidates_matrix[r_idx, col2]:
                                self.candidates_matrix[r_idx, col2].remove(number)
                                updated_in_x_wing = True

        for number in range(1, 10):
            col_pairs = {}
            for c in range(9):
                rows_with_num = [r for r in range(9) if self.sudoku[r, c] == 0 and number in self.candidates_matrix[r, c]]
                if len(rows_with_num) == 2:
                    rows_tuple = tuple(rows_with_num)
                    if rows_tuple not in col_pairs:
                        col_pairs[rows_tuple] = []
                    col_pairs[rows_tuple].append(c)
        
            for rows, cols in col_pairs.items():
                if len(cols) == 2:
                    row1, row2 = rows
                    col1, col2 = cols
                    for c_idx in range(9):
                        if c_idx not in cols:
                            if self.sudoku[row1, c_idx] == 0 and number in self.candidates_matrix[row1, c_idx]:
                                self.candidates_matrix[row1, c_idx].remove(number)
                                updated_in_x_wing = True
                            if self.sudoku[row2, c_idx] == 0 and number in self.candidates_matrix[row2, c_idx]:
                                self.candidates_matrix[row2, c_idx].remove(number)
                                updated_in_x_wing = True

        return updated_in_x_wing

    def update_candidates(self, row, col):

        placed_number = self.sudoku[row,col]

        for c in range (9):
            if placed_number in self.candidates_matrix[row, c]:
                self.candidates_matrix[row, c].remove(placed_number)

        for r in range (9):
            if placed_number in self.candidates_matrix[r, col]:
                self.candidates_matrix[r, col].remove(placed_number)

        grid_row = (row // 3) * 3
        grid_col = (col // 3) * 3

        for r in range(grid_row, grid_row + 3):
            for c in range(grid_col, grid_col + 3):
                if placed_number in self.candidates_matrix[r, c]:
                    self.candidates_matrix[r, c].remove(placed_number)

    def preprocess(self):
        initial_zeros = np.count_nonzero(self.sudoku == 0)
        updated = True
        while updated:
            updated = False
            for row in range(9):
                for col in range(9):
                    if self.sudoku[row, col] == 0:
                        if self.analyze_cell(row, col):
                            updated = True
            
            if self.x_wing():
                updated = True

        final_zeros = np.count_nonzero(self.sudoku == 0)
        numbers_filled_by_pp = initial_zeros - final_zeros
        return self.sudoku, numbers_filled_by_pp

class Controller(object):

    def __init__(self):
        return

    def load(self, p):
        self.sudoku = p
        return

    def controller(self):
        preprocessor = PreProcessing(self.sudoku)
        final_board, numbers_filled = preprocessor.preprocess()
        return final_board, numbers_filled