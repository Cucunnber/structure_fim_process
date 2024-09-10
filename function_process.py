from tqdm import tqdm
from utils import *
import multiprocessing
import random


np_rng = np.random.default_rng()


def random_select(jsonl_file_name: str, sample_num):
    data_list = read_jsonl(jsonl_file_name)
    sampled_data = random.sample(data_list, sample_num)
    print(f"select {sample_num} datas in {len(data_list)}datas.")
    return sampled_data


def manual_split_function_body(function_string):
    lines = []
    current_line = []
    in_string = False
    escape_next = False
    line_start_indices = []
    current_index = 0

    # Skip the first line with the function signature and the opening brace
    body_start = function_string.find('{') + 1
    body_end = function_string.rfind('}')

    for i in range(body_start, body_end):
        char = function_string[i]

        if escape_next:
            # Skip escaped characters, add them directly to the current line
            current_line.append(char)
            escape_next = False
        elif char == '\\':
            # If a backslash is encountered, mark the next character as escaped
            current_line.append(char)
            escape_next = True
        elif char == '"':
            # Toggle the in-string flag when encountering a quotation mark
            in_string = not in_string
            current_line.append(char)
        elif char == '\n' and not in_string:
            # When encountering a newline and not inside a string, the line ends
            lines.append(''.join(current_line).strip())
            line_start_indices.append(current_index)
            current_line = []
            current_index = i + 1
        else:
            # Add other characters normally to the current line
            current_line.append(char)

    # Handle the last line (no newline character at the end)
    if current_line:
        lines.append(''.join(current_line).strip())
        line_start_indices.append(current_index)

    # Filter out empty lines and lines with only 1 character
    lines_with_indices = [(line, idx) for line, idx in zip(lines, line_start_indices) if line and len(line.strip()) > 1]

    return lines_with_indices


def random_line_and_chars_with_index(function_string):
    # Parse the function body and manually split valid lines
    lines_with_indices = manual_split_function_body(function_string)

    if not lines_with_indices:
        return None, None, None

    # Randomly select a line
    chosen_line, start_index = random.choice(lines_with_indices)
    stripped_line = chosen_line.strip()

    # Randomly select the number of characters from the start of the chosen line
    if len(stripped_line) > 1:
        num_chars = random.randint(1, len(stripped_line))
    else:
        num_chars = len(stripped_line)

    # Find the ending position of the line in the original string (excluding the newline character)
    actual_line_index = function_string.find(stripped_line, start_index)
    end_of_line_index = actual_line_index + len(stripped_line)

    # Return the start index of the randomly selected characters, the end index, and the line's end index
    return actual_line_index, actual_line_index + num_chars - 1, end_of_line_index


def single_line_process(function_string):
    """
    random select a suffix code snippet of a random line in the function string
    """
    _, snippet_end_idx, line_end_idx = random_line_and_chars_with_index(function_string)
    prefix = function_string[: snippet_end_idx]
    middle = function_string[snippet_end_idx: line_end_idx]
    suffix = function_string[line_end_idx:]
    flag = "RANDOM_SINGLE_LINE"
    return prefix, middle, suffix, flag


def extract_expression_statement(function_string):
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node
    query = C_LANGUAGE.query("(expression_statement) @es")
    captures = query.captures(root)
    if not captures:
        return single_line_process(function_string)
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
    flag = "EXPRESSION_STATEMENT"
    return prefix, middle, suffix, flag


def extract_binary_expression(function_string):
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node
    query = C_LANGUAGE.query("(binary_expression) @be")
    captures = query.captures(root)
    if not captures:
        return single_line_process(function_string)
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
    flag = "BINARY_EXPRESSION"
    return prefix, middle, suffix, flag


