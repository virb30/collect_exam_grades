import os
import time
import traceback
import argparse

from exam_grades import ENEMScrap

USERNAME = os.environ['WS_USERNAME']
PASSWORD = os.environ['WS_PASSWORD']


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


start_time = time.time()
try:
    args = get_args()

    scrap = ENEMScrap(username=USERNAME, password=PASSWORD)
    scrap.run(**args)
except:
    traceback.print_exc()
finally:
    print(f'Script exited. Execution time: {time.time() - start_time}s')
