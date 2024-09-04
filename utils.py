import os
import re
import json
import chardet
from tree_sitter import Language, Parser
import tree_sitter_c as tsc


CWD = os.path.dirname(os.path.abspath(__file__))

C_LANGUAGE = Language(tsc.language())
parser = Parser()
parser.language = C_LANGUAGE


def build_byte_to_char_map(byte_sequence):
    byte_to_char_map = []
    char_sequence = byte_sequence.decode('utf-8')
    for char_index, char in enumerate(char_sequence):
        char_bytes = char.encode('utf-8')
        for _ in char_bytes:
            byte_to_char_map.append(char_index)
    return byte_to_char_map


def find_c_files(directory, skip_dirs=None):
    """
    Return a list of C files (with .c or .h suffix) under the directory.
    """
    skip_dirs = set(skip_dirs) if skip_dirs is not None else None
    c_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if skip_dirs is not None:
                dirs = set(path.split(os.sep))
                if dirs & skip_dirs:
                    continue
            if file.endswith('.c') or file.endswith('.h'):
                c_files.append(path)
    return c_files


def find_c_source_files(directory, skip_dirs=None):
    """
    Return a list of C files (with .c or .h suffix) under the directory.
    """
    skip_dirs = set(skip_dirs) if skip_dirs is not None else None
    c_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if skip_dirs is not None:
                dirs = set(path.split(os.sep))
                if dirs & skip_dirs:
                    continue
            if file.endswith('.c'):
                c_files.append(path)
    return c_files


def find_files(directory, include_regex=None):
    """
    Return a list of files under the directory.
    """
    if include_regex is not None:
        include_regex = re.compile(include_regex)
    files = []
    for root, _, file_names in os.walk(directory):
        for file_name in file_names:
            file_path = os.path.join(root, file_name)
            if include_regex is None or include_regex.match(file_path):
                files.append(file_path)
    return files


def read_jsonl(filepath):
    dataset = []
    with open(filepath, 'r') as rf:
        for line in rf:
            json_obj = json.loads(line)
            dataset.append(json_obj)
    return dataset


def write_jsonl(filepath, dataset: list, ensure_ascii=False):
    with open(filepath, 'w') as wf:
        wf.writelines([json.dumps(obj, ensure_ascii=ensure_ascii) + '\n' for obj in dataset])


def should_skip_path(path, include_regex=None, exclude_regex=None):
    if include_regex is not None and not include_regex.match(path):
        return True
    if exclude_regex is not None and exclude_regex.match(path):
        return True
    return False


def versatile_find_files(root, include_regex=None, exclude_regex=None, depth=float('inf')) -> list[str]:
    """
    Return a list of files or directories under the root directory.
    """
    if isinstance(include_regex, str):
        include_regex = re.compile(include_regex)
    if isinstance(exclude_regex, str):
        exclude_regex = re.compile(exclude_regex)
    paths = [root]
    is_updated = True
    while depth > 0 and is_updated:
        is_updated = False
        new_paths = []
        for path in paths:
            # add the file in paths to new_paths
            if os.path.isfile(path):
                new_paths.append(path)
            # search the directory in paths recursively
            elif os.path.isdir(path):
                for item in os.listdir(path):
                    new_path = os.path.join(path, item)
                    if should_skip_path(new_path, include_regex, exclude_regex):
                        continue
                    new_paths.append(new_path)
                    is_updated = True
            else:
                raise ValueError('Invalid path: ' + path)
        
        paths = new_paths # update paths to new_paths
        depth -= 1
    return paths


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        return encoding


def versatile_read_file(filepath):
    detected_encoding = detect_encoding(filepath)
    possible_encoding = [detected_encoding, 'utf-8', 'gb2312', 'gbk', 'gb18030']
    content = None
    for encoding in possible_encoding:
        try:
            with open(filepath, 'r', encoding=encoding) as rf:
                content = rf.read()
            break
        except:
            continue
    if content is None:
        print('Failed to read file: {}, detected encoding: {}'.format(filepath, detected_encoding))
        return ''
    return content
