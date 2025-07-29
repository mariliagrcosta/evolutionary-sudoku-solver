from gui import frame as sg
from tkinter import *
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

puzzle_name = input("Digite o nome do puzzle: ")
puzzle_path = f"puzzles/mantere_collection/{puzzle_name}.txt"

try:
    tk = Tk()
    sudoku_gui = sg.SudokuGUI(tk, puzzle_path)
    sudoku_gui.mainloop()

except FileNotFoundError:
    print(f"Erro: O arquivo '{puzzle_path}' não foi encontrado.")
    sys.exit(1)

except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
    sys.exit(1)