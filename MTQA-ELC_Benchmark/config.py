import argparse

def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default=None, choices=[
        "TreeSRI",
        "Phi-3.5-mini-128k",
        "Phi-3-small-128k-instruct",
        "Mistral-7B-Instruct-v0.3",
        "Mistral-Nemo-Instruct-2407",
        "Llama-3.1-8B-Instruct",
        "GLM-4-9B-Chat",
        "GLM-4-9B-Chat-1M",
        "DeepSeek-V2-Lite-Chat",
        "Yi-1.5-9B-Chat-16K",
        "Qwen2.5-7B-Instruct",
        "RAG",
        "LongAgent"
    ], help="Fill in the names of all models to be evaluated")
    parser.add_argument('--gpus', type=str, default=None)
    parser.add_argument('--shuffled_choice', type=str, choices=[
        "shuffled",
        "unshuffled"
    ], default=None, help="Choose whether to shuffle the order of options for evaluation questions")
    return parser.parse_args(args)

# Define constants
K = 1000
SUB = 500
# Define a constant dictionary to store model names and their corresponding max_lengths
MODEL_MAX_LENGTHS = {
    "TreeSRI":1024*K - SUB,
    "Phi-3.5-mini-128k":128*K - SUB,
    "Phi-3-small-128k-instruct":128*K - SUB,
    "Mistral-7B-Instruct-v0.3":32*K - SUB,
    "Mistral-Nemo-Instruct-2407":128*K - SUB,
    "Llama-3.1-8B-Instruct":128*K - SUB,
    "GLM-4-9B-Chat":128*K - SUB,
    "GLM-4-9B-Chat-1M":1024*K - SUB,
    "DeepSeek-V2-Lite-Chat":32*K - SUB,
    "Yi-1.5-9B-Chat-16K":16*K - SUB,
    "Qwen2.5-7B-Instruct":128*K - SUB,
    "RAG": 1024*K - SUB,
    "LongAgent": 1024*K - SUB
}
MODEL_PATH = {
    "TreeSRI":"./modelPath/TreeSRI/",
    "Phi-3.5-mini-128k":"./modelPath/Phi/Phi-3.5-mini-instruct",
    "Phi-3-small-128k-instruct":"./modelPath/Phi/Phi-3-small-128k-instruct",
    "Mistral-7B-Instruct-v0.3":"./modelPath/Mistral/Mistral-7B-Instruct-v0.3",
    "Mistral-Nemo-Instruct-2407":"./modelPath/Mistral/Mistral-Nemo-Instruct-2407",
    "Llama-3.1-8B-Instruct":"./modelPath/Llama/Llama-3.1-8B-Instruct",
    "GLM-4-9B-Chat":"./modelPath/GLM/GLM-4-9B-Chat",
    "GLM-4-9B-Chat-1M":"./modelPath/GLM/GLM-4-9B-Chat-1M",
    "DeepSeek-V2-Lite-Chat":"./modelPath/DeepSeek/DeepSeek-V2-Lite-Chat",
    "Yi-1.5-9B-Chat-16K":"./modelPath/01Yi/Yi-1.5-9B-Chat-16K",
    "Qwen2.5-7B-Instruct":"./modelPath/Qwen/Qwen2.5-7B-Instruct",
    "RAG": "./modelPath/Llama/Llama-3.1-8B-Instruct",
    "LongAgent": ".."
}