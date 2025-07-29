import os
import numpy as np
import time
import re
import pandas as pd
import datetime

from core.config import *
from core import solver as ga
from core import pre_processing as pp
from utils import fitness_reporter


def load_puzzle_from_file(file_path):
    puzzle_content_lines = []
    try:
        with open(file_path, "r") as input_file:
            for line in input_file:
                processed_line = line.strip()
                if not processed_line: continue
                if processed_line.startswith("["): continue
                puzzle_content_lines.append(processed_line)

        if len(puzzle_content_lines) != 9:
            return None

        full_puzzle_string = "".join(puzzle_content_lines)
        processed_puzzle_string = full_puzzle_string.replace('-', '0').replace('.', '0')
        cleaned_puzzle_string = re.sub(r"[^0-9]", "", processed_puzzle_string)

        if len(cleaned_puzzle_string) != 81:
            return None

        return np.array(list(cleaned_puzzle_string)).reshape((9, 9)).astype(int)
    except Exception as e:
        return None


def run_solver_for_puzzle(puzzle_data_orig, use_preprocessing=True):
    puzzle_data_for_run = np.copy(puzzle_data_orig)
    results = {
        'time_pp_s': "0.000",
        'time_ag_s': "0.000",
        'time_total_s': "0.000",
        'numbers_filled_by_pp': 0,
        'ag_generations_taken': 'N/A',
        'ag_solution_position': 'N/A',
        'ag_final_mutation_rate': 'N/A',
        'ag_final_sigma': 'N/A',
        'ag_final_phi_success_rate': 'N/A',
        'ag_reseed_count': 0,
        'ag_total_individuals_generated': 'N/A',
        'final_status': 'Pendente',
        'final_board_state': np.copy(puzzle_data_for_run),
        'solved_by_pp_only': False,
        'error_message': '',
        'fitness_history': [],
        'boxplot_data': []
    }
    ga_sudoku_instance = ga.Sudoku()

    time_pp_val = 0.0
    time_ag_val = 0.0
    overall_start_time = time.time()

    try:
        if use_preprocessing:
            time_pp_start_local = time.time()
            pp_controller = pp.Controller()
            pp_controller.load(np.copy(puzzle_data_for_run))
            processed_puzzle, numbers_filled = pp_controller.controller()
            time_pp_val = time.time() - time_pp_start_local
            results['numbers_filled_by_pp'] = numbers_filled
            results['final_board_state'] = np.copy(processed_puzzle)

            if not np.any(processed_puzzle == 0):
                checker_board = ga.Fixed(processed_puzzle)
                if checker_board.no_duplicates():
                    results['final_status'] = "Resolvido (Pré-proc.)"
                    results['solved_by_pp_only'] = True
                    results['ag_generations_taken'] = 0
                    results['ag_reseed_count'] = 0
                    results['ag_total_individuals_generated'] = 0
                else:
                    results['final_status'] = "Erro (Pré-proc. inválido)"
                    results['solved_by_pp_only'] = False
                    results['error_message'] = "Pré-processamento resultou em tabuleiro inválido."
            else:
                ga_sudoku_instance.load(processed_puzzle)
                time_ag_start_local = time.time()
                solve_output = ga_sudoku_instance.solve()
                time_ag_val = time.time() - time_ag_start_local

                gen_val = solve_output['generation']
                results['ag_generations_taken'] = gen_val
                
                sol_idx = solve_output.get('solution_index', -1)
                if gen_val is not None and isinstance(gen_val, int) and gen_val >= 0 and sol_idx != -1:
                    results['ag_solution_position'] = (gen_val * POPULATION_SIZE) + (sol_idx + 1)
                else:
                    results['ag_solution_position'] = 'N/A'

                results['ag_final_mutation_rate'] = f"{solve_output['final_mutation_rate']:.4f}" if isinstance(solve_output['final_mutation_rate'], (int, float)) else 'N/A'
                results['ag_final_sigma'] = f"{solve_output['final_sigma']:.4f}" if isinstance(solve_output['final_sigma'], (int, float)) else 'N/A'
                results['ag_final_phi_success_rate'] = f"{solve_output['final_phi_success_rate']:.4f}" if isinstance(solve_output['final_phi_success_rate'], (int, float)) else 'N/A'
                results['ag_reseed_count'] = solve_output.get('reseed_count', 0)
                results['fitness_history'] = solve_output.get('fitness_history', [])
                results['boxplot_data'] = solve_output.get('boxplot_data', [])

                effective_gen_cycles = 0
                if gen_val is not None and isinstance(gen_val, int) and gen_val >= 0: effective_gen_cycles = gen_val + 1
                elif gen_val is not None and isinstance(gen_val, int) and gen_val == -2: effective_gen_cycles = MAX_GENERATIONS

                pop_size_for_calc = POPULATION_SIZE if isinstance(POPULATION_SIZE, int) else 0
                results['ag_total_individuals_generated'] = (effective_gen_cycles) * pop_size_for_calc if gen_val != -1 else 0

                solution_candidate = solve_output['solution_candidate']
                if solution_candidate and hasattr(solution_candidate, 'values') and gen_val not in [-1, -2]:
                    final_board_ag = solution_candidate.values
                    if not np.any(final_board_ag == 0):
                        checker_board_ag = ga.Fixed(final_board_ag)
                        if checker_board_ag.no_duplicates():
                            results['final_status'] = "Resolvido (AG)"
                            results['final_board_state'] = np.copy(final_board_ag)
                        else:
                            results['final_status'] = "Erro (AG - Sol. Inválida)"
                            results['error_message'] = "AG produziu uma solução com duplicatas."
                            results['final_board_state'] = np.copy(final_board_ag) if final_board_ag is not None else np.copy(processed_puzzle)
                    else:
                        results['final_status'] = "Erro (AG - Sol. Incompleta)"
                        results['error_message'] = "AG produziu uma solução com células vazias (0)."
                        results['final_board_state'] = np.copy(final_board_ag) if final_board_ag is not None else np.copy(processed_puzzle)
                elif gen_val == -1: results['final_status'] = "Entrada Inválida (AG)"
                elif gen_val == -2:
                    results['final_status'] = "Não Resolvido (AG)"
                    results['ag_generations_taken'] = "Limite de Gerações Atingido" 
                    if solution_candidate and hasattr(solution_candidate, 'values'):
                        results['final_board_state'] = np.copy(solution_candidate.values)

        else:
            ga_sudoku_instance.load(puzzle_data_for_run)
            time_ag_start_local = time.time()
            solve_output = ga_sudoku_instance.solve()
            time_ag_val = time.time() - time_ag_start_local

            gen_val = solve_output['generation']
            results['ag_generations_taken'] = gen_val

            sol_idx = solve_output.get('solution_index', -1)
            if gen_val is not None and isinstance(gen_val, int) and gen_val >= 0 and sol_idx != -1:
                results['ag_solution_position'] = (gen_val * POPULATION_SIZE) + (sol_idx + 1)
            else:
                results['ag_solution_position'] = 'N/A'
            
            results['ag_final_mutation_rate'] = f"{solve_output['final_mutation_rate']:.4f}" if isinstance(solve_output['final_mutation_rate'], (int, float)) else 'N/A'
            results['ag_final_sigma'] = f"{solve_output['final_sigma']:.4f}" if isinstance(solve_output['final_sigma'], (int, float)) else 'N/A'
            results['ag_final_phi_success_rate'] = f"{solve_output['final_phi_success_rate']:.4f}" if isinstance(solve_output['final_phi_success_rate'], (int, float)) else 'N/A'
            results['ag_reseed_count'] = solve_output.get('reseed_count', 0)
            results['fitness_history'] = solve_output.get('fitness_history', [])
            results['boxplot_data'] = solve_output.get('boxplot_data', [])

            effective_gen_cycles = 0
            if gen_val is not None and isinstance(gen_val, int) and gen_val >= 0: effective_gen_cycles = gen_val + 1
            elif gen_val is not None and isinstance(gen_val, int) and gen_val == -2: effective_gen_cycles = MAX_GENERATIONS
            pop_size_for_calc = POPULATION_SIZE if isinstance(POPULATION_SIZE, int) else 0
            results['ag_total_individuals_generated'] = (effective_gen_cycles) * pop_size_for_calc if gen_val != -1 else 0

            results['final_board_state'] = np.copy(puzzle_data_for_run)
            solution_candidate = solve_output['solution_candidate']

            if solution_candidate and hasattr(solution_candidate, 'values') and gen_val not in [-1, -2]:
                final_board_ag_no_pp = solution_candidate.values
                if not np.any(final_board_ag_no_pp == 0):
                    checker_board_ag_no_pp = ga.Fixed(final_board_ag_no_pp)
                    if checker_board_ag_no_pp.no_duplicates():
                        results['final_status'] = "Resolvido (AG)"
                        results['final_board_state'] = np.copy(final_board_ag_no_pp)
                    else:
                        results['final_status'] = "Erro (AG - Sol. Inválida)"
                        results['error_message'] = "AG (sem PP) produziu uma solução com duplicatas."
                        results['final_board_state'] = np.copy(final_board_ag_no_pp) if final_board_ag_no_pp is not None else np.copy(puzzle_data_for_run)
                else:
                    results['final_status'] = "Erro (AG - Sol. Incompleta)"
                    results['error_message'] = "AG (sem PP) produziu uma solução com células vazias (0)."
                    results['final_board_state'] = np.copy(final_board_ag_no_pp) if final_board_ag_no_pp is not None else np.copy(puzzle_data_for_run)
            elif gen_val == -1: results['final_status'] = "Entrada Inválida (AG)"
            elif gen_val == -2:
                results['final_status'] = "Não Resolvido (AG)"
                results['ag_generations_taken'] = "Limite de Gerações Atingido"
                if solution_candidate and hasattr(solution_candidate, 'values'):
                    results['final_board_state'] = np.copy(solution_candidate.values)

    except Exception as e:
        results['final_status'] = "Erro na Execução"
        results['error_message'] = str(e).replace('\n', ' ').replace('\r', '')
        results['boxplot_data'] = results.get('boxplot_data', [])


    results['time_pp_s'] = f"{time_pp_val:.3f}"
    results['time_ag_s'] = f"{time_ag_val:.3f}"
    results['time_total_s'] = f"{(time.time() - overall_start_time):.3f}"

    return results

