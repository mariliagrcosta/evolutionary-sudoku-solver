import numpy as np
import random
from .individual import Candidate

class Tournament(object):
    def __init__(self):
        self.tournament_size = 2
        return

    def compete(self, candidates):
        if not candidates:
            return None

        num_total_candidates = len(candidates)

        actual_tournament_size = min(self.tournament_size, num_total_candidates)

        if actual_tournament_size == 0:
            return None

        tournament_participants = random.sample(candidates, actual_tournament_size)

        best_participant = tournament_participants[0]

        best_fitness = best_participant.fitness if best_participant.fitness is not None else -float('inf')

        for i in range(1, len(tournament_participants)):
            participant = tournament_participants[i]
            participant_fitness = participant.fitness if participant.fitness is not None else -float('inf')
            if participant_fitness > best_fitness:
                best_fitness = participant_fitness
                best_participant = participant

        return best_participant

class CXCrossover(object):
    def __init__(self):
        return

    def crossover(self, parent1, parent2):
        child1 = Candidate()
        child2 = Candidate()

        if parent1 is None or parent2 is None or parent1.values is None or parent2.values is None:
            if parent1 is not None:
                child1.values = np.copy(parent1.values)
            else:
                child1.values = np.zeros((9,9))

            if parent2 is not None:
                child2.values = np.copy(parent2.values)
            else:
                child2.values = np.zeros((9,9))

            if parent1:
                child1.update_fitness()

            if parent2:
                child2.update_fitness()

            return child1, child2

        child1.values = np.copy(parent1.values)
        child2.values = np.copy(parent2.values)

        for k_row in range(9):
            if k_row < parent1.values.shape[0] and k_row < parent2.values.shape[0]:
                res_c1, res_c2 = self.cx_row_segment(parent1.values[k_row], parent2.values[k_row])
                if res_c1 is not None and res_c2 is not None:
                    child1.values[k_row] = res_c1
                    child2.values[k_row] = res_c2

        return child1, child2

    def cx_row_segment(self, row1_parent, row2_parent):
        n = len(row1_parent)
        child_row1 = np.zeros(n, dtype=int)
        child_row2 = np.zeros(n, dtype=int)
        
        cycles = []
        visited = [False] * n

        for i in range(n):
            if not visited[i]:
                cycle = []
                start_index = i
                current_index = i
                
                while not visited[current_index]:
                    cycle.append(current_index)
                    visited[current_index] = True
                    val_in_p1 = row1_parent[current_index]
                    
                    if val_in_p1 in row2_parent:
                        current_index = list(row2_parent).index(val_in_p1)
                    else:
                        break
                cycles.append(cycle)

        for i, cycle in enumerate(cycles):
            if i % 2 == 0:
                for index in cycle:
                    child_row1[index] = row1_parent[index]
                    child_row2[index] = row2_parent[index]
            else:
                for index in cycle:
                    child_row1[index] = row2_parent[index]
                    child_row2[index] = row1_parent[index]

        return child_row1, child_row2

def mutate(candidate, mutation_rate, given):
    r = random.uniform(0, 1.1)

    success = False
    if random.random() < mutation_rate:
        attempts = 0
        while not success and attempts < 50:
            attempts +=1
            row1 = random.randint(0, 8)

            mutable_columns = [col for col in range(9) if given.values[row1][col] == 0]

            if len(mutable_columns) >= 2:
                from_column, to_column = random.sample(mutable_columns, 2)

                temp = candidate.values[row1][to_column]
                candidate.values[row1][to_column] = candidate.values[row1][from_column]
                candidate.values[row1][from_column] = temp
                success = True

    return success