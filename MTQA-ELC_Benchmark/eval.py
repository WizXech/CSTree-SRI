import os
import re
import json
import math
import numpy as np
import jsonlines

from config import parse_args

def check_answer(model_raw_output, answer_key):
    match = re.search(r'\b[A-F]\b', model_raw_output)
    if match and match.group() == answer_key["tag"]:
        return 1
    else:
        answer_length = len(answer_key["text"])
        extract_answers = model_raw_output[:min(answer_length + 15, len(model_raw_output))] + model_raw_output[max(0, len(model_raw_output) - answer_length - 15):]
        if answer_key["text"] in extract_answers:
            return 1
        return 0

def extract_parts(input_str):
    article_id = input_str.split("Please choose the correct answer from options ")[0].split("This is a question about article ")[1]
    question = input_str.split(" below to answer the question. ")[1]

    match = re.match(r"([A-Za-z\s]+)(\d+)", article_id)
    dataset_name, id = match.group(1).strip(), match.group(2)
    return dataset_name, id, question

def get_human_performance(original_dataset, dataset_name, id, question):
    dataset = original_dataset[dataset_name]
    for data in dataset:
        if data["id"] != dataset_name + "_" + id:
            continue
        for dataset_question in data["questions"]:
            stem = dataset_question["question_stem"]
            if stem in question:
                return dataset_question["human_performance"]

def calculate_accuracy(data_list, original_dataset, k = 1):
    correct_count = 0
    total_count = 0
    total_time = 0.0
    
    total_f = 0.0
    for data in data_list:
        total_time += data["run_time"]
        for query_index, query in enumerate(data["query_list"]):
            if query_index >= 100: break
            total_count += 1
            correct = check_answer(query["model_raw_output"], query["answer_key"])
            correct_count += correct

            dataset_name, id, question = extract_parts(query["query"])
            human_performance = get_human_performance(original_dataset, dataset_name, id, question)
            f = calc_f(human_performance, correct, k)
            total_f += f

    accuracy = correct_count / total_count * 100
    average_time = total_time / total_count
    w_score = total_f / total_count * 100
    return correct_count, total_count, accuracy, average_time, w_score

def calc_ETScore(accuracy, average_time, K = 100, beta = 0.002):
    return accuracy * 0.01 * K / (1 + beta * average_time)

def calc_f(human_performance, correct, k):
    a = 1 if correct == 1 else -1
    p = float(human_performance.split("%")[0]) / 100
    return math.exp(k * 0.5) + a * math.exp(k * (0.5 - p) * a)

def save_file(file_path, metric_data):
    os.makedirs(file_path, exist_ok=True)
    
    result_path = os.path.join(file_path, "result.json")
    with open(result_path, "w", encoding="utf-8") as file:
        json.dump(metric_data, file, ensure_ascii=False, indent=4)

    print("Result save in: {}".format(result_path))
    print("=" * 50)

if __name__ == '__main__':
    args = parse_args()

    original_dataset = {}
    for file in os.listdir("./dataset"):
        if file.endswith(".jsonl"):
            with jsonlines.open(os.path.join("./dataset", file), "r") as reader:
                original_dataset[file.split(".")[0]] = [line for line in reader]
            
    for shuffled_choice in ["shuffled", "unshuffled"]:
        if args.shuffled_choice != None and args.shuffled_choice != shuffled_choice: continue
        model_output_path = "./model_output/{}".format(shuffled_choice)
        metric_output_path = "./metric/{}".format(shuffled_choice)

        for model_name in os.listdir(model_output_path):
            if args.model != None and model_name != args.model:
                continue

            metric_data = {}
            metric_data["model_name"] = model_name
            input_path = os.path.join(model_output_path, model_name)
            output_path = os.path.join(metric_output_path, model_name)

            for file in sorted(os.listdir(input_path)):
                if file.endswith(".jsonl"):
                    filename = file.split(".jsonl")[0]
                    data_list = []
                    with jsonlines.open(os.path.join(input_path, file), "r") as reader:
                        data_list = [line for line in reader]

                    correct_count, total_count, accuracy, average_time, w_score  = calculate_accuracy(data_list, original_dataset)
                    ETScore = calc_ETScore(accuracy, average_time)
                    
                    metric_data[filename] = {
                        "correct_count": correct_count,
                        "total_count": total_count,
                        "accuracy": f"{accuracy:.2f}%",
                        "average_time": f"{average_time:.4f}",
                        "ETScore": f"{ETScore:.2f}",
                        "w_score": w_score
                    }
                    filename = "".join(filename.split(" "))
                    
            LENGTH_OVERALL = 0.0
            LENGTH_Count = 0
            TYPE_OVERALL = 0.0
            TYPE_Count = 0
            TASK_OVERALL = 0.0
            TASK_Count = 0
            for file in sorted(os.listdir(input_path)):
                if file.endswith(".jsonl"):
                    filename = file.split(".jsonl")[0]
                    length = filename.split("_")[0]
                    type = filename.split("_")[1]
                    task = filename.split("_")[2]
                    if length in ["32k", "64k", "128k", "256k"] and type == "ALL" and task == "ALL":
                        LENGTH_OVERALL += metric_data[filename]["w_score"]
                        LENGTH_Count += 1
                    elif length in ["32k", "256k"] and type in ["NMET", "CET", "PGEE", "TOEFL TPO"] and task == "ALL":
                        TYPE_OVERALL += metric_data[filename]["w_score"]
                        TYPE_Count += 1
                    elif length in ["32k", "256k"] and type == "ALL" and task in ["Detail Comprehension", "Main Idea & Perspective", "Inference & Judgment", "Semantic & Reference"]:
                        TASK_OVERALL += metric_data[filename]["w_score"] 
                        TASK_Count += 1
            if LENGTH_Count != 0:
                LENGTH_OVERALL /= LENGTH_Count
            if TYPE_Count != 0:
                TYPE_OVERALL /= TYPE_Count
            if TASK_Count != 0:
                TASK_OVERALL /= TASK_Count
            metric_data["OVERALL"] = {
                "LENGTH_OVERALL": LENGTH_OVERALL,
                "LENGTH_Count": LENGTH_Count,
                "TYPE_OVERALL": TYPE_OVERALL,
                "TYPE_Count": TYPE_Count,
                "TASK_OVERALL": TASK_OVERALL,
                "TASK_Count": TASK_Count
            }
                    
            save_file(output_path, metric_data)