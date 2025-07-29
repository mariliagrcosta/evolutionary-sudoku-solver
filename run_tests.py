import os
import datetime
import time
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_solver_performance import batch_test_sudoku

if __name__ == "__main__":
    default_puzzle_folder = os.path.join("examples", "mantere")
    user_input_path = input(f"Digite o caminho para a pasta contendo os arquivos Sudoku .txt (padrão: {default_puzzle_folder}): ")
    puzzle_folder_path = user_input_path if user_input_path else default_puzzle_folder

    total_runs = 1

    results_folder = "results"
    os.makedirs(results_folder, exist_ok=True)

    for i in range(total_runs):

        current_run = i + 1
        
        print(f"\n{'='*20}\nINICIANDO EXECUÇÃO {current_run} DE {total_runs}\n{'='*20}\n")
        
        timestamp_for_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        output_file_name = f"evolutionary-sudoku-solver-{timestamp_for_filename}_run_{current_run}_sudoku_results.xlsx"
        full_output_path = os.path.join(results_folder, output_file_name)

        batch_test_sudoku(puzzle_folder_path, output_file_name)
        
        if i < total_runs - 1:
            print(f"\n--- Execução {current_run} concluída. Aguardando 2 segundos antes da próxima. ---\n")
            print(f"--- Iniciando a próxima execução em instantes. ---\n")
            time.sleep(2)

    print(f"\nTodas as {total_runs} execuções foram concluídas.")