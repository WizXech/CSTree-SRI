import torch

from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_flash_attn_monkey_patch import replace_llama_attn_with_flash_attn

class LLM:
    def __init__(self):
        # TODO need to update
        replace_llama_attn_with_flash_attn()
        
        self.tokenizer = AutoTokenizer.from_pretrained("./modelPath/Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained("./modelPath/Qwen/Qwen2.5-7B-Instruct", torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)
    def generate(self, prompt):
        input = self.tokenizer(prompt, truncation=False, return_tensors="pt").to('cuda')
        context_length = input.input_ids.shape[-1]
        output = self.model.generate(
                **input,
                num_beams=1,
                do_sample=False,
                temperature=1.0,
                max_new_tokens=50
            )[0]
        pred = self.tokenizer.decode(output[context_length:], skip_special_tokens=True)
        return pred