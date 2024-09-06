import tqdm
from utils import *
from multiprocessing import Pool, cpu_count
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
    return prefix, middle, suffix


def random_select_multi_line(function_string):
    """
    Randomly select a snippet of 2 to 6 complete lines from the function body.
    """
    lines = function_string.splitlines()
    n = random.randint(2, min(6, len(lines)))
    start_line_idx = random.randint(0, len(lines) - n)
    end_line_idx = start_line_idx + n
    cut_seq = '\n'.join(lines[start_line_idx: end_line_idx])
    total_len = len(cut_seq)
    start_line = lines[start_line_idx]

    seq_idx1 = function_string.find(start_line)
    seq_idx2 = seq_idx1 + total_len

    for char in start_line:
        if char != ' ':
            break
        seq_idx1 += 1

    prefix = function_string[: seq_idx1]
    middle = function_string[seq_idx1: seq_idx2]
    suffix = function_string[seq_idx2:]

    return prefix, middle, suffix


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
    if np_rng.binomial(1, 0.5):
        prefix = prefix_ + '\n' + leading_whitespace
    else:
        prefix = prefix_

    middle = ""
    suffix = function_string[line_end_idx:]

    return prefix, middle, suffix


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
    return function_sig, function_body


def function_process(jsonl_file_name: str, sample_num: int):
    function_list = random_select(jsonl_file_name, sample_num)


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
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    node_content = random_node.text.decode('utf-8')
    line_num = len(node_content.splitlines())

    if line_num <= 5:
        start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    else:
        if_blocks_level2 = query.captures(random_node)
        if if_blocks_level2 is not None:
            if_block_level2 = random.choice(if_blocks_level2)
            start_idx, end_idx = get_char_seq_idx(if_block_level2[0], byte_to_char)
        else:
            start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)

    fim_span = function_string[start_idx: end_idx]
    # when the line number of "if-block" is over 20, turn to random multi line
    if len(fim_span.splitlines()) > 20:
        return random_select_multi_line(function_string)
    prefix, middle, suffix = get_fim_span(function_string, start_idx, end_idx)
    return prefix, middle, suffix


def extract_switch_case_block(function_string):
    byte_seq = function_string.encode('utf-8')
    byte_to_char = build_byte_to_char_map(byte_seq)
    tree = parser.parse(byte_seq)
    root = tree.root_node

    query = C_LANGUAGE.query("""
    (switch_statement
        body: (compound_statement
            (case_statement)@case-block ))""")
    captures = query.captures(root)
    nodes = [node for node, _ in captures]
    random_node = random.choice(nodes)
    node_content = random_node.text.decode('utf-8')
    line_num = len(node_content.splitlines())
    if line_num > 20:
        return random_select_multi_line(function_string)

    start_idx, end_idx = get_char_seq_idx(random_node, byte_to_char)
    return get_fim_span(function_string, start_idx, end_idx)

