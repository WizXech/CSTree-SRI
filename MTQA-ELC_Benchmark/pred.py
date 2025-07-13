import os
import re
import random
import torch
import jsonlines
import numpy as np
from datetime import datetime
from tqdm import tqdm

from model import load_model_and_tokenizer, post_process, load_model_maxlen
from config import parse_args
from multiQA_prompt import DEAFAULT_DATASET_PROMPT, TREESRI_DATASET_PROMPT

from treesri_main import TreeSRI
from TinyRAG import RAG_example
from Longagent import main_NeedleInAHaystack_PLUS_test

gpu_ids = [0,1,2,3,4,5,6,7]
os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, gpu_ids))

def seed_everything(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.cuda.manual_seed_all(seed)

def get_pred(data_list, max_length, max_gen, prompt_format, dataset_name, device, model, tokenizer, model_name):

    if "TreeSRI" in model_name:
        treesri = TreeSRI(chunk_size = 512, per_chunk = 6)

    save_data_list = data_list
    for data_index, data in tqdm(enumerate(data_list), total=len(data_list), desc="{} Processing".format(dataset_name)):
        if "TreeSRI" in model_name:
            treesri.clean_cache()
            treesri.preprocess(ELC = data["ELC"], flag = True)

        start_time = datetime.now()
        # Maintain conversation history (context for each query)
        dialog_history = ""
        # Process each query one by one
        for query_index, query_info in tqdm(enumerate(data["query_list"]), total=len(data["query_list"]), desc="ELC_{} Query Processing".format(data_index)):
            if query_index >= 100: break
            # initial
            response = ""
            save_data_list[data_index]["query_list"][query_index]["model_raw_output"] = ""
            if "RAG" in model_name:
                response = RAG_example.get_response(model, tokenizer, data["ELC"], query_info["query"])
            elif "LongAgent" in model_name:
                response = main_NeedleInAHaystack_PLUS_test.get_longAgent_response(data["ELC"], query_info["query"])
            elif "TreeSRI" in model_name:
                response = treesri.inference(query_info["query"])
            else:
                history_context = dialog_history + "\n" + query_info["query"] # Splicing historical dialogues into a text
                # dataset2prompt
                prompt = prompt_format.format(
                    ELC=data["ELC"],
                    queries=history_context
                )
                tokenized_prompt = tokenizer(prompt, truncation=True, return_tensors="pt").to(device)

                # Handling situations that exceed the maximum length
                if len(tokenized_prompt['input_ids'][0]) > max_length:
                    half = max_length // 2
                    prompt = tokenizer.decode(tokenized_prompt['input_ids'][0][:half], skip_special_tokens=True) + \
                            tokenizer.decode(tokenized_prompt['input_ids'][0][-half:], skip_special_tokens=True)
                    tokenized_prompt = tokenizer(prompt, truncation=True, return_tensors="pt").to(device)
                try:
                    output = model.generate(
                        **tokenized_prompt,
                        max_new_tokens=max_gen,
                        num_beams=1,
                        do_sample=False,
                        temperature=1.0,
                    )[0]
                    response = tokenizer.decode(output[len(tokenized_prompt['input_ids'][0]):], skip_special_tokens=True)
                    # Response added to history
                    dialog_history += "{}\nModel_Output: {}\n".format(query_info["query"], response)
                except Exception as e:
                    print(f"Error occurred while generating model output: {e}")
            
            response = post_process(response, model_name).strip()
            save_data_list[data_index]["query_list"][query_index]["model_raw_output"] = response

        end_time = datetime.now()
        run_time = end_time - start_time
        save_data_list[data_index]["run_time"] = run_time.total_seconds()
        print("")
    return save_data_list

def save_data(file_path, data_list):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with jsonlines.open(file_path, "w") as writer:
        writer.write_all(data_list)

# Retrieve all file names and sort them by numerical part
def get_numeric_prefix(file_name):
    match = re.match(r"(\d+)(k)_.*\.jsonl", file_name)
    if match:
        return int(match.group(1))
    return float('inf')

if __name__ == '__main__':
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    seed_everything(52)
    args = parse_args()

    model_name = args.model
    max_length = load_model_maxlen(model_name)
    
    # Call the functions in the local model.py file to load the model
    model, tokenizer = load_model_and_tokenizer(model_name, device)
    
    evaluate_dataset_path = "./ELCdataset_{}".format(args.shuffled_choice)
    # Start reading files from 1k
    for file in sorted(os.listdir(evaluate_dataset_path),key=get_numeric_prefix):
        if file.endswith(".jsonl"):
            dataset_name = file.split(".jsonl")[0]
            task_type = dataset_name.split("_")[-1]
            print("Evaluate", dataset_name, "Processing")
            
            output_path = "model_output/{}/{}/{}.jsonl".format(args.shuffled_choice, model_name, dataset_name)

            if os.path.isfile(output_path) == True:
                continue
            
            data_list = []
            with jsonlines.open(os.path.join(evaluate_dataset_path, file), "r") as reader:
                data_list = [line for line in reader]
            if "TreeSRI" in model_name:
                prompt_format = TREESRI_DATASET_PROMPT[task_type]
            else:
                prompt_format = DEAFAULT_DATASET_PROMPT[task_type]
            max_gen = 50
            save_data_list = get_pred(data_list, max_length, max_gen, prompt_format, dataset_name, device, model, tokenizer, model_name)
            save_data(output_path, save_data_list)