def random_select_multi_line(function_string):
    """
    Randomly select a snippet of 2 to 6 complete lines from the function body.
    """
    lines = [line for line in function_string.splitlines() if line.strip()]
    line_num = len(lines)

    if line_num < 5:
        return '', '', '', "USELESS"

    start_line_idx = random.randint(1, line_num-3)
    # start_line_idx = 12
    n = random.randint(2, min(6, line_num-start_line_idx))
    end_line_idx = start_line_idx + n - 1

    first_line = lines[start_line_idx]
    remain_idx = 0
    while remain_idx < len(first_line) and (first_line[remain_idx] == ' ' or first_line[remain_idx] == '\t'):
        remain_idx += 1

    prefix = '\n'.join(lines[:start_line_idx]) + '\n' + first_line[: remain_idx]
    middle = first_line[remain_idx:] + '\n' + '\n'.join(lines[start_line_idx+1:end_line_idx+1])
    suffix = '\n' + '\n'.join(lines[end_line_idx+1:])

    flag = "RANDOM_MULTI_LINE"
    return prefix, middle, suffix, flag


def empty_process(function_string):
    """
    Randomly select the end of a line as the finish span.
    Add \n to the end of "prefix" with a 50% probability and preserve the correct indentation.
    """
    _, _, line_end_idx = random_line_and_chars_with_index(function_string)
    prefix_ = function_string[:line_end_idx]

    # Determine the indentation of the current line
    current_line_start = function_string.rfind('\n', 0, line_end_idx) + 1
    current_line = function_string[current_line_start:line_end_idx]

    # Extract leading spaces or tabs for indentation
    leading_whitespace = ''
    for char in current_line:
        if char in (' ', '\t'):
            leading_whitespace += char
        else:
            break

    # Decide whether to add a newline and preserve indentation
    if np_rng.binomial(1, 0.7):
        prefix = prefix_ + '\n' + leading_whitespace
    else:
        prefix = prefix_

    middle = ""
    suffix = function_string[line_end_idx:]
    flag = "EMPTY"

    return prefix, middle, suffix, flag


def short_function_process(function_string):
    """
    extract function body of short function which has less than 20 lines
    """
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node

    query = C_LANGUAGE.query("""
    (function_definition
        body: (compound_statement) @function-body)""")
    node = query.captures(root)[0][0]
    start_idx = byte_to_char[node.start_byte]
    function_body = node.text.decode('utf-8')
    function_sig = function_string[: start_idx]
    suffix = ""
    flag = "SHORT_FUNCTION"

    return function_sig, function_body, suffix, flag


def long_if_block_process(function_string, start_idx, fim_span):
    n = random.randint(3, 10)
    lines = fim_span.splitlines()
    part = '\n'.join(lines[:n])
    end_idx = start_idx + len(part)
    if np_rng.binomial(1, 0.5):
        return *(get_fim_span(function_string, start_idx, end_idx)), "IF_BLOCK_LONG"
    else:
        return *(get_fim_span_half(function_string, start_idx, end_idx)), "IF_BLOCK_LONG"


def extract_if_block(function_string):
    """
    select if-statement block in function sequence
    """
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node

    query = C_LANGUAGE.query("""
    (if_statement
      condition: (parenthesized_expression)
      consequence: (compound_statement) @if-block
      (else_clause
        (compound_statement) @else-block)?)""")

    captures = query.captures(root)
    if not captures:
        return random_select_multi_line(function_string)
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    node_content = random_node.text.decode('utf-8')
    line_num = len(node_content.splitlines())

    if line_num <= 5:
        start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    else:
        if_blocks_level2 = query.captures(random_node)
        if len(if_blocks_level2) != 0:
            if_block_level2 = random.choice(if_blocks_level2)
            start_idx, end_idx = get_char_seq_idx(if_block_level2[0], byte_to_char)
        else:
            start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)

    fim_span = function_string[start_idx: end_idx]
    # when the line number of "if-block" is over 20, turn to random multi line
    if len(fim_span.splitlines()) > 20:
        return long_if_block_process(function_string, start_idx, fim_span)
    if np_rng.binomial(1, 0.5):
        prefix, middle, suffix = get_fim_span_(function_string, start_idx, end_idx)
    else:
        prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
    flag = "IF_BLOCK"
    return prefix, middle, suffix, flag


def long_switch_case_process(function_string, start_idx, end_idx):
    n = random.randint(3, 10)
    fim_span = function_string[start_idx:end_idx]
    lines = fim_span.splitlines()
    part = '\n'.join(lines[:n])
    end_idx2 = start_idx + len(part)
    if np_rng.binomial(1, 0.5):
        return *(get_fim_span(function_string, start_idx, end_idx2)), "SWITCH_CASE_LONG"
    else:
        return *(get_fim_span_half(function_string, start_idx, end_idx2)), "SWITCH_CASE_LONG"


