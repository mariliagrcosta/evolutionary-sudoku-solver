import numpy as np

class Candidate(object):

    def __init__(self):
        self.values = np.zeros((9, 9))
        self.fitness = None
        return

    def update_fitness(self):
        column_sum = 0
        block_sum = 0
        self.values = self.values.astype(int)

        for j in range(0, 9):
            column_values_for_count = self.values[:, j]
            unique_elements_col, counts_in_col = np.unique(column_values_for_count[column_values_for_count != 0], return_counts=True)
            column_sum += np.sum(counts_in_col == 1)

        column_sum = column_sum / 81

        for r_offset in range(0, 9, 3):
            for c_offset in range(0, 9, 3):
                block_values_for_count = self.values[r_offset:r_offset+3, c_offset:c_offset+3].flatten()
                unique_elements_block, counts_in_block = np.unique(block_values_for_count[block_values_for_count != 0], return_counts=True)
                block_sum += np.sum(counts_in_block == 1)

        block_sum = block_sum / (9 * 9)

        if abs(column_sum - 1.0) < 1e-9 and abs(block_sum - 1.0) < 1e-9 :
            fitness = 1.0
        else:
            fitness = column_sum * block_sum
        self.fitness = fitness
        return

    def _get_col_counts(self, col_idx):
        counts = np.zeros(10, dtype=int)
        for r_idx in range(9):
            val = self.values[r_idx, col_idx]
            if 0 <= val <= 9:
                 counts[val] += 1
        return counts

    def _get_block_counts(self, block_r_start, block_c_start):
        counts = np.zeros(9 + 1, dtype=int)
        for r_offset_val in range(3):
            for c_offset_val in range(3):
                val = self.values[block_r_start + r_offset_val, block_c_start + c_offset_val]
                if 0 <= val <= 9:
                    counts[val] += 1
        return counts

class Fixed(Candidate):
    def __init__(self, values):
        self.values = values
        self.fitness = None
        return

    def is_row_duplicate(self, row_idx, value):
        for column_idx in range(0, 9):
            if self.values[row_idx][column_idx] == value:
                return True
        return False

    def is_column_duplicate(self, column_idx, value):
        for row_idx in range(0, 9):
            if self.values[row_idx][column_idx] == value:
                return True
        return False

    def is_block_duplicate(self, row_idx, column_idx, value):
        i_start = 3 * (row_idx // 3)
        j_start = 3 * (column_idx // 3)

        for r_block_offset in range(3):
            for c_block_offset in range(3):
                if self.values[i_start + r_block_offset][j_start + c_block_offset] == value:
                    return True
        return False

    def no_duplicates(self):
        for r_idx in range(0, 9):
            for c_idx in range(0, 9):
                val = self.values[r_idx][c_idx]
                if val != 0:
                    for c_check in range(0, 9):
                        if c_check != c_idx and self.values[r_idx][c_check] == val:
                            return False
                    for r_check in range(0, 9):
                        if r_check != r_idx and self.values[r_check][c_idx] == val:
                            return False
                    block_row_start = (r_idx // 3) * 3
                    block_col_start = (c_idx // 3) * 3
                    for r_b_offset in range(block_row_start, block_row_start + 3):
                        for c_b_offset in range(block_col_start, block_col_start + 3):
                            if (r_b_offset != r_idx or c_b_offset != c_idx) and self.values[r_b_offset][c_b_offset] == val:
                                return False
        return True