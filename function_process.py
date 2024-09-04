import tqdm
from utils import *
from multiprocessing import Pool, cpu_count
import random


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

    # 跳过第一行函数签名以及开头的花括号
    body_start = function_string.find('{') + 1
    body_end = function_string.rfind('}')

    for i in range(body_start, body_end):
        char = function_string[i]

        if escape_next:
            # 跳过转义字符，直接加入当前行
            current_line.append(char)
            escape_next = False
        elif char == '\\':
            # 如果遇到反斜杠，标记下一个字符被转义
            current_line.append(char)
            escape_next = True
        elif char == '"':
            # 遇到引号，切换字符串内部标记
            in_string = not in_string
            current_line.append(char)
        elif char == '\n' and not in_string:
            # 遇到换行符且不在字符串内，表示一行结束
            lines.append(''.join(current_line).strip())
            line_start_indices.append(current_index)
            current_line = []
            current_index = i + 1
        else:
            # 其他字符正常加入当前行
            current_line.append(char)

    # 处理最后一行（没有换行符）
    if current_line:
        lines.append(''.join(current_line).strip())
        line_start_indices.append(current_index)

    # 过滤掉空行和仅包含1个字符的行
    lines_with_indices = [(line, idx) for line, idx in zip(lines, line_start_indices) if line and len(line.strip()) > 1]

    return lines_with_indices


def random_line_and_chars_with_index(function_string):
    # 解析函数体并手动分割有效行
    lines_with_indices = manual_split_function_body(function_string)

    if not lines_with_indices:
        return None, None, None

    # 随机选择一行
    chosen_line, start_index = random.choice(lines_with_indices)
    stripped_line = chosen_line.strip()

    # 在选定的行中随机选择一个开头的字符数
    if len(stripped_line) > 1:
        num_chars = random.randint(1, len(stripped_line))
    else:
        num_chars = len(stripped_line)

    # 找出该行在原字符串中的结束位置（不包括换行符）
    actual_line_index = function_string.find(stripped_line, start_index)
    end_of_line_index = actual_line_index + len(stripped_line)

    # 返回随机选取字符的起始索引，结束索引，以及该行的结束索引
    return actual_line_index, actual_line_index + num_chars - 1, end_of_line_index


def random_line_end_index(function_string):
    # 解析函数体并手动分割有效行
    lines_with_indices = manual_split_function_body(function_string)

    if not lines_with_indices:
        return None

    # 随机选择一行
    chosen_line, start_index = random.choice(lines_with_indices)

    # 找出该行在原字符串中的结束位置（包括所有字符，连同空格和符号）
    end_of_line_index = start_index + len(chosen_line) - 1  # 找到行末尾的非换行字符索引

    # 返回该行末尾非换行符前最后一个字符的索引
    return end_of_line_index


def function_process(jsonl_file_name: str, sample_num: int):
    function_list = random_select(jsonl_file_name, sample_num)


test_string = \
"""
void readFile(const char *filename) {


    FILE *file = fopen(filename, "r");
    if (file == NULL) {
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

idx1, idx2, idx3 = random_line_and_chars_with_index(test_string)

print(test_string[idx1:idx3])