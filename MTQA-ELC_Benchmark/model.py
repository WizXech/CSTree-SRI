import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
# from llama_flash_attn_monkey_patch import replace_llama_attn_with_flash_attn

from config import MODEL_MAX_LENGTHS, MODEL_PATH

def load_model_maxlen(model_name):
    try:
        model2maxlen = MODEL_MAX_LENGTHS[model_name]
        return model2maxlen
    except Exception as e:
        print(f"Load Model MaxLen ERROR: {e}")
        return {}


def load_model_and_tokenizer(model_name, device):
    model = None
    tokenizer = None
    try:
        path = MODEL_PATH[model_name]
    except KeyError:
        print(f"ERROR: Model: '{model_name}' Not Found")
        path = None
    ###########################################TODO
    if "TreeSRI" in model_name:
        return "", ""
    elif "LongAgent" in model_name:
        return "", ""
    else:
        tokenizer = AutoTokenizer.from_pretrained(path, torch_dtype=torch.float16,trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.float16, device_map="auto",trust_remote_code=True)
        model.eval()
    ############################################
    return model, tokenizer

def build_chat(tokenizer, prompt,model_name,):
    ##Different input format requirements for different models.
    #if "llama2" in model_name:
    #    prompt = f"[INST]{prompt}[/INST]"
    #elif "xgen" in model_name:
    #   header = (
    #       "A chat between a curious human and an artificial intelligence assistant. "
    #        "The assistant gives helpful, detailed, and polite answers to the human's questions.\n\n"
    #   )
    #    prompt = header + f" ### Human: {prompt}\n###"
    #elif "internlm" in model_name:
    #    prompt = f"<|User|>:{prompt}<eoh>\n<|Bot|>:"
    #####
    return prompt

def post_process(response, model_name):
    return response
