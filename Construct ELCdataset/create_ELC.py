"""
改为使用递归函数查找符合要求的文章组合
全部查找完成也不符合时去另一个list随便找一个截取即可
"""
import time
import os
import jsonlines
import json
import random
import re
from tqdm import tqdm

QUESTION_TYPEMAP = {
    "1": "Detail Comprehension",
    "2": "Main Idea & Perspective",
    "3": "Inference & Judgment",
    "4": "Semantic & Reference",
    "5": "Paragraph Sequencing",
    "6": "Search & Match"
}

DEFAULT_QUESTION_INSTRUCTION = "This is a question about article {}. Please choose the correct answer from options A, B, C, and D below to answer the question."

def load_jsonl_data(file_path):
    article_data = []  # 保存每篇文章的字符串及其对应的单词数

    # 读取jsonl文件
    with jsonlines.open(file_path, "r") as reader:
        for data in reader:
            article_id = data["id"]
            article_word_count = 0  # 当前文章的总单词数
            for index, passage in enumerate(data["passages"]):
                passage_content = passage["passage_content"]
                passage_id = passage["order"]

                # 计算当前passage的单词数量
                passage_words = passage_content.split()
                passage_word_count = len(passage_words) + 10
                article_word_count += passage_word_count

                # 创建当前段落的字符串格式
                formatted_passage = f"<article {article_id} paragraph {passage_id}> {passage_content} </article {article_id} paragraph {passage_id}>\n"
                data["passages"][index]["passage_content"] = formatted_passage
                data["passages"][index]["passage_wordcounts"] = passage_word_count

            data["article_wordcounts"] = article_word_count

            # 保存文章及其单词数
            article_data.append(data)

    return article_data

def filter_data(data_list, args):
    filtered_data_list = []  # 有所需类别题目的文章
    unfiltered_data_list = []  # 没有所需类别题目的文章
    for i, data in enumerate(data_list):
        # 获取指定数据集的文章
        if args["dataset_name"] == "ALL" or data["dataset_name"] == args["dataset_name"]:
            # 获取指定类别的问题
            question_list = []
            for question in data["questions"]:
                if args["category"] == "ALL" or question["category"] == QUESTION_TYPEMAP[args["category"]]:
                    question_list.append(question)

            # 有指定类别的问题，说明该文章可以保存下来
            if question_list != []:
                data["questions"] = question_list
                filtered_data_list.append(data)
                continue
        # 不符合的都作为噪音文章
        unfiltered_data_list.append(data)
    
    print("符合要求的文章总数量 {} 篇，噪音文章总数量 {} 篇".format(len(filtered_data_list), len(unfiltered_data_list)))
    return filtered_data_list, unfiltered_data_list

def get_unique_list(final_choose_list):
    unique_list = []
    seen = set()
    for item in final_choose_list:
        id = [x["id"] for x in item["choose_list"]]
        if str(id) not in seen:
            unique_list.append(item)
            seen.add(str(id))
    return unique_list

choose_list = [] # 最终的方案选择,全局变量
def dfs_concat(pos, current_word_count, res_jump_pos, args):
    if current_word_count >= args["upper_limit"]:
        return
    if current_word_count in range(args["lower_limit"], args["upper_limit"]) or pos >= len(args["data_list"]):
        temp_choose_list = [data for flag, data in zip(args["flags"], args["data_list"]) if flag == 1]
        if len(temp_choose_list) > 0:
            choose_list.append({
                "choose_list": temp_choose_list,
                "word_total_count": sum(data["article_wordcounts"] for data in temp_choose_list),
            })

        if len(choose_list) >= args["required_strings"]: return True
        else: return False
    
    next_pos = pos + 1
    random_chance = random.uniform(0, 1)
    # 剩余跳跃次数，并且此处允许跳跃
    if res_jump_pos > 0 and random_chance > args["next_pos_chance"] and pos + 1 <= len(args["data_list"]) - 1:
        next_pos = random.randint(pos + 1, min(len(args["data_list"]) - 1, pos + 8))

    args["flags"][pos] = 1
    enough = dfs_concat(next_pos, current_word_count + args["data_list"][pos]["article_wordcounts"], res_jump_pos - (1 if next_pos != pos + 1 else 0), args)
    if enough: return True
    args["flags"][pos] = 0
    enough = dfs_concat(next_pos, current_word_count, res_jump_pos, args)
    if enough: return True
    return False

