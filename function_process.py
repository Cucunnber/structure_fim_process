import tqdm
from utils import *
from multiprocessing import Pool, cpu_count
import random


def random_select(jsonl_file_name: str, sample_num):
    data_list = read_jsonl(jsonl_file_name)
    sampled_data = random.sample(data_list, sample_num)
    print(f"select {sample_num} datas in {len(data_list)}datas.")
    return sampled_data


def function_process(jsonl_file_name: str, sample_num: int):
    function_list = random_select(jsonl_file_name, sample_num)
