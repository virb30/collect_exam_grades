# -*- encoding: utf-8 -*-

import argparse, sys, os, re, time, glob
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

BASE_DIR = './downloads'
DATE_DIR = date.today().strftime("%Y-%m-%d")
candidates_dict = {}

def login(driver):
    username=os.environ['USERNAME']
    password=os.environ['WS_PASSWORD']
    driver.find_element_by_id('username').send_keys(username)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_xpath("//input[@type='image']").click()
    driver.implicitly_wait(5)


def get_result_files():
    directory = os.path.realpath(f'{BASE_DIR}/{DATE_DIR}')
    return glob.glob1(directory, "*.txt")


def file_exists(search_file):
    file_list = get_result_files()
    if search_file in file_list:
        return True
    return False


def open_browser(driver):
    url = "http://sistemasenem.inep.gov.br/EnemSolicitacao/"
    driver.get(url)
    driver.implicitly_wait(5)
    driver.switch_to.frame(driver.find_element_by_tag_name('iframe'))


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
    download_link = driver.find_element_by_xpath("//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td/div/a")
    file_name = download_link.get_attribute('href').split('/')[-1]
    if(not file_exists(file_name)):
        download_link.click()
    driver.implicitly_wait(2)


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
    options.headless = False
    options.add_experimental_option("prefs", chrome_config)    
    return webdriver.Chrome(executable_path=executable_path, options=options)


def process_file(input_file = 'cpf.txt'):
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
    parser.add_argument('--col',
                        help='Defines the column which contains the remote id data to search (default: 0)', default=0, type=int)
    parser.add_argument('--sep',
                        help='Defines separator character of files (default: ;)', default=';')
    parser.add_argument('--local_col', 
                        help="Defines the column which contains the local id data to compare (default: 1)", default=1, type=int)
    return parser.parse_args()

def generate_output_file(args):
    global candidates_dict

    input_file = open(args.input_file)
    lines = input_file.readlines()
    with open(args.output_file, mode='w') as output_file:
        for line in lines:
            line_data = line.split(args.sep)
            write_data = re.sub(r'\D', '', line_data[args.col])
            candidates_dict[write_data] = line_data[args.local_col]
            output_file.write(f'{write_data}\n')
        output_file.close()
    input_file.close()


def create_directory(directory):
    if(not os.path.exists(directory)):
        os.mkdir(directory)


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


def calculate_grades(args):
    export_file_date = date.today().strftime('%d%m%Y')     
    grades_output = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{export_file_date}_PON.txt'
    essay_output = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{export_file_date}_RED.txt'

    result_files = get_result_files()
    for result_file in result_files:
        with open(f'{BASE_DIR}/{DATE_DIR}/{result_file}') as file:
            exam_results = file.readlines()
            for result in exam_results:
                line_data = result.split(';')
                cpf = line_data[1]
                essay_grade = calculate_essay_grade(line_data[7])
                grades_average = calculate_grade_average(line_data[3:7])
                if(grades_average > 0 and essay_grade > 0):
                    save_result_to_file(grades_output, grades_average, cpf)
                    save_result_to_file(essay_output, essay_grade, cpf)
            file.close()


def main():
    try:
        args = extract_args()
        generate_output_file(args)
        create_directory(BASE_DIR)
        create_directory(f'{BASE_DIR}/{DATE_DIR}')
        create_directory(f'{BASE_DIR}/{DATE_DIR}/results')
        # process_file(args.output_file)
        calculate_grades(args)
        print('Script successful executed')
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
