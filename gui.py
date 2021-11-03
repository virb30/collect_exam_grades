import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.constants import BOTH, BOTTOM, DISABLED, END, LEFT, NORMAL, RIGHT

from exam_grades import ENEMScrap

MAX_RETRIES = 3
DEFAULT_SEPARATOR = ';'


class frm_main:
    retries = 1
    file_path = ''

    def __init__(self, parent):
        self.total = 0
        self.parent = parent
        self.parent.title('Notas do ENEM')
        self.parent.geometry('400x400')

        row_login = tk.Frame(self.parent)
        row_login.pack(fill=BOTH, expand=1)

        tk.Label(row_login, text='Usuário').pack(side=LEFT)
        self.input_username = tk.Entry(row_login)
        self.input_username.pack(side=LEFT)

        tk.Label(row_login, text='Senha').pack(side=LEFT)
        self.input_password = tk.Entry(row_login,  show="*")
        self.input_password.pack(side=LEFT)

        row1 = tk.Frame(self.parent)
        row1.pack(fill=BOTH, expand=1)

        row2 = tk.Frame(self.parent)
        row2.pack(fill=BOTH, expand=1)

        self.row3 = tk.Frame(self.parent)
        self.row3.pack(fill=BOTH, expand=1)

        row4 = tk.Frame(self.parent)
        row4.pack(side=BOTTOM, fill=BOTH, expand=1)

        sepLabel = tk.Label(row1, text='Separador')
        sepLabel.pack(side=LEFT)

        self.separator_input = tk.Entry(row1)
        self.separator_input.pack(side=LEFT)
        self.separator_input.insert(END, DEFAULT_SEPARATOR)

        tk.Label(row2, text='Inscritos').pack(side=LEFT)

        tk.Button(row2, text='Selecione um arquivo',
                  command=self.select_file).pack(side=LEFT)
        self.lbl_input_file = tk.Label(
            row2, text=self.get_filepath())
        self.lbl_input_file.pack(side=RIGHT)

        tk.Label(self.row3, text='Saída').pack(side=LEFT)

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

    def open_results_dir(self):
        path = self.results_dir
        os.system(f'start {path}')

    def run(self):
        username = self.input_username.get()
        password = self.input_password.get()
        separator = self.separator_input.get()

        if not self.file_path:
            messagebox.showerror(
                'Input Error', message='Selecione o arquivo de inscritos'
            )

        scrap = ENEMScrap(username, password)
        try:
            self.timer()
            self.run_button.config(state=DISABLED)
            self.run_button.update()
            args = {
                'input_file': self.file_path,
                'output_file': 'cpf.txt',
                'sep': separator
            }

            self.results_dir = scrap.run(**args)

            # request_file = scrap.generate_request_file(**args)
            # response_files = scrap.get_response_files(request_file)
            # scrap.save_final_results(response_files)

            # self.results_dir = scrap.get_results_dir()

            tk.Button(self.row3, text='Resultados',
                      command=self.open_results_dir).pack(side=LEFT)

            self.retries = 1
        except Exception as err:
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


if __name__ == '__main__':
    root = tk.Tk()
    main_frm = frm_main(root)
    root.mainloop()