def search_ELC_article(word_limit, lower_limit, up_limit, required_strings, next_pos_chance, jump_pos_cnt, filtered_data_list, unfiltered_data_list):
    """
    word_limit: 字符串的单词数限制(单位为k)
    lower_limit, up_limit: 字符串长度范围比例
    required_strings: 要输出几个这样的字符串
    next_pos_chance: (0~1之间)下一个位置的选择方式，提高比率将会正常一步步遍历，降低比率将会跳跃遍历数组
    jump_pos_cnt: 允许跳跃遍历数组次数
    """
    lower_limit = round(word_limit * 1000 * (1 - lower_limit))
    upper_limit = round(word_limit * 1000 * (1 + up_limit))
    final_choose_list = []
    for start_pos in range(0, len(filtered_data_list)):
        choose_list.clear()
        dfs_concat(pos = start_pos, current_word_count = 0, res_jump_pos = jump_pos_cnt, args={
            "data_list": filtered_data_list,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit,
            "flags": [0] * len(filtered_data_list),
            "required_strings": required_strings * 2,
            "next_pos_chance": next_pos_chance
        })
        final_choose_list += choose_list
    
    final_choose_list.sort(key=lambda x: (-x["word_total_count"], -len(x["choose_list"])))
    final_choose_list = get_unique_list(final_choose_list)

    print("search done")

    ELC_choose = []
    for choose in final_choose_list:
        if choose["word_total_count"] >= lower_limit:
            ELC_choose.append({
                "filter": choose,
                "unfilter": {"choose_list": [], "word_total_count": 0}
            })
        else:
            # 对字数不够的长文本去寻找文章来补全长度
            random.shuffle(unfiltered_data_list)
            choose_list.clear()
            dfs_concat(pos = 0, current_word_count = choose["word_total_count"], res_jump_pos = jump_pos_cnt, args={
                "data_list": unfiltered_data_list,
                "lower_limit": lower_limit,
                "upper_limit": upper_limit,
                "flags": [0] * len(unfiltered_data_list),
                "required_strings": 1,
                "next_pos_chance": 1
            })
            ELC_choose.append({
                "filter": choose,
                "unfilter": {"choose_list": [], "word_total_count": 0} if choose_list == [] else choose_list[0]
            })
        if len(ELC_choose) >= required_strings:
            break


    return ELC_choose

def build_query(article_id, stem, all_choice, instruction = DEFAULT_QUESTION_INSTRUCTION):
    return "{} {}\n{}".format(instruction.format(article_id), stem, all_choice)

def construct_ELC_data(elc, Print_Flag = True, shuffle_choice = False):
    normal_article = elc["filter"]["choose_list"]
    noise_article = elc["unfilter"]["choose_list"]
    article_list = normal_article + noise_article
    pos_list = [0] * len(article_list)

    # 没意义，只是为了统计一下数据
    normal_para = [para["passage_content"] for data in normal_article for para in data["passages"]]
    noise_para = [para["passage_content"] for data in noise_article for para in data["passages"]]
    para_list = normal_para + noise_para

    if Print_Flag:
        print("正常单词数 {}，噪音单词数 {}".format(elc["filter"]["word_total_count"], elc["unfilter"]["word_total_count"]))
        print("正常文章id：(总数 {})".format(len(normal_article)))
        for data in normal_article:
            print(data["id"], end = " ")
        print("")
        print("噪声文章id：(总数 {})".format(len(noise_article)))
        for data in noise_article:
            print(data["id"], end = " ")
        print("")

    ## 超长文章构建
    ELC_str = ""
    # 总共取len(para_list)次
    for _ in range(0, len(para_list)):
        while True:
            random_acticle = random.randint(0, len(article_list) - 1)
            # 取该篇文章的段落已经全部选完了
            if pos_list[random_acticle] >= len(article_list[random_acticle]["passages"]):
                continue

            # 取随机某篇文章的下一个段落
            ELC_str += article_list[random_acticle]["passages"][pos_list[random_acticle]]["passage_content"]
            pos_list[random_acticle] += 1
            break
    
    ## 问答构建
    query_list_choiceunshuffled = []
    query_list_choiceshuffled = []
    for data in normal_article:
        article_id = data["id"]
        for question in data["questions"]:
            # 获取数据
            if True:
                stem = question["question_stem"]
                choices = question["choices"]
                answer_key_unshuffled = {}
                all_choice = ""
                for choice_index, choice in enumerate(choices):
                    all_choice += choice["tag"] + ". " + choice["text"] + "\n"
                    if choice["tag"] == question["answer_key"]:
                        answer_key_unshuffled = {
                            "tag": choice["tag"],
                            "text": choice["text"]
                        }
                query_list_choiceunshuffled.append({
                    "query": build_query(article_id, stem, all_choice),
                    "answer_key": answer_key_unshuffled
                })

            if True:
                stem = question["question_stem"]
                choices = question["choices"]
                answer_key_shuffled = {}
                all_choice = ""
                # 找到答案所在的选项
                for choice in choices:
                    if choice["tag"] == question["answer_key"]:
                        answer_key_shuffled = choice
                # 打乱选项
                shuffled_choices = random.sample(choices, len(choices))
                for choice_index, choice in enumerate(shuffled_choices):
                    all_choice += chr(choice_index + 65) + ". " + choice["text"] + "\n"
                    if choice["text"] == answer_key_shuffled["text"]:
                        answer_key_shuffled = {
                            "tag": chr(choice_index + 65),
                            "text": choice["text"]
                        }
                query_list_choiceshuffled.append({
                    "query": build_query(article_id, stem, all_choice),
                    "answer_key": answer_key_shuffled
                })

    indices = list(range(len(query_list_choiceunshuffled)))
    random.shuffle(indices)
    # 问题打乱顺序
    query_list_choiceunshuffled_shuffled = [query_list_choiceunshuffled[i] for i in indices]
    query_list_choiceshuffled_shuffled = [query_list_choiceshuffled[i] for i in indices]
            
    total_word_count = sum(data["article_wordcounts"] for data in article_list)
    return {
        "ELC": ELC_str, 
        "query_list": query_list_choiceunshuffled_shuffled,
        "normal_article_count": len(normal_article),
        "noise_article_count": len(noise_article),
        "normal_para_count": len(normal_para),
        "noise_para_count": len(noise_para),
        "normal_word_count": elc["filter"]["word_total_count"], 
        "noise_word_count": elc["unfilter"]["word_total_count"],
        "total_word_count": total_word_count
    }, {
        "ELC": ELC_str, 
        "query_list": query_list_choiceshuffled_shuffled,
        "normal_article_count": len(normal_article),
        "noise_article_count": len(noise_article),
        "normal_para_count": len(normal_para),
        "noise_para_count": len(noise_para),
        "normal_word_count": elc["filter"]["word_total_count"], 
        "noise_word_count": elc["unfilter"]["word_total_count"],
        "total_word_count": total_word_count
    }

