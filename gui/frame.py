import random
import time
import numpy as np
from math import sqrt
from tkinter import *
from tkinter.ttk import *
import threading
import queue
import os

from core import solver as ga
from core import pre_processing as pp


random.seed(time.time())

class SudokuGUI(Frame):

    def __init__(self, master, file):

        Frame.__init__(self, master)
        if master:
            master.title("Sudoku")

        self.original_sudoku_problem = np.zeros((9,9)).astype(int)
        self.sudoku_problem = np.zeros((9,9)).astype(int)
        self.locked = []
        self.puzzle = []
        self.sudoku_pre_processed = np.zeros((9,9)).astype(int)
        self.update_queue = queue.Queue()
        self.solver_thread = None

        self.load_sudoku(file)

        self.main_frame = Frame(self)
        self.title_label = Label(self.main_frame, text="SUDOKU SOLVER", font=("Arial", 24, "bold")).pack()
        
        self.spacer1 = Label(self.main_frame,text="", padding=4).pack()
        puzzle_filename = os.path.basename(file)
        puzzle_name, _ = os.path.splitext(puzzle_filename)
        self.puzzle_name_label = Label(self.main_frame, text="PUZZLE", font=("Arial", 12, "underline")).pack()
        self.puzzle_name_label = Label(self.main_frame, text=f"{puzzle_name}", font=("Arial", 10)).pack()

        self.spacer1 = Label(self.main_frame,text="", padding=4).pack()
        
        self.label_frame = Frame(self.main_frame)

        fixed_grid_width = 256
        fixed_grid_spacing = 20

        frame_desafio = Frame(self.label_frame, width=fixed_grid_width, height=20)
        frame_desafio.pack(side=LEFT, padx=(0, fixed_grid_spacing // 2), fill='x', expand=True)
        frame_desafio.pack_propagate(False)
        Label(frame_desafio, text="DESAFIO", font=("Arial", 10)).pack(expand=True)

        frame_preprocessamento = Frame(self.label_frame, width=fixed_grid_width, height=20)
        frame_preprocessamento.pack(side=LEFT, padx=(fixed_grid_spacing // 2, fixed_grid_spacing // 2), fill='x', expand=True)
        frame_preprocessamento.pack_propagate(False)
        Label(frame_preprocessamento, text="PRÉ-PROCESSAMENTO", font=("Arial", 10)).pack(expand=True)

        frame_melhor_individuo = Frame(self.label_frame, width=fixed_grid_width, height=20)
        frame_melhor_individuo.pack(side=LEFT, padx=(fixed_grid_spacing // 2, 0), fill='x', expand=True)
        frame_melhor_individuo.pack_propagate(False)
        Label(frame_melhor_individuo, text="MELHOR INDIVÍDUO", font=("Arial", 10)).pack(expand=True)

        self.label_frame.pack()

        self.make_grid()
        self.show_puzzle()
        
        self.spacer2 = Label(self.main_frame,text="", padding=4).pack()
        
        self.generation_label = Label(self.main_frame, text="Geração: N/A", font=("Arial", 10))
        self.generation_label.pack()
        self.individuals_label = Label(self.main_frame, text="Indivíduos Gerados: N/A", font=("Arial", 10))
        self.individuals_label.pack()
        self.best_fitness_label = Label(self.main_frame, text="Melhor Aptidão: N/A", font=("Arial", 10))
        self.best_fitness_label.pack()
        self.elapsed_time_label = Label(self.main_frame, text="Tempo Decorrido: 0.00s", font=("Arial", 10))
        self.elapsed_time_label.pack()

        self.spacer_before_buttons = Label(self.main_frame, text="", padding=8).pack()

        self.button_solve_w_pp = Button(self.main_frame, text='RESOLVER COM PRÉ-PROCESSAMENTO', width=40, command=self.start_solver_w_pp)
        self.button_solve_w_pp.pack()

        self.button_solve_wo_pp = Button(self.main_frame, text='RESOLVER SEM PRÉ-PROCESSAMENTO', width=40, command=self.start_solver_wo_pp)
        self.button_solve_wo_pp.pack()

        self.spacer3 = Label(self.main_frame,text="", padding=4).pack()

        self.status_label = Label(self.main_frame, text="", relief="solid", justify=LEFT)
        self.status_label.pack()

        self.main_frame.pack()
        self.pack()

        self.after(100, self.check_queue_for_updates)

    def load_sudoku (self, file):
        with open(file, "r") as input_file:
                file_content = input_file.read()
                self.puzzle = file_content.replace(' ', '').replace('-', '0').replace('\n', '')

    def show_puzzle(self):
        self.original_sudoku_problem = np.array(list(self.puzzle)).reshape((9,9)).astype(int)
        self.sudoku_problem = np.copy(self.original_sudoku_problem)
        self.update_canvas_1()

    def pre_processing(self):
        pp_controller = pp.Controller()
        pp_controller.load(np.copy(self.original_sudoku_problem)) 
        self.sudoku_pre_processed, _ = pp_controller.controller()
        self.update_canvas_2()


    def _update_ga_progress_callback(self, generation_num, best_candidate, total_individuals, best_fitness, start_time):
        self.update_queue.put({
            'type': 'ga_progress',
            'generation_num': generation_num,
            'best_candidate_values': best_candidate.values.copy() if best_candidate else np.zeros((9,9)),
            'total_individuals': total_individuals,
            'best_fitness': best_fitness
        })
        elapsed = time.time() - start_time
        self.update_queue.put({'type': 'time_update', 'elapsed_time': elapsed})
        
    def check_queue_for_updates(self):
        try:
            while True:
                update_data = self.update_queue.get_nowait()
                
                update_type = update_data.get('type')

                if update_type == 'status_message':
                    self.status_label.config(text=update_data['status_message'])
                elif update_type == 'enable_buttons':
                    self.button_solve_w_pp.config(state=NORMAL)
                    self.button_solve_wo_pp.config(state=NORMAL)
                elif update_type == 'final_board':
                    self.update_canvas_3(update_data['final_board'])
                elif update_type == 'ga_progress':
                    self.generation_label.config(text=f"Geração: {update_data['generation_num']}")
                    self.individuals_label.config(text=f"Indivíduos Gerados: {update_data['total_individuals']}")
                    self.best_fitness_label.config(text=f"Melhor Aptidão: {update_data['best_fitness']:.6f}")
                    self.update_canvas_3(update_data['best_candidate_values'])
                elif update_type == 'time_update':
                    self.elapsed_time_label.config(text=f"Tempo Decorrido: {update_data['elapsed_time']:.2f}s")

        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.check_queue_for_updates)


    def start_solver_w_pp(self):
        self.sudoku_problem = np.copy(self.original_sudoku_problem)
        self.update_canvas_1()
        self.pre_processing()
        self.start_solver_thread(use_preprocessing_result=True)
        
    def start_solver_wo_pp(self):
        self.sudoku_problem = np.copy(self.original_sudoku_problem)
        self.update_canvas_1()
        self.update_canvas_2(np.zeros((9,9)))
        self.start_solver_thread(use_preprocessing_result=False)

    def start_solver_thread(self, use_preprocessing_result):
        self.button_solve_w_pp.config(state=DISABLED)
        self.button_solve_wo_pp.config(state=DISABLED)

        self.status_label.config(text="")
        self.generation_label.config(text="Geração: N/A")
        self.individuals_label.config(text="Indivíduos Gerados: N/A")
        self.best_fitness_label.config(text="Melhor Aptidão: N/A")
        self.elapsed_time_label.config(text="Tempo Decorrido: 0.00s")
        self.update_canvas_3(np.zeros((9,9)))

        if self.solver_thread and self.solver_thread.is_alive():
            pass

        self.solver_thread = threading.Thread(target=self._run_solver, args=(use_preprocessing_result,))
        self.solver_thread.daemon = True
        self.solver_thread.start()

    def _run_solver(self, use_preprocessing_result):
        ga_sudoku = ga.Sudoku()

        if use_preprocessing_result:
            board_to_solve = np.copy(self.sudoku_pre_processed)
        else:
            board_to_solve = np.copy(self.original_sudoku_problem)

        ga_sudoku.load(board_to_solve)
        start_time = time.time()
        
        solve_output = ga_sudoku.solve(progress_callback=lambda gen, best_cand, total_ind, best_fit: 
                                      self._update_ga_progress_callback(gen, best_cand, total_ind, best_fit, start_time))
        
        final_time_elapsed = time.time()-start_time

        generation = solve_output['generation']
        solution_candidate = solve_output['solution_candidate']
        
        str_print = ""
        if generation == -1:
            str_print = "ENTRADA INVÁLIDA"
        elif generation == -2:
            str_print = "SOLUÇÃO NÃO ENCONTRADA - LIMITE DE GERAÇÕES ATINGIDO"
            if solution_candidate and hasattr(solution_candidate, 'values'):
                self.update_queue.put({'type': 'final_board', 'final_board': solution_candidate.values.copy()})
        else:
            if solution_candidate and hasattr(solution_candidate, 'values'):
                self.sudoku_final_solution = solution_candidate.values
                self.update_queue.put({'type': 'final_board', 'final_board': self.sudoku_final_solution.copy()})
                str_print = "SOLUÇÃO ENCONTRADA!"
            else:
                str_print = "Erro: Solução encontrada, mas dados ausentes."
        
        self.update_queue.put({'type': 'status_message', 'status_message': str_print})
        self.update_queue.put({'type': 'enable_buttons', 'enable_buttons': True})


    def make_grid(self):
            w, h = 256, 256
            grid_spacing = 20

            total_width = (3 * w) + (2 * grid_spacing)
            self.canvas = Canvas(self.main_frame, bg="white", width=total_width, height=h)
            self.canvas.pack()

            self.rects = [[None for x in range(3 * 9)] for y in range(9)]
            self.handles = [[None for x in range(3 * 9)] for y in range(9)]
            
            rsize = w / 9
            
            line_thickness_thin = 1
            line_thickness_thick = 3

            offset_thick = line_thickness_thick / 2.0

            for y_grid in range(9):
                for x_grid_section in range(3):
                    for x_cell_in_grid in range(9):
                        x_total = x_grid_section * 9 + x_cell_in_grid
                        y_total = y_grid

                        current_section_x_offset = (x_grid_section * w) + (x_grid_section * grid_spacing)

                        cell_x_start = current_section_x_offset + x_cell_in_grid * rsize
                        cell_y_start = y_grid * rsize

                        r = self.canvas.create_rectangle(cell_x_start, cell_y_start,
                                                        cell_x_start + rsize, cell_y_start + rsize,
                                                        width=line_thickness_thin)
                        
                        t = self.canvas.create_text(cell_x_start + rsize / 2, cell_y_start + rsize / 2,
                                            font=("Arial", 14, "bold"))
                        
                        self.handles[y_total][x_total] = (r, t)

            for x_grid_section in range(3):
                current_section_x_offset = (x_grid_section * w) + (x_grid_section * grid_spacing)
                

                self.canvas.create_line(current_section_x_offset - offset_thick, offset_thick,
                                        current_section_x_offset + w + offset_thick, offset_thick,
                                        width=line_thickness_thick, fill="black")
                self.canvas.create_line(current_section_x_offset - offset_thick, h - offset_thick,
                                        current_section_x_offset + w + offset_thick, h - offset_thick,
                                        width=line_thickness_thick, fill="black")
                self.canvas.create_line(current_section_x_offset + offset_thick, offset_thick,
                                        current_section_x_offset + offset_thick, h - offset_thick,
                                        width=line_thickness_thick, fill="black")
                self.canvas.create_line(current_section_x_offset + w - offset_thick, offset_thick,
                                        current_section_x_offset + w - offset_thick, h - offset_thick,
                                        width=line_thickness_thick, fill="black")

                for i in range(1, 3):
                    y_pos = i * (h / 3)
                    self.canvas.create_line(current_section_x_offset - offset_thick, y_pos,
                                            current_section_x_offset + w + offset_thick, y_pos,
                                            width=line_thickness_thick, fill="black")

                for j in range(1, 3):
                    x_pos = current_section_x_offset + j * (w / 3)
                    self.canvas.create_line(x_pos, 0 - offset_thick,
                                            x_pos, h + offset_thick,
                                            width=line_thickness_thick, fill="black")

            self.update_canvas_1()

    def update_canvas_1(self):
        g = self.original_sudoku_problem
        for y in range(9):
            for x in range(9):
                if g[y][x] != 0:
                    self.canvas.itemconfig(self.handles[y][x][1],
                                           text=str(g[y][x]), fill="black")
                else:
                    self.canvas.itemconfig(self.handles[y][x][1],
                                           text='')
                    
    def update_canvas_2(self, board=None):
            if board is None:
                g = self.sudoku_pre_processed
            else:
                g = board

            for y in range(9):
                for x in range(9):
                    if g[y][x] != 0:
                        if self.original_sudoku_problem[y][x] != 0:
                            fill_color = "black"
                        else:
                            fill_color = "red"
                        
                        self.canvas.itemconfig(self.handles[y][x+9][1],
                                            text=str(g[y][x]), fill=fill_color)
                    else:
                        self.canvas.itemconfig(self.handles[y][x+9][1],
                                            text='')


    def update_canvas_3(self, board):
        for y in range(9):
            for x in range(9):
                if board[y][x] != 0:
                    if self.original_sudoku_problem[y][x] != 0:
                        fill_color = "black" 
                    elif self.sudoku_pre_processed[y][x] != 0 and self.original_sudoku_problem[y][x] == 0: 
                        fill_color = "blue"
                    else:
                        fill_color = "red"

                    self.canvas.itemconfig(self.handles[y][x+18][1],
                                           text=str(board[y][x]), fill=fill_color)
                else:
                    self.canvas.itemconfig(self.handles[y][x+18][1],
                                           text='')