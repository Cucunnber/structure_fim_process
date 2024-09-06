import tqdm
from utils import *
from multiprocessing import Pool, cpu_count

dirs_to_skip = ["grpcplugin", "resource", "webplugin", "verifysuite"]


def extract_functions(code_byte_sequence):
    """
    capture function definition node
    """
    tree = parser.parse(code_byte_sequence)
    root_node = tree.root_node
    query = C_LANGUAGE.query('(function_definition) @func_def')
    captures = query.captures(root_node)
    function_nodes = [node for node, _ in captures]
    return function_nodes


def get_function_node_name(function_node):
    """
    capture function name node
    """
    query = C_LANGUAGE.query("""
    (function_definition
      (function_declarator
        (identifier)@func_name))""")
    captures = query.captures(function_node)
    for node, _ in captures:
        return node.text.decode('utf-8')


def convert_to_linux_path(path):
    """
    convert path to standard Linux path style
    """
    norm_path = os.path.normpath(path)
    return norm_path.replace(os.sep, '/')


def process_file(c_file):
    source_code = versatile_read_file(c_file)
    if not source_code:
        return None
    code_byte_sequence = source_code.encode('utf-8')
    function_nodes = extract_functions(code_byte_sequence)

    func_table = []
    for function_node in function_nodes:
        function_content = function_node.text.decode('utf-8')
        function_name = get_function_node_name(function_node)
        file_path = convert_to_linux_path(c_file)
        func_table.append({
            "func_name": function_name,
            "file_path": file_path,
            "func_def": function_content
        })
    return func_table


def collect_functions(project_directory, output_name):
    c_source_files = find_c_source_files(project_directory, skip_dirs=dirs_to_skip)

    with Pool(processes=cpu_count()) as pool:
        results = list(tqdm.tqdm(pool.imap(process_file, c_source_files), total=len(c_source_files)))

    func_table = [item for sublist in results if sublist for item in sublist]

    save_path = output_name
    write_jsonl(save_path, func_table)

