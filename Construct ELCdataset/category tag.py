import os
import re
import jsonlines
from openai_gpt import ask_gpt

dataset_name = ["NMET", "CET", "PGEE", "TOEFL"]
question_typemap = {
    "1": "Detail Comprehension",
    "2": "Main Idea & Perspective",
    "3": "Inference & Judgment",
    "4": "Semantic & Reference",
    "5": "Paragraph Sequencing",
    "6": "Search & Match"
}

def open_file(file_path):
    data_list = []
    with jsonlines.open(file_path, "r") as reader:
        for line in reader:
            data_list.append(line)
    return data_list

def save_file(data_list, file_path):
    with jsonlines.open(file_path, "w") as writer:
        writer.write_all(data_list)


def main(format_data_list):
    for index in range(len(format_data_list)):
        data = format_data_list[index]
        questions = data["questions"]
        for question_index, question in enumerate(questions):
            if "category" in question:
                continue

            stem = question["question_stem"]
            choices = question["choices"]
            all_choice = ""
            for choice in choices:
                all_choice += choice["tag"] + ". " + choice["text"] + "\n"
            print("")
            print("{} 中的 第 {} 题".format(data["id"], question_index))
            print(stem)
            print(all_choice)

            fanyi_stem = ask_gpt(stem)
            print("=========LLM translate=========")
            print(fanyi_stem)
            print("=========translate done=========")
            
            category = input("1-细节 2-主旨 3-推理 4-指代，请输入1234，代表某一题，输入回车即可保存并断开程序\n")
            if category in question_typemap.keys():
                format_data_list[index]["questions"][question_index]["category"] = question_typemap[category]
            else:
                return True, format_data_list
    return False, format_data_list

if __name__ == "__main__":
    format_file_path = "./dataset copy"

    data_list = []
    for file in os.listdir(format_file_path):
        file_path = os.path.join(format_file_path, file)
        format_data_list = open_file(file_path)
        flag, data_list = main(format_data_list)
        save_file(data_list, file_path)
        if flag == True:
            break
    print("Done!!!!!!!!!")