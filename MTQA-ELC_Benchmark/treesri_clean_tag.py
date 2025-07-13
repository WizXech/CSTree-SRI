import os
import re
import json
import jsonlines
from tqdm import tqdm

def generate_label(task_type, tag):
    return "{}-{}".format(task_type, tag)

def check_restrict(task_type, decision_token_original):
    decision_token = ""
    if task_type.endswith("Retr"):
        pattern_yes = r'judg(e)?ment(\s)*:(\s)*(\[)?yes(\])?[a-z,.:\s\.\n]*$'
        pattern_no = r'judg(e)?ment(\s)*:(\s)*(\[)?no(\])?[a-z,.:\s\.\n]*$'
        if "need retrieval?: [yes]" in decision_token_original or re.search(pattern_yes, decision_token_original):
            decision_token = generate_label(task_type, "YES")
            return -1, decision_token
        if "need retrieval?: [no]" in decision_token_original or re.search(pattern_no, decision_token_original):
            decision_token = generate_label(task_type, "NO")
            return -1, decision_token
        pattern_yes = r'^(\s)*(\[)?yes(\])?[,.:\s\.\n]*$'
        pattern_no = r'^(\s)*(\[)?no(\])?[,.:\s\.\n]*$'
        if re.search(pattern_yes, decision_token_original):
            decision_token = generate_label(task_type, "YES")
            return -1, decision_token
        if re.search(pattern_no, decision_token_original):
            decision_token = generate_label(task_type, "NO")
            return -1, decision_token

    elif task_type == "FitScore":
        pattern_irrelevant = r'judg(e)?ment(\s)*:(\s)*(\[)?ir(re)?levant(\])?[a-z,.:\s\.\n]*$'
        pattern_relevant = r'judg(e)?ment(\s)*:(\s)*(\[)?r(e)?levant(\])?[a-z,.:\s\.\n]*$'
        if re.search(pattern_irrelevant, decision_token_original):
            decision_token = generate_label(task_type, "0")
            return -1, decision_token
        if re.search(pattern_relevant, decision_token_original):
            decision_token = generate_label(task_type, "1")
            return -1, decision_token
        
        pattern_irrelevant = r'^(\s)*(\[)?ir(re)?levant(\])?[,.:\s\.\n]*$'
        pattern_relevant = r'^(\s)*(\[)?r(e)?levant(\])?[,.:\s\.\n]*$'
        if re.search(pattern_irrelevant, decision_token_original):
            decision_token = generate_label(task_type, "0")
            return -1, decision_token
        if re.search(pattern_relevant, decision_token_original):
            decision_token = generate_label(task_type, "1")
            return -1, decision_token

    elif task_type == "AidScore":
        for i in range(1, 4):
            pattern = fr'judg(e)?ment(\s)*:(\s)*(\[)?{i}(\])?[a-z,.:\s\.\n]*$'
            if re.search(pattern, decision_token_original):
                decision_token = generate_label(task_type, str(i))
                return -1, decision_token
            
    elif task_type == "CorrectScore":
        for i in range(1, 6):
            pattern = fr'score(\s)*:(\s)*(\[)?{i}(\])?[a-z,.:\s\.\n]*$'
            if re.search(pattern, decision_token_original):
                decision_token = generate_label(task_type, str(i))
                return -1, decision_token
            
    if task_type.endswith("Score"):
        for i in range(1, 6):
            pattern = fr'\[[\s]*{i}[\s]*-[a-z\s]*\][a-z,.:\s\.\n]*$'
            pattern_strict = fr'^(\s)*(\[)?{i}(\])?[a-z,.:\s\.\n]*$'
            if re.search(pattern, decision_token_original) or re.search(pattern_strict, decision_token_original):
                decision_token = generate_label(task_type, str(i))
                return -1, decision_token
            
    return 0, decision_token

def check(cnt, task_type, decision_token_original):
    decision_token = ""
    if task_type.endswith("Retr"):
        yes_bool = "[yes]" in decision_token_original or "yes" == decision_token_original or "[yes]" == decision_token_original or "[maybe]" == decision_token_original
        no_bool = "[no]" in decision_token_original or "no" == decision_token_original or "[no]" == decision_token_original
        if yes_bool and not no_bool:
            decision_token = generate_label(task_type, "YES")
            cnt += 1
        if not yes_bool and no_bool:
            decision_token = generate_label(task_type, "NO")
            cnt += 1

    elif task_type == "FitScore":
        irrelevant_bool = "[irrelevant]" in decision_token_original or "[irlevant]" in decision_token_original
        relevant_bool = "[relevant]" in decision_token_original or "[rlevant]" in decision_token_original or "[partially relevant]" in decision_token_original

        if irrelevant_bool and not relevant_bool:
            decision_token = generate_label(task_type, "0")
            cnt += 1
        if not irrelevant_bool and relevant_bool:
            decision_token = generate_label(task_type, "1")
            cnt += 1

    elif task_type == "AidScore":
        for i in range(1, 4):
            if "[{}]".format(str(i)) in decision_token_original:
                checkin = False
                for j in range(1, 4):
                    if j != i and "[{}]".format(str(j)) in decision_token_original:
                        checkin == True
                        break
                if checkin == False:
                    decision_token = generate_label(task_type, str(i))
                    cnt += 1
            
    elif task_type == "CorrectScore":
        for i in range(1, 6):
            if "[{}]".format(str(i)) in decision_token_original:
                checkin = False
                for j in range(1, 6):
                    if j != i and "[{}]".format(str(j)) in decision_token_original:
                        checkin == True
                        break
                if checkin == False:
                    decision_token = generate_label(task_type, str(i))
                    cnt += 1
    return cnt, decision_token

def load_data(data_dir, regenerate_cnt = 0):
    data_list = []
    for dir in tqdm(os.listdir(data_dir), desc="Loading Processing"):
        path = os.path.join(data_dir, dir)
        for file in os.listdir(path):
            if regenerate_cnt == 0 or file.endswith("_{}.jsonl".format(regenerate_cnt)):
                with jsonlines.open(os.path.join(path, file), 'r') as reader:
                    for example in reader:
                        example["task_type"] = dir
                        data_list.append(example)

    error_data_list = []
    clean_data_list = []
    for index, example in tqdm(enumerate(data_list), desc="Clean Data Processing"):
        task_type = example["task_type"]
        cnt = 0
        cnt, decision_token = check_restrict(task_type, example["decision_token"].lower())
        if cnt == 0:
            cnt, decision_token = check(cnt, task_type, example["decision_token"].lower())
        
        if cnt == 0:
            cnt, decision_token = check_restrict(task_type, example["raw_output"].lower())
            if cnt == 0:
                cnt, decision_token = check(cnt, task_type, example["raw_output"].lower())

        if cnt > 1 or cnt == 0:
            error_data_list.append(data_list[index])
        else:
            data_list[index]["decision_token"] = decision_token
            clean_data_list.append(data_list[index])

    print("total data: {}".format(len(data_list)))
    print("error_data data: {}".format(len(error_data_list)))
    print("clean_data data: {}".format(len(clean_data_list)))

    print("equal: ", len(data_list) == (len(clean_data_list) + len(error_data_list)))

    return clean_data_list, error_data_list


if __name__ == "__main__":
    data_dir = "./tag_data"
    clean_output_dir = "./tag_data_cleaned_9"
    error_output_dir = "./tag_data_error_9"
    regenerate_cnt = 9

    clean_data_list, error_data_list = load_data(data_dir, regenerate_cnt)