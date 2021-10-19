import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.constants import BOTH, BOTTOM, DISABLED, END, LEFT, NORMAL, RIGHT

from exam_grades import generate_request_file, get_response_files, initialize_directories, save_final_results

MAX_RETRIES = 3
DEFAULT_SEPARATOR = ';'

root = tk.Tk()


class frm_main:
    retries = 1
    file_path = ''
    separator = DEFAULT_SEPARATOR

    def __init__(self, parent):
        self.total = 0
        self.parent = parent
        self.parent.title('Notas do ENEM')
        self.parent.geometry('400x400')

        row1 = tk.Frame(self.parent)
        row1.pack(fill=BOTH, expand=1)

        row2 = tk.Frame(self.parent)
        row2.pack(fill=BOTH, expand=1)

        row3 = tk.Frame(self.parent)
        row3.pack(fill=BOTH, expand=1)

        row4 = tk.Frame(self.parent)
        row4.pack(side=BOTTOM, fill=BOTH, expand=1)

        sepLabel = tk.Label(row1, text='Separador')
        sepLabel.pack(side=LEFT)

        separator_input = tk.Entry(row1, textvariable=self.separator)
        separator_input.pack(side=LEFT)
        separator_input.insert(END, self.separator)

        tk.Label(row2, text='Inscritos').pack(side=LEFT)

        tk.Button(row2, text='Selecione um arquivo',
                  command=self.select_file).pack(side=LEFT)
        self.lbl_input_file = tk.Label(
            row2, text=self.get_filepath())
        self.lbl_input_file.pack(side=RIGHT)

        tk.Label(row3, text='Saída').pack(side=LEFT)

        self.run_button = tk.Button(
            row4, text='Processar', background='green', fg='white', command=self.run)
        self.run_button.pack(fill=BOTH)

        self.lbl_counter = tk.Label(row4, text='')
        self.lbl_counter.pack(fill=BOTH)

    def get_filepath(self):
        return '/'.join(self.file_path.split('/')[-2:]) if self.file_path else 'Nenhum arquivo selecionado'

    def select_file(self):
        self.file_path = filedialog.askopenfilename()
        self.lbl_input_file.configure(text=self.get_filepath())
        self.lbl_input_file.update()

    def timer(self):
        self.start_time = time.time()
        self.lbl_counter.configure(text='Processando...')
        self.lbl_counter.update()

    def run(self):
        if not self.file_path:
            messagebox.showerror(
                'Input Error', message='Selecione o arquivo de inscritos'
            )

        try:
            self.timer()
            self.run_button.config(state=DISABLED)
            self.run_button.update()
            initialize_directories()
            args = {
                'input_file': self.file_path,
                'output_file': 'cpf.txt',
                'sep': self.separator
            }

            request_file = generate_request_file(**args)
            response_files = get_response_files(request_file)
            save_final_results(response_files)

            self.retries = 1
        except:
            self.retries += 1
            if self.retries >= MAX_RETRIES:
                messagebox.showerror(
                    'Error', message='Erro ao processar, tente novamente'
                )
            else:
                self.run()
        finally:
            self.file_path = ''
            self.run_button.configure(state=NORMAL)
            self.run_button.update()
            self.lbl_counter.configure(
                text=f'Execution time: {time.time() - self.start_time}s')
            self.lbl_counter.update


main_frm = frm_main(root)
root.mainloop()