def batch_test_sudoku(folder_path, output_file_path="sudoku_test_results.xlsx"):
    if not os.path.isdir(folder_path):
        print(f"Erro: Pasta '{folder_path}' não encontrada.")
        return

    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    if not txt_files:
        print(f"Nenhum arquivo .txt encontrado em '{folder_path}'.")
        return

    creation_timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"Encontrados {len(txt_files)} arquivos .txt em '{folder_path}'. Processando...\n")

    all_run_data_for_output = []
    column_headers_main_report = [
        "Arquivo", "Celulas_Vazias_Iniciais",
        "GA_Tam_Populacao", "GA_Max_Geracoes", "GA_Perc_Elite", "GA_Taxa_Mutacao_Inicial", "GA_Limite_Estagnacao_Reiniciar",
        "Tipo_Execucao", "Numeros_Preenchidos_PP", "Resolvido_Apenas_PP",
        "AG_Geracoes", "AG_Taxa_Mutacao_Final", "AG_Sigma_Final", "AG_PHI_Taxa_Sucesso_Final",
        "AG_Reinicios_Populacao",
        "AG_Total_Individuos_Gerados", "AG_Posicao_Solucao",
        "Tempo_PP_s", "Tempo_AG_s", "Tempo_Total_s", "Status_Final",
        "Celulas_Vazias_Finais", "Mensagem_Erro"
    ]
    actual_elite_count = int(POPULATION_SIZE * ELITE_PERCENTAGE)
    if actual_elite_count % 2 != 0 and POPULATION_SIZE - actual_elite_count > 0:
        actual_elite_count = max(0, actual_elite_count -1)

    for i, txt_file in enumerate(sorted(txt_files)):
        file_path = os.path.join(folder_path, txt_file)
        puzzle_data = load_puzzle_from_file(file_path)

        ga_limite_estagnacao_valor = "N/A (Desativado)"

        if puzzle_data is None:
            error_row = {header: 'N/A' for header in column_headers_main_report}
            error_row["Arquivo"] = txt_file
            error_row["Status_Final"] = "Erro ao Carregar"
            error_row["GA_Limite_Estagnacao_Reiniciar"] = ga_limite_estagnacao_valor
            error_row["AG_Reinicios_Populacao"] = 0
            error_row["boxplot_data"] = []
            error_row["fitness_history"] = []
            all_run_data_for_output.append(error_row)
            print(f"Erro ao carregar {txt_file}. Pulando.")
            continue

        initial_empty_cells = np.count_nonzero(puzzle_data == 0)
        print(f"--- Processando {txt_file} ({i+1}/{len(txt_files)}) ---")

        print(f"  {txt_file} - COM Pré-processamento...")
        results_pp = run_solver_for_puzzle(np.copy(puzzle_data), use_preprocessing=True)
        if results_pp['solved_by_pp_only']:
             print(f"    >> {txt_file} (Com PP): Resolvido APENAS pelo pré-processamento!")

        print(f"    Números Preenchidos (PP): {results_pp['numbers_filled_by_pp']}")
        print(f"    Status: {results_pp['final_status']}, Número da Geração: {results_pp['ag_generations_taken']}, Quantidade de Gerações: {results_pp['ag_generations_taken'] + 1 if isinstance(results_pp['ag_generations_taken'], int) else results_no_pp['ag_generations_taken']}, Indivíduos AG: {results_pp['ag_total_individuals_generated']}")
        print(f"    Tempos: PP: {results_pp['time_pp_s']}s, AG: {results_pp['time_ag_s']}s, Total: {results_pp['time_total_s']}s")


        row_pp_data = {
            "Arquivo": txt_file, "Celulas_Vazias_Iniciais": initial_empty_cells,
            "GA_Tam_Populacao": POPULATION_SIZE, "GA_Max_Geracoes": MAX_GENERATIONS,
            "GA_Perc_Elite": f"{ELITE_PERCENTAGE*100:.1f}% ({actual_elite_count})",
            "GA_Taxa_Mutacao_Inicial": INITIAL_MUTATION_RATE,
            "GA_Limite_Estagnacao_Reiniciar": ga_limite_estagnacao_valor,
            "Tipo_Execucao": "Com_PP",
            "Numeros_Preenchidos_PP": results_pp['numbers_filled_by_pp'],
            "Resolvido_Apenas_PP": results_pp['solved_by_pp_only'],
            "AG_Geracoes": results_pp['ag_generations_taken'],
            "AG_Taxa_Mutacao_Final": results_pp['ag_final_mutation_rate'],
            "AG_Sigma_Final": results_pp['ag_final_sigma'],
            "AG_PHI_Taxa_Sucesso_Final": results_pp['ag_final_phi_success_rate'],
            "AG_Total_Individuos_Gerados": results_pp['ag_total_individuals_generated'],
            "AG_Posicao_Solucao": results_pp['ag_solution_position'],
            "Tempo_PP_s": results_pp['time_pp_s'], "Tempo_AG_s": results_pp['time_ag_s'],
            "Tempo_Total_s": results_pp['time_total_s'], "Status_Final": results_pp['final_status'],
            "Celulas_Vazias_Finais": np.count_nonzero(results_pp['final_board_state'] == 0),
            "Mensagem_Erro": results_pp['error_message'],
            "fitness_history": results_pp['fitness_history'],
            "boxplot_data": results_pp['boxplot_data']
        }
        all_run_data_for_output.append(row_pp_data)

        print(f"  {txt_file} - SEM Pré-processamento...")
        results_no_pp = run_solver_for_puzzle(np.copy(puzzle_data), use_preprocessing=False)
        print(f"    Status: {results_no_pp['final_status']}, Número da Geração: {results_no_pp['ag_generations_taken']}, Quantidade de Gerações: {results_no_pp['ag_generations_taken'] + 1 if isinstance(results_no_pp['ag_generations_taken'], int) else results_no_pp['ag_generations_taken']}, Indivíduos AG: {results_no_pp['ag_total_individuals_generated']}")
        print(f"    Tempos: PP: {results_no_pp['time_pp_s']}s, AG: {results_no_pp['time_ag_s']}s, Total: {results_no_pp['time_total_s']}s\n")

        row_no_pp_data = {
            "Arquivo": txt_file, "Celulas_Vazias_Iniciais": initial_empty_cells,
            "GA_Tam_Populacao": POPULATION_SIZE, "GA_Max_Geracoes": MAX_GENERATIONS,
            "GA_Perc_Elite": f"{ELITE_PERCENTAGE*100:.1f}% ({actual_elite_count})",
            "GA_Taxa_Mutacao_Inicial": INITIAL_MUTATION_RATE,
            "GA_Limite_Estagnacao_Reiniciar": ga_limite_estagnacao_valor,
            "Tipo_Execucao": "Sem_PP",
            "Numeros_Preenchidos_PP": 0, "Resolvido_Apenas_PP": False,
            "AG_Geracoes": results_no_pp['ag_generations_taken'],
            "AG_Taxa_Mutacao_Final": results_no_pp['ag_final_mutation_rate'],
            "AG_Sigma_Final": results_no_pp['ag_final_sigma'],
            "AG_PHI_Taxa_Sucesso_Final": results_no_pp['ag_final_phi_success_rate'],
            "AG_Reinicios_Populacao": results_no_pp.get('ag_reseed_count', 0),
            "AG_Total_Individuos_Gerados": results_no_pp['ag_total_individuals_generated'],
            "AG_Posicao_Solucao": results_no_pp['ag_solution_position'],
            "Tempo_PP_s": results_no_pp['time_pp_s'], "Tempo_AG_s": results_no_pp['time_ag_s'],
            "Tempo_Total_s": results_no_pp['time_total_s'], "Status_Final": results_no_pp['final_status'],
            "Celulas_Vazias_Finais": np.count_nonzero(results_no_pp['final_board_state'] == 0),
            "Mensagem_Erro": results_no_pp['error_message'],
            "fitness_history": results_no_pp['fitness_history'],
            "boxplot_data": results_no_pp['boxplot_data']
        }
        all_run_data_for_output.append(row_no_pp_data)

    try:
        df = pd.DataFrame(all_run_data_for_output)
        for col in column_headers_main_report:
            if col not in df.columns:
                df[col] = 'N/A'
        df_main_report = df[column_headers_main_report]

        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            info_df = pd.DataFrame([{"Data e Hora da Geração do Relatório": creation_timestamp}])
            info_df.to_excel(writer, sheet_name='Resultados_Testes', index=False, startrow=0, header=True)
            df_main_report.to_excel(writer, sheet_name='Resultados_Testes', index=False, startrow=2, header=True)

        print(f"\nResultados dos testes salvos em: {output_file_path}")

        output_folder_summary_fitness = output_file_path.replace(".xlsx", "_fitness_summary_reports")
        fitness_reporter.generate_fitness_reports(all_run_data_for_output, output_folder_summary_fitness)

        output_folder_boxplot_data = output_file_path.replace(".xlsx", "_boxplot_data_reports")
        fitness_reporter.generate_boxplot_data_reports(all_run_data_for_output, output_folder_boxplot_data)

    except ImportError:
        print("\nERRO: A biblioteca pandas e/ou openpyxl não estão instaladas.")
        print("Por favor, instale-as para gerar arquivos .xlsx, por exemplo: pip install pandas openpyxl")
    except Exception as e:
        print(f"\nUm erro inesperado ocorreu ao tentar salvar o arquivo XLSX ou gerar relatórios: {e}")