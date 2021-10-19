import time
import traceback
import argparse

from .exam_grades import generate_request_file, get_response_files, initialize_directories, save_final_results


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
    initialize_directories()
    request_file = generate_request_file(**args)
    response_files = get_response_files(request_file)
    save_final_results(response_files)
except:
    traceback.print_exc()
finally:
    print(f'Script exited. Execution time: {time.time() - start_time}s')
