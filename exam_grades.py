# -*- encoding: utf-8 -*-

import argparse, sys, os, re, time, glob, traceback
from datetime import date, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

INPUT_FILE_LAYOUT = {
    'cpf': 2,
    'subscription': 0,
    'year': 3
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

url = "http://sistemasenem.inep.gov.br/EnemSolicitacao/"

def create_directory(directory):
    if(not os.path.exists(directory)):
        os.mkdir(directory)


def initialize_directories():
    create_directory(BASE_DIR)
    create_directory(f'{BASE_DIR}/{DATE_DIR}')
    create_directory(f'{BASE_DIR}/{DATE_DIR}/results')


def get_args():
    parser = argparse.ArgumentParser(
        description='Extract cpf from input file and remove any non digit character')
    parser.add_argument('input_file', metavar='input_file', type=str,
                        help='input file path')
    parser.add_argument('output_file', metavar='output_file', type=str,
                        help='output file path')
    parser.add_argument('--sep',
                        help='Defines separator character of files (default: ;)', default=';')
    return vars(parser.parse_args())


def read_file_lines(file):
    lines = []
    if(os.path.exists(file)):
        with open(file) as read_file:
            lines = read_file.read().splitlines()
    return lines


def write_lines_to_file(file, data, mode='a', end='\n'):
    with open(file, mode=mode) as output_file:
        output_file.write(f'{data}{end}')


def already_processed(cpf):
    processed_candidates = read_file_lines(LOG_FILE)
    return cpf in processed_candidates


def generate_request_file(input_file, output_file, sep=';'):
    global candidates_dict
    lines = read_file_lines(input_file)
    output = []
    for line in lines:
        line_data = line.split(sep)
        cpf = re.sub(r'\D', '', line_data[INPUT_FILE_LAYOUT['cpf']])
        candidates_dict[cpf] = {
            'subscription': line_data[INPUT_FILE_LAYOUT['subscription']],
            'year': line_data[INPUT_FILE_LAYOUT['year']]
        }
        if(not already_processed(cpf)):
            output.append(cpf)
    output_data = '\n'.join(output)
    write_lines_to_file(file=output_file, data=output_data, mode='w')
    return output_file


def file_has_data(file):
    return os.path.getsize(file) > 0

# webscraping - download result files

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


def login(webdriver):
    webdriver.get(url)
    webdriver.implicitly_wait(5)
    webdriver.switch_to.frame(webdriver.find_element_by_tag_name('iframe'))
    webdriver.find_element_by_id('username').send_keys(USERNAME)
    webdriver.find_element_by_id('password').send_keys(PASSWORD)
    webdriver.find_element_by_xpath("//input[@type='image']").click()
    webdriver.implicitly_wait(5)


def send_request_file(driver, submenu_id, input_file):
    driver.find_element_by_id(submenu_id).click()
    year = driver.find_element_by_xpath(f"//div[@id='{submenu_id}']/table/tbody/tr/td[contains(@class, 'rich-pmenu-group-self-label')]").text
    driver.find_element_by_xpath(f"//div[@id='{submenu_id}']/div/table/tbody/tr/td[text()='Por arquivo (Cpf)']").click()
    driver.find_element_by_xpath("//form[@id='formForm']/div[@id='uploadid']//input[@type='file']").send_keys(os.path.realpath(input_file))
    driver.implicitly_wait(1)
    driver.find_element_by_id('uploadid:upload1').click()
    time.sleep(5)
    return year
    

def last_requested_today(driver, time):
    last_request = driver.find_element_by_xpath("//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td[@id='listaSolicitacaoAtendidas:0:j_id160']/div")
    last_request_date = datetime.strptime(last_request.text, '%d/%m/%Y %H:%M:%S')
    return last_request_date.time() >= time.time()


def download_response_file(driver):
    file_name = ''
    two_minutes = timedelta(minutes=2)
    execution_time = datetime.now() - two_minutes
    driver.find_element_by_xpath("//div[@id='menugroup_5']/div").click()
    driver.implicitly_wait(5)
    if(last_requested_today(driver, execution_time)):
        download_link = driver.find_element_by_xpath("//table[@id='listaSolicitacaoAtendidas']//tbody[@id='listaSolicitacaoAtendidas:tb']//tr[contains(@class,'rich-table-firstrow')]//td/div/a")
        file_name = download_link.get_attribute('href').split('/')[-1]
        if(not file_exists(file_name)):
            download_link.click()
        time.sleep(5)
    return file_name


def get_results_by_year(webdriver, input_file):
    login(webdriver)
    response_files_by_year = {}
    submenus = [submenu.get_attribute('id') for submenu in webdriver.find_elements_by_xpath("//div[@id='menugroup_4']/div[not(@id='menugroup_4_1')]")]
    for submenu_id in submenus:
        year =  send_request_file(webdriver, submenu_id, input_file)
        time.sleep(10)
        file = download_response_file(webdriver)
        if(file):
            response_files_by_year[year] = file
        webdriver.implicitly_wait(2)
    time.sleep(3)
    webdriver.quit()
    return response_files_by_year
    

def get_response_files(input_file):
    if(file_has_data(input_file)):
        driver = get_webdriver()
        return get_results_by_year(driver, input_file)
        

def get_exam_results_files():
    directory = os.path.realpath(f'{BASE_DIR}/{DATE_DIR}')
    return glob.glob1(directory, "*.txt")


def file_exists(search_file):
    file_list = get_exam_results_files()
    if search_file in file_list:
        return True
    return False


def calculate_grade_average(grades):
    average = sum([float(grade) for grade in grades]) / 4
    return round(average * 30 / 1000)


def calculate_essay_grade(grade):
    return round(float(grade) / 100)


def candidate_year(cpf, year):
    global candidates_dict
    candidate = candidates_dict.get(cpf)
    return candidate.get('year') == year


def grade_exists(haystack, needle):
    return needle in haystack


def save_final_results(files):    
    result_file_date = date.today().strftime('%d%m%Y')     
    grades_file = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{result_file_date}_PON.txt'
    essay_file = f'{BASE_DIR}/{DATE_DIR}/results/EXP_{result_file_date}_RED.txt'

    grades_output = []
    essay_output = []
    processed_registers_output = []
    errors_output = []

    for year, filename in files.items():
        exam_results = read_file_lines(f'{BASE_DIR}/{DATE_DIR}/{filename}')
        for result in exam_results:
            line_data = result.split(';')
            cpf = line_data[EXAM_RESULTS_LAYOUT['cpf']]
            subscription = candidates_dict.get(cpf)['subscription']
            essay_grade = calculate_essay_grade(line_data[EXAM_RESULTS_LAYOUT['essay']])
            grades_average = calculate_grade_average(line_data[EXAM_RESULTS_LAYOUT['grades']])
            if(essay_grade > 0):
                if (not grade_exists(processed_registers_output, cpf)):
                    essay_output.append(f'{"X" * 40}{subscription.zfill(6)}{"X" * 14}{essay_grade}')
                    grades_output.append(f'{"X" * 40}{subscription.zfill(6)}{"X" * 14}{grades_average}')
                    processed_registers_output.append(cpf)  
            else:
                if(cpf not in errors_output):
                    errors_output.append(cpf)
    write_lines_to_file(file='errors.log', data='\n'.join(errors_output), mode='a')
    write_lines_to_file(file=grades_file, data='\n'.join(grades_output), mode='a')
    write_lines_to_file(file=essay_file, data='\n'.join(essay_output), mode='a')
    write_lines_to_file(file=LOG_FILE, data='\n'.join(processed_registers_output), mode='a')


def main():
    start_time = time.time()
    try:
        args = get_args()
        initialize_directories()
        request_file = generate_request_file(**args)
        response_files = get_response_files(request_file)
        save_final_results(response_files)        
    except:
        traceback.print_exc()
    finally:
        print(f'Script exited. Execution time: {time.time() - start_time}s')


if __name__ == "__main__":
    main()


