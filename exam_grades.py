# -*- encoding: utf-8 -*-

import argparse, sys, os, re, time, glob
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

INPUT_FILE_LAYOUT = {
    'cpf': 2,
    'subscription': 0
}

EXAM_RESULTS_LAYOUT = {
    'cpf': 1,
    'essay': 7,
    'grades': slice(3,7)
}

USERNAME = os.environ['WS_USERNAME']
PASSWORD = os.environ['WS_PASSWORD']

BASE_DIR = './downloads'
DATE_DIR = date.today().strftime("%Y-%m-%d")

LOG_FILE = './processed_data.log'

candidates_dict = {}


def create_directory(directory):
    if(not os.path.exists(directory)):
        os.mkdir(directory)


def init_directories():
    create_directory(BASE_DIR)
    create_directory(f'{BASE_DIR}/{DATE_DIR}')
    create_directory(f'{BASE_DIR}/{DATE_DIR}/results')


def get_result_files():
    directory = os.path.realpath(f'{BASE_DIR}/{DATE_DIR}')
    return glob.glob1(directory, "*.txt")


def file_exists(search_file):
    file_list = get_result_files()
    if search_file in file_list:
        return True
    return False


def get_webdriver():
    executable_path = r'.\\chromedriver\\chromedriver.exe'
    chrome_config = {
        "download.default_directory": os.path.realpath(f'{BASE_DIR}/{DATE_DIR}'),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 2,
    }
    options = Options()
    options.headless = True
    options.add_experimental_option("prefs", chrome_config)    
    return webdriver.Chrome(executable_path=executable_path, options=options)


def open_browser(driver):
    url = "http://sistemasenem.inep.gov.br/EnemSolicitacao/"
    driver.get(url)
    driver.implicitly_wait(5)
    driver.switch_to.frame(driver.find_element_by_tag_name('iframe'))


def login(driver):
    driver.find_element_by_id('username').send_keys(USERNAME)
    driver.find_element_by_id('password').send_keys(PASSWORD)
    driver.find_element_by_xpath("//input[@type='image']").click()
    driver.implicitly_wait(5)


def open_request_form(driver, submenu_id):
    driver.find_element_by_id(submenu_id).click()
    driver.find_element_by_xpath(f"//div[@id='{submenu_id}']/div/table/tbody/tr/td[text()='Por arquivo (Cpf)']").click()


def upload_request_file(driver, input_file):
    driver.find_element_by_xpath("//form[@id='formForm']/div[@id='uploadid']//input[@type='file']").send_keys(os.path.realpath(input_file))
    driver.implicitly_wait(1)
    driver.find_element_by_id('uploadid:upload1').click()
    driver.implicitly_wait(5)


def download_response_file(driver):
    driver.find_element_by_xpath("//div[@id='menugroup_5']/div").click()
    driver.implicitly_wait(1)
    last_request = driver.find_element_by_xpath("//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td[@id='listaSolicitacaoAtendidas:0:j_id160']/div")
    last_request_date = datetime.strptime(last_request.text, '%d/%m/%Y %H:%M:%S')
    last_requested_today = last_request_date.date() >= date.today()
    if(last_requested_today):
        download_link = driver.find_element_by_xpath("//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td/div/a")
        file_name = download_link.get_attribute('href').split('/')[-1]
        if(not file_exists(file_name)):
            download_link.click()
        driver.implicitly_wait(2)


def get_response_files(input_file):
    if(os.path.getsize(input_file) > 0):
        driver = get_webdriver()
        open_browser(driver)
        login(driver)
        submenus = [submenu.get_attribute('id') for submenu in driver.find_elements_by_xpath("//div[@id='menugroup_4']/div[not(@id='menugroup_4_1')]")]
        for submenu_id in submenus:
            open_request_form(driver, submenu_id)
            upload_request_file(driver, input_file)
            download_response_file(driver)
        time.sleep(5)
        driver.quit()


def extract_args():
    parser = argparse.ArgumentParser(
        description='Extract cpf from input file and remove any non digit character')
    parser.add_argument('input_file', metavar='input_file', type=str,
                        help='input file path')
    parser.add_argument('output_file', metavar='output_file', type=str,
                        help='output file path')
    parser.add_argument('--sep',
                        help='Defines separator character of files (default: ;)', default=';')
    return parser.parse_args()


def read_processed_registers(): 
    lines = []
    if(os.path.exists(LOG_FILE)):
        log_file = open(LOG_FILE, mode="r+")
        lines = log_file.read().splitlines()
        log_file.close()
    return lines


def save_processed_registers(data):
    with open(LOG_FILE, mode="a") as log_file:
        log_file.write(f'{data}\n')
        log_file.close()


def generate_request_file():
    global candidates_dict
    args = extract_args()
    input_file = open(args.input_file)
    lines = input_file.readlines()
    processed_candidates = read_processed_registers()
    with open(args.output_file, mode='w') as output_file:
        for line in lines:
            line_data = line.split(args.sep)
            write_data = re.sub(r'\D', '', line_data[INPUT_FILE_LAYOUT['cpf']])
            candidates_dict[write_data] = line_data[INPUT_FILE_LAYOUT['subscription']]
            if(write_data not in processed_candidates):
                output_file.write(f'{write_data}\n')
        output_file.close()
    input_file.close()
    return args.output_file


def calculate_grade_average(grades):
    average = sum([float(grade) for grade in grades]) / 4
    return round(average * 30 / 1000)


def calculate_essay_grade(grade):
    return round(float(grade) / 100)


def save_result_to_file(filepath, result, cpf):
    global candidates_dict
    subscription = candidates_dict.get(cpf)    
    with open(filepath, mode='a') as file:
        file.write(''.join(['X'*40, subscription.zfill(6), 'X'*14, f'{result}\n']))
        file.close()


def calculate_grades():
    export_file_date = date.today().strftime('%d%m%Y')     
    grades_output = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{export_file_date}_PON.txt'
    essay_output = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{export_file_date}_RED.txt'

    result_files = get_result_files()
    for result_file in result_files:
        with open(f'{BASE_DIR}/{DATE_DIR}/{result_file}') as file:
            exam_results = file.readlines()
            for result in exam_results:
                line_data = result.split(';')
                cpf = line_data[EXAM_RESULTS_LAYOUT['cpf']]
                essay_grade = calculate_essay_grade(line_data[EXAM_RESULTS_LAYOUT['essay']])
                grades_average = calculate_grade_average(line_data[EXAM_RESULTS_LAYOUT['grades']])
                if(grades_average > 0 and essay_grade > 0):
                    save_result_to_file(grades_output, grades_average, cpf)
                    save_result_to_file(essay_output, essay_grade, cpf)
                    save_processed_registers(cpf)
            file.close()
        
            
def main():
    try:
        init_directories()
        request_file = generate_request_file()
        get_response_files(request_file)
        calculate_grades()
        print('Script successful executed')
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
