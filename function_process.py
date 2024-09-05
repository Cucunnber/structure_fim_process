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


def function_process(jsonl_file_name: str, sample_num: int):
    function_list = random_select(jsonl_file_name, sample_num)




test_string = \
"""
void readFile(const char *filename) {

    bool flag = true;
    FILE *file = fopen(filename, "r");
    if (file == NULL){
        if (flag == true)
        {
            printf("you know");
        }
        else
        {
            exit();
        }
        perror("Error opening file");
        return;
    }
    
    char buffer[256];
    
    
    while (fgets(buffer, sizeof(buffer), file) != NULL) {
        printf("%s\n", buffer);
    }
    
    fclose(file);
}
"""




# for child in if_block_node.children:
#     if child.type == 'if_statement':
#         consequence = child.child_by_field_name('consequence')
#         print(child.text.decode('utf-8'))

# idx1 = byte_to_char[if_block_node.start_byte]
# idx2 = byte_to_char[if_block_node.end_byte]
# print(len(if_block_nodes))
# print(test_string[idx1:idx2])


def extract_if_block(function_string):
    byte_seq = test_string.encode('utf-8')
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
    if  line_num < 5:



extract_if_block(test_string)