def extract_switch_case_block(function_string):
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node

    query = C_LANGUAGE.query("""
    (switch_statement
        body: (compound_statement
            (case_statement
                (compound_statement) @case-block)))""")
    captures = query.captures(root)
    if not captures:
        return random_select_multi_line(function_string)
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    node_content = random_node.text.decode('utf-8')
    line_num = len(node_content.splitlines())

    start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    if line_num > 20:
        return long_switch_case_process(function_string, start_idx, end_idx)

    if np_rng.binomial(1, 0.5):
        prefix, middle, suffix = get_fim_span_(function_string, start_idx, end_idx)
    else:
        prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
    flag = "SWITCH_CASE"
    return prefix, middle, suffix, flag


def long_loop_process(function_string, start_idx, end_idx):
    n = random.randint(3, 10)
    fim_span = function_string[start_idx:end_idx]
    lines = fim_span.splitlines()
    part = '\n'.join(lines[:n])
    end_idx2 = start_idx + len(part)
    if np_rng.binomial(1, 0.5):
        return *(get_fim_span(function_string, start_idx, end_idx2)), "LOOP_BLOCK_LONG"
    else:
        return *(get_fim_span_half(function_string, start_idx, end_idx2)), "LOOP_BLOCK_LONG"


def extract_loop_block(function_string):
    """
    random  select while/for/macro_func loop block
    """
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node

    query = C_LANGUAGE.query("""
    (compound_statement) @blocks
    """)

    captures = query.captures(root)
    loop_block_nodes = []

    for node, _ in captures:
        if (node.parent.type == "if_statement" or node.parent.type == "function_definition") \
                or node.parent.type == "else_clause" or node.parent.type == "switch_statement" \
                or node.parent.type == "do_statement" or node.parent.type == "case_statement":
            continue
        loop_block_nodes.append(node)

    if not loop_block_nodes:
        return random_select_multi_line(function_string)

    max_attempts = min(3, len(loop_block_nodes))
    last_start_idx = 0
    last_end_idx = 0
    for _ in range(max_attempts):
        selected_node = random.choice(loop_block_nodes)
        node_text = selected_node.text.decode('utf-8')
        line_count = len(node_text.splitlines())

        start_idx, end_idx = get_char_seq_idx(selected_node, byte_to_char)

        if line_count <= 20:
            if np_rng.binomial(1, 0.5):
                prefix, middle, suffix = get_fim_span_(function_string, start_idx, end_idx)
            else:
                prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
            flag = "LOOP_BLOCK"
            return prefix, middle, suffix, flag
        last_start_idx, last_end_idx = start_idx, end_idx
    return long_loop_process(function_string, last_start_idx, last_end_idx)


def function_process(jsonl_file_name: str, sample_num: int, output_path):
    new_datas = []

    # 从文件中随机选择一些函数列表
    function_list = random_select(jsonl_file_name, int(sample_num))

    # 使用 multiprocessing.Pool 来并行化
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    # 将每个 item 传递给 process_single_item 并行处理
    new_datas = pool.map(process_single_item, function_list)

    # 关闭进程池并等待所有进程结束
    pool.close()
    pool.join()

    # 将结果写入 JSONL 文件
    write_jsonl(output_path, new_datas)


def process_single_item(json_data):
    func_str = json_data["func_def"]
    line_num = len(func_str.splitlines())

    if line_num <= 20 and np_rng.binomial(1, 0.1):
        prefix, middle, suffix, flag = short_function_process(func_str)
    else:
        # 选择处理函数
        process_options = [single_line_process, extract_expression_statement, extract_binary_expression,
                           random_select_multi_line, extract_if_block, extract_loop_block,
                           extract_switch_case_block, empty_process]
        probs = [0.25, 0.2, 0.05, 0.1, 0.1, 0.15, 0.05, 0.1]

        select_option = random.choices(process_options, probs)[0]
        prefix, middle, suffix, flag = select_option(func_str)

    return {
        "file_path": json_data["file_path"],
        "func_name": json_data["func_name"],
        "prefix": prefix,
        "middle": middle,
        "suffix": suffix,
        "flag": flag
    }