def select_need_string(ELC_benchmark_cu, ELC_benchmark_cs, need_strings):
    paired_list = list(zip(ELC_benchmark_cu, ELC_benchmark_cs))
    random_sampled_pairs = random.sample(paired_list, need_strings)
    random_list1, random_list2 = zip(*random_sampled_pairs)
    random_list1 = list(random_list1)
    random_list2 = list(random_list2)
    return random_list1, random_list2

def save_benchmark(ELC_benchmark, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with jsonlines.open(save_path, "w") as writer:
        writer.write_all(ELC_benchmark)

if __name__ == "__main__":
    # 文件路径示例
    file_path = './dataset'
    # 最终每个数据集需要的测试数据
    need_strings = 3

    Print_Flag = True
    shuffle_choice = True
    # "NMET", "CET", "PGEE", "TOEFL TPO", "TOEFL", "ALL"
    # "1","2","3","4", "ALL"
    # 1,2,4,8,16,32,64,128,256
    for dataset_name in ["NMET", "CET", "PGEE", "TOEFL TPO"]:
        for category in ["ALL"]:
            for index, word_limit in enumerate([32,256]):
                data_list = []

                # 1000 500
                required_strings = 200

                lower_limit = 0.1 + word_limit * 0.0002
                up_limit = -0.06 - word_limit * 0.00004
                next_pos_chance = 0.65
                jump_pos_cnt = 7 - index

                for file in os.listdir(file_path):
                    data_list += load_jsonl_data(os.path.join(file_path, file))
                print("load data done")

                random.shuffle(data_list)

                filtered_data_list, unfiltered_data_list = filter_data(data_list, args={
                    "dataset_name": dataset_name,
                    "category": category
                })
                ELC_choose = search_ELC_article(word_limit, lower_limit, up_limit, required_strings, next_pos_chance, jump_pos_cnt, filtered_data_list, unfiltered_data_list)
                ELC_benchmark_cu = []
                ELC_benchmark_cs = []
                # 构建超长文本评测数据
                for elc in tqdm(ELC_choose, desc="Construct Process"):
                    ELC_Data_cu, ELC_Data_cs = construct_ELC_data(elc, Print_Flag, shuffle_choice)
                    ELC_benchmark_cu.append(ELC_Data_cu)
                    ELC_benchmark_cs.append(ELC_Data_cs)

                os.makedirs("./output", exist_ok = True)
                save_file_name = "{}k_{}_{}.jsonl".format(word_limit, dataset_name, "ALL" if category == "ALL" else QUESTION_TYPEMAP[category])
                random_ELC_benchmark_cu, random_ELC_benchmark_cs = select_need_string(ELC_benchmark_cu, ELC_benchmark_cs, need_strings)
                
                save_benchmark(random_ELC_benchmark_cs, os.path.join("output_shuffled", save_file_name))
                save_benchmark(random_ELC_benchmark_cu, os.path.join("output_unshuffled", save_file_name))
                print("======", save_file_name, "======")
                time.sleep(3)