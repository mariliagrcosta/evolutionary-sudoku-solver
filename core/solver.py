import numpy as np
import random
import operator

from .config import *
from .individual import Candidate, Fixed
from .population import Population
from .genetic_operators import Tournament, CXCrossover, mutate

random.seed()

class Sudoku(object):

    def __init__(self):
        self.given = None
        return

    def load(self, p_values):
        self.given = Fixed(p_values)
        return

    def solve(self, progress_callback=None):
        population_size_used = POPULATION_SIZE
        quant_elite_used = int(ELITE_PERCENTAGE * population_size_used)
        if quant_elite_used % 2 != 0 and (population_size_used - quant_elite_used) > 0:
            quant_elite_used = max(0, quant_elite_used -1)

        num_generations_to_run = MAX_GENERATIONS
        mutation_rate = INITIAL_MUTATION_RATE
        sigma = 1.0
        phi_accumulator = 0
        total_mutations_attempted = 0
        fitness_history = []
        boxplot_data_per_generation = [] 

        reseed_count = 0

        default_return_metrics = {
            'final_mutation_rate': INITIAL_MUTATION_RATE,
            'final_sigma': sigma,
            'final_phi_success_rate': 0.0,
            'reseed_count': reseed_count,
            'fitness_history': fitness_history,
            'boxplot_data': boxplot_data_per_generation,
            'generation': -1,
            'solution_candidate': None,
            'solution_index': -1
        }

        if self.given is None or self.given.values is None or self.given.no_duplicates() == False:
            return default_return_metrics

        self.population = Population()
        seed_success = self.population.seed(population_size_used, self.given)
        if seed_success != 1:
            default_return_metrics['boxplot_data'] = boxplot_data_per_generation
            return default_return_metrics

        for generation_num in range(0, num_generations_to_run):
            self.population.update_fitness()
            all_fitness_values = [c.fitness for c in self.population.candidates if c.fitness is not None]

            if all_fitness_values: 
                boxplot_data_per_generation.append({
                    'Geracao': generation_num,
                    'Todas_Aptidoes': list(all_fitness_values)
                })

            solution_found_candidate = None
            solution_index = -1
            max_f, min_f, avg_f = 0.0, 0.0, 0.0

            if all_fitness_values:
                max_f = np.max(all_fitness_values)
                min_f = np.min(all_fitness_values)
                avg_f = np.mean(all_fitness_values)
                median_f = np.median(all_fitness_values)
                fitness_history.append({
                    'Geracao': generation_num,
                    'Maior_Aptidao': max_f,
                    'Menor_Aptidao': min_f,
                    'Media_Aptidao': avg_f
                })
                if abs(max_f - 1.0) < 1e-9:
                    for idx, c_sol in enumerate(self.population.candidates):
                        if c_sol.fitness is not None and abs(c_sol.fitness - 1.0) < 1e-9 :
                            if not np.any(c_sol.values == 0) and Fixed(c_sol.values).no_duplicates():
                                solution_found_candidate = c_sol
                                solution_index = idx
                                break


            if progress_callback:
                self.population.sort()
                best_candidate_current_gen = self.population.candidates[0] if self.population.candidates else None
                total_individuals_current = (generation_num + 1) * population_size_used
                progress_callback(generation_num, best_candidate_current_gen, total_individuals_current, max_f)

            if solution_found_candidate:
                phi_success_rate = phi_accumulator / total_mutations_attempted if total_mutations_attempted > 0 else 0.0
                return {'generation': generation_num,
                        'solution_candidate': solution_found_candidate,
                        'solution_index': solution_index,
                        'final_mutation_rate': mutation_rate,
                        'final_sigma': sigma,
                        'final_phi_success_rate': phi_success_rate,
                        'reseed_count': reseed_count,
                        'fitness_history': fitness_history,
                        'boxplot_data': boxplot_data_per_generation 
                        }

            self.population.sort()

            tourney_selector = Tournament()
            
            pmx_crossover_op = CXCrossover()
            offspring_population = []

            parent_pool = self.population.candidates

            while len(offspring_population) < population_size_used:
                parent1 = tourney_selector.compete(parent_pool)
                parent2 = tourney_selector.compete(parent_pool)

                if parent1 is None or parent2 is None:
                    continue

                child1, child2 = pmx_crossover_op.crossover(parent1, parent2)

                if child1 is not None and child1.values is not None:
                    child1.update_fitness()
                    old_fitness_c1 = child1.fitness if child1.fitness is not None else -1.0
                    mutation_performed_c1 = mutate(child1, mutation_rate, self.given)
                    if mutation_performed_c1:
                        total_mutations_attempted += 1
                        child1.update_fitness()
                        if child1.fitness > old_fitness_c1: phi_accumulator += 1
                    offspring_population.append(child1)

                if len(offspring_population) >= population_size_used:
                    break

                if child2 is not None and child2.values is not None:
                    child2.update_fitness()
                    old_fitness_c2 = child2.fitness if child2.fitness is not None else -1.0
                    mutation_performed_c2 = mutate(child2, mutation_rate, self.given)
                    if mutation_performed_c2:
                        total_mutations_attempted += 1
                        child2.update_fitness()
                        if child2.fitness > old_fitness_c2: phi_accumulator += 1
                    offspring_population.append(child2)

            combined_population = self.population.candidates + offspring_population
            combined_population = sorted(
                [c for c in combined_population if c.fitness is not None],
                key=operator.attrgetter('fitness'),
                reverse=True
            )

            next_population_candidates = []

            num_elites = min(quant_elite_used, len(combined_population))
            next_population_candidates.extend(combined_population[:num_elites])

            tournament_pool = combined_population[num_elites:]
            
            num_to_select_from_tournament = population_size_used - len(next_population_candidates)
            
            for _ in range(num_to_select_from_tournament):
                if len(tournament_pool) < 2:
                    if tournament_pool:
                        next_population_candidates.append(tournament_pool.pop())
                    break

                participant1, participant2 = random.sample(tournament_pool, 2)
                
                winner = participant1 if participant1.fitness >= participant2.fitness else participant2
                
                next_population_candidates.append(winner)
                tournament_pool.remove(winner)
            
            idx_filler = 0
            while len(next_population_candidates) < population_size_used:
                if not combined_population: break
                filler_candidate = Candidate()
                source_candidate = combined_population[idx_filler % len(combined_population)]
                if source_candidate.values is not None:
                    filler_candidate.values = np.copy(source_candidate.values)
                    filler_candidate.update_fitness()
                    next_population_candidates.append(filler_candidate)
                idx_filler += 1
                if idx_filler > 2 * population_size_used: break

            if not next_population_candidates:
                if self.population.seed(population_size_used, self.given) != 1:
                    phi_success_rate = phi_accumulator / total_mutations_attempted if total_mutations_attempted > 0 else 0.0
                    default_return_metrics.update({
                        'generation': -2, 'final_mutation_rate': mutation_rate, 'final_sigma': sigma,
                        'final_phi_success_rate': phi_success_rate, 'reseed_count': reseed_count,
                        'fitness_history': fitness_history,
                        'boxplot_data': boxplot_data_per_generation,
                        'solution_index': -1
                        })
                    return default_return_metrics
            else:
                 self.population.candidates = next_population_candidates

            if 'max_f' in locals() and 'median_f' in locals() and max_f > 0:
                
                amplitude_reduction = 1.0 - max_f

                upper_bound = max_f * (1.0 - (1.0 - MEDIAN_FITNESS_UPPER_BOUND_RATIO) * amplitude_reduction)
                lower_bound = max_f * (1.0 - (1.0 - MEDIAN_FITNESS_LOWER_BOUND_RATIO) * amplitude_reduction)

                if median_f > upper_bound:
                    mutation_rate += MUTATION_RATE_ADJUSTMENT_STEP
                elif median_f < lower_bound:
                    mutation_rate -= MUTATION_RATE_ADJUSTMENT_STEP
                
                mutation_rate = max(MIN_MUTATION_RATE, min(mutation_rate, MAX_MUTATION_RATE))

        phi_success_rate_final = phi_accumulator / total_mutations_attempted if total_mutations_attempted > 0 else 0.0
        best_candidate_at_end = None

        if self.population.candidates:
            self.population.sort()
            best_candidate_at_end = self.population.candidates[0]
            if best_candidate_at_end and hasattr(best_candidate_at_end, 'values') and best_candidate_at_end.values is not None:
                if not (abs(best_candidate_at_end.fitness - 1.0) < 1e-9 and \
                        not np.any(best_candidate_at_end.values == 0) and \
                        Fixed(best_candidate_at_end.values).no_duplicates()):
                     pass
            else:
                best_candidate_at_end = None

        default_return_metrics.update({
            'generation': -2,
            'solution_candidate': best_candidate_at_end,
            'solution_index': -1,
            'final_mutation_rate': mutation_rate,
            'final_sigma': sigma,
            'final_phi_success_rate': phi_success_rate_final,
            'reseed_count': reseed_count,
            'fitness_history': fitness_history,
            'boxplot_data': boxplot_data_per_generation 
        })
        return default_return_metrics