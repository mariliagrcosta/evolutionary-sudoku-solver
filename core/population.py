import numpy as np
import random
import operator
from .individual import Candidate

class Population(object):

    def __init__(self):
        self.candidates = []
        return

    def seed(self, population, given):
        self.candidates = []
        helper = Candidate()
        helper.values = [[[] for j in range(0, 9)] for i in range(0, 9)]
        for row in range(0, 9):
            for column in range(0, 9):
                for value in range(1, 10):
                    if ((given.values[row][column] == 0) and not (given.is_column_duplicate(column, value) or given.is_block_duplicate(row, column, value) or given.is_row_duplicate(row, value))):
                        helper.values[row][column].append(value)
                    elif given.values[row][column] != 0:
                        helper.values[row][column].append(given.values[row][column])
                        break
        
        max_generation_attempts = 500000

        for p in range(0, population):
            g = Candidate()
            for i in range(0, 9):
                row_values = np.zeros(9)
                for j in range(0, 9):
                    if given.values[i][j] != 0:
                        row_values[j] = given.values[i][j]
                    elif given.values[i][j] == 0:
                        if not helper.values[i][j]:
                            row_values[j] = 0
                        else:
                            row_values[j] = helper.values[i][j][random.randint(0, len(helper.values[i][j]) - 1)]
                
                try_count = 0

                while len(list(set(row_values))) != 9:
                    try_count += 1
                    if try_count > max_generation_attempts:
                        problematic_indices = [idx for idx, val in enumerate(given.values[i]) if val == 0]
                        random.shuffle(problematic_indices)
                        temp_row = np.copy(given.values[i])
                        numbers_to_fill = [n for n in range(1,10) if n not in temp_row]
                        random.shuffle(numbers_to_fill)

                        current_index  = 0
                        for problematic_idx in problematic_indices:
                            if current_index  < len(numbers_to_fill):
                                temp_row[problematic_idx] = numbers_to_fill[current_index ]
                                current_index  +=1
                            else:
                                temp_row[problematic_idx] = 0
                        
                        row_values = temp_row
                        
                        if len(list(set(row_values))) != 9 and 0 not in row_values:
                             fixed_elements = {val for val in given.values[i] if val != 0}
                             available_numbers = [n for n in range(1,10) if n not in fixed_elements]
                             random.shuffle(available_numbers)

                             current_fill_idx = 0
                             new_row_attempt = np.zeros(9, dtype=int)
                             for col_idx_fill in range(9):
                                 if given.values[i][col_idx_fill] != 0:
                                     new_row_attempt[col_idx_fill] = given.values[i][col_idx_fill]
                                 else:
                                     if current_fill_idx < len(available_numbers):
                                         new_row_attempt[col_idx_fill] = available_numbers[current_fill_idx]
                                         current_fill_idx +=1
                                     else:
                                         new_row_attempt[col_idx_fill] = 0
                             row_values = new_row_attempt

                        if try_count > 500001 and len(list(set(row_values))) != 9:
                            return 0


                    for j_idx in range(0, 9):
                        if given.values[i][j_idx] == 0:
                            if not helper.values[i][j_idx]:
                                row_values[j_idx] = 0
                            else:
                                row_values[j_idx] = helper.values[i][j_idx][random.randint(0, len(helper.values[i][j_idx]) - 1)]
                g.values[i] = row_values
            self.candidates.append(g)
        self.update_fitness()
        return 1

    def update_fitness(self):
        for candidate in self.candidates:
            candidate.update_fitness()
        return

    def sort(self):
        self.candidates = sorted([c for c in self.candidates if c.fitness is not None],
                                 key=operator.attrgetter('fitness'),
                                 reverse=True)
        return