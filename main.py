import argparse
from extract_all_functions import collect_functions


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--collect_funcs', nargs='+', type=str, default=None, help='args for collect funcs')
    # arg_parser.add_argument('--task2', nargs='+', type=str, default=None, help='args for task2')
    # arg_parser.add_argument('--task3', nargs='+', type=str, default=None, help='args for task3')
    # arg_parser.add_argument('--task4', nargs='+', type=str, default=None, help='args for task4')
    # arg_parser.add_argument('--parallel', default=False, action='store_true', help='whether to run tasks in parallel')
    args = arg_parser.parse_args()
    if args.collect_funcs is not None:
        collect_functions(*args.collect_funcs)
    # if args.task2 is not None:
    #     task2(*args.task2)
    # if args.task3 is not None:
    #     task3(*args.task3, parallel=args.parallel)
    # if args.task4 is not None:
    #     task4(*args.task4)