import os
import re
import time
import glob
from datetime import date, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

INPUT_FILE_LAYOUT = {
    'cpf': 2,
    'subscription': 0,
    'year': 3
}

EXAM_RESULTS_LAYOUT = {
    'cpf': 1,
    'essay': 7,
    'grades': slice(3, 7)
}

BASE_DIR = Path(__file__).resolve().parent

DOWNLOADS_DIR = BASE_DIR / 'downloads'
DATE_DIR = DOWNLOADS_DIR / date.today().strftime("%Y-%m-%d")
RESULTS_DIR = DATE_DIR / 'results'

LOGS_DIR = BASE_DIR / 'logs'

ERRORS_FILE = LOGS_DIR / 'errors.log'
SUCCESS_FILE = LOGS_DIR / 'processed_data.log'

WEBDRIVER = BASE_DIR / 'drivers' / 'chromedriver.exe'

url = "http://sistemasenem.inep.gov.br/EnemSolicitacao/"


class ENEMScrap:
    username = ''
    password = ''
    processed_candidates = []
    candidates_dict = {}

    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

    def run(self, input_file, output_file, sep=';'):
        self.initialize_directories()
        self.generate_request_file(input_file, output_file, sep)
        self.get_response_files()
        self.save_final_results()
        return self.get_results_dir()

    def get_processed_candidates(self):
        try:
            self.processed_candidates = ENEMScrap.read_file_lines(SUCCESS_FILE)
        except:
            SUCCESS_FILE.touch()
        return self.processed_candidates

    @staticmethod
    def create_directory(directory):
        if not directory.exists():
            directory.mkdir()

    def initialize_directories(self):
        directories = [DOWNLOADS_DIR, DATE_DIR, RESULTS_DIR, LOGS_DIR]
        for directory in directories:
            ENEMScrap.create_directory(directory)

    @staticmethod
    def read_file_lines(file):
        lines = []
        assert file.exists()
        with file.open(mode='r', encoding='utf8') as f:
            lines = f.read().splitlines()
        return lines

    def write_lines_to_file(self, file, data, mode='a', end='\n'):
        with file.open(mode=mode, encoding='utf8') as output_file:
            output_file.write(f'{data}{end}')

    def already_processed(self, cpf):
        return cpf in self.processed_candidates

    def generate_request_file(self, input_file, output_file, sep=';'):
        file = Path(input_file)
        self.request_file = Path(output_file)
        lines = ENEMScrap.read_file_lines(file)
        output = []
        for line in lines:
            line_data = line.split(sep)
            cpf = re.sub(r'\D', '', line_data[INPUT_FILE_LAYOUT['cpf']])
            self.candidates_dict[cpf] = {
                'subscription': line_data[INPUT_FILE_LAYOUT['subscription']],
                'year': line_data[INPUT_FILE_LAYOUT['year']]
            }
            if not self.already_processed(cpf):
                output.append(cpf)
        output_data = '\n'.join(output)
        self.write_lines_to_file(
            file=self.request_file, data=output_data, mode='w')
        return self.request_file

    def has_data(self, file):
        return file.stat().st_size > 0

    def get_webdriver(self):
        executable_path = WEBDRIVER
        chrome_config = {
            "download.default_directory": str(DATE_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 2,
        }
        options = Options()
        options.headless = True
        # options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_experimental_option("prefs", chrome_config)
        return webdriver.Chrome(executable_path=executable_path, options=options)

    def login(self, webdriver):

        if not self.username or not self.password:
            raise Exception('Informe usuário e senha')

        webdriver.get(url)
        webdriver.implicitly_wait(10)
        webdriver.switch_to.frame(webdriver.find_element_by_tag_name('iframe'))
        webdriver.find_element_by_id('username').send_keys(self.username)
        webdriver.find_element_by_id('password').send_keys(self.password)
        webdriver.find_element_by_xpath("//input[@type='image']").click()
        webdriver.implicitly_wait(5)

    def send_request_file(self, driver, submenu_id, input_file):
        driver.find_element_by_id(submenu_id).click()
        year = driver.find_element_by_xpath(
            f"//div[@id='{submenu_id}']/table/tbody/tr/td[contains(@class, 'rich-pmenu-group-self-label')]").text
        driver.find_element_by_xpath(
            f"//div[@id='{submenu_id}']/div/table/tbody/tr/td[text()='Por arquivo (Cpf)']").click()
        driver.find_element_by_xpath(
            "//form[@id='formForm']/div[@id='uploadid']//input[@type='file']").send_keys(os.path.realpath(input_file))
        driver.implicitly_wait(1)
        driver.find_element_by_id('uploadid:upload1').click()
        time.sleep(5)
        return year

    def last_requested_today(self, driver, time):
        last_request = driver.find_element_by_xpath(
            "//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td[@id='listaSolicitacaoAtendidas:0:j_id165']/div")
        last_request_date = datetime.strptime(
            last_request.text, '%d/%m/%Y %H:%M:%S')
        return last_request_date.time() >= time.time()

    def download_response_file(self, driver):
        file_name = ''
        two_minutes = timedelta(minutes=3)
        execution_time = datetime.now() - two_minutes
        driver.find_element_by_xpath("//div[@id='menugroup_5']/div").click()
        driver.implicitly_wait(10)
        if self.last_requested_today(driver, execution_time):
            download_link = driver.find_element_by_xpath(
                "//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td/div/a")
            file_name = download_link.get_attribute('href').split('/')[-1]
            if not self.file_exists(file_name):
                download_link.click()
            time.sleep(5)
        return file_name

    def get_results_by_year(self):
        webdriver = self.get_webdriver()
        self.login(webdriver)
        self.response_files_by_year = {}
        submenus = [submenu.get_attribute('id') for submenu in webdriver.find_elements_by_xpath(
            "//div[@id='menugroup_4']/div[not(@id='menugroup_4_1')]")]
        for submenu_id in submenus:
            year = self.send_request_file(
                webdriver, submenu_id, self.request_file)
            time.sleep(10)
            file = self.download_response_file(webdriver)
            if file:
                self.response_files_by_year[year] = file
            webdriver.implicitly_wait(2)
        time.sleep(3)
        webdriver.quit()
        return self.response_files_by_year

    def get_response_files(self):
        if self.has_data(self.request_file):
            return self.get_results_by_year()

    def get_exam_results_files(self):
        directory = str(DATE_DIR)
        return glob.glob1(directory, "*.txt")

    def file_exists(self, search_file):
        file_list = self.get_exam_results_files()
        if search_file in file_list:
            return True
        return False

    @staticmethod
    def calculate_grade_average(grades):
        average = sum([float(grade) for grade in grades]) / 4
        return round(average * 30 / 1000)

    @staticmethod
    def calculate_essay_grade(grade):
        return round(float(grade) / 100)

    def candidate_year(self, cpf, year):
        candidate = self.candidates_dict.get(cpf)
        return candidate.get('year') == year

    def get_line(self, data, separator=';'):
        return data.split(separator)

    def grade_exists(self, haystack, needle):
        return needle in haystack

    def get_cpf(self, data):
        return data[EXAM_RESULTS_LAYOUT['cpf']]

    def get_essay_grade(self, data):
        return data[EXAM_RESULTS_LAYOUT['essay']]

    def get_grades(self, data):
        return data[EXAM_RESULTS_LAYOUT['grades']]

    def save_final_results(self):
        files = self.response_files_by_year
        result_file_date = date.today().strftime('%d%m%Y')
        grades_file = RESULTS_DIR / f'EXP_{result_file_date}_PON.txt'
        essay_file = RESULTS_DIR / f'EXP_{result_file_date}_RED.txt'

        grades_output = []
        essay_output = []
        processed_registers_output = []
        errors_output = []

        for _, filename in files.items():
            file = DATE_DIR / filename
            exam_results = ENEMScrap.read_file_lines(file)
            for result in exam_results:
                line_data = self.get_line(result)
                cpf = self.get_cpf(line_data)
                subscription = self.candidates_dict.get(cpf)['subscription']

                raw_essay_grade = self.get_essay_grade(line_data)
                essay_grade = ENEMScrap.calculate_essay_grade(raw_essay_grade)

                raw_grades = self.get_grades(line_data)
                grades_average = ENEMScrap.calculate_grade_average(raw_grades)

                if essay_grade > 0:
                    if not self.grade_exists(processed_registers_output, cpf):
                        essay_output.append(
                            f'{"X" * 40}{subscription.zfill(6)}{"X" * 14}{essay_grade}')
                        grades_output.append(
                            f'{"X" * 40}{subscription.zfill(6)}{"X" * 14}{grades_average}')
                        processed_registers_output.append(cpf)
                else:
                    if cpf not in errors_output:
                        errors_output.append(cpf)

        self.write_lines_to_file(
            file=ERRORS_FILE, data='\n'.join(errors_output), mode='a')
        self.write_lines_to_file(
            file=grades_file, data='\n'.join(grades_output), mode='a')
        self.write_lines_to_file(
            file=essay_file, data='\n'.join(essay_output), mode='a')
        self.write_lines_to_file(file=SUCCESS_FILE, data='\n'.join(
            processed_registers_output), mode='a')

    def get_results_dir(self):
        return RESULTS_DIR
