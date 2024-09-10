import argparse
from extract_all_functions import collect_functions
from function_process import function_process


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--collect_funcs', nargs='+', type=str, default=None, help='args for collect funcs')
    arg_parser.add_argument('--function_process', nargs='+', type=str, default=None, help='args for function process')

    args = arg_parser.parse_args()
    if args.collect_funcs is not None:
        collect_functions(*args.collect_funcs)
    if args.function_process is not None:
        function_process(*args.function_process)
