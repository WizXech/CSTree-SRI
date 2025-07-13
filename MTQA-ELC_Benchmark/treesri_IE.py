from treesri_gpt4tag_prompt import PROMPT_DICT
from treesri_openai_gpt import ask_gpt
from treesri_clean_tag import check_restrict, check
    
class IntrospectiveModel:
    def __init__(self):
        pass
    
    def generate(self, task_types, inputs):
        if len(task_types) == 0 and len(inputs) == 0: return []

        if task_types[0] == "FitScore":
            retrieval_content = ""
            for index, input in enumerate(inputs):
                retrieval_content += "Evidence[{}] {}\n".format(index + 1, input["retrieval_content"])
            
            inputs[0]["retrieval_content"] = retrieval_content
            prompt = PROMPT_DICT[task_types[0]].format(**inputs[0])
            it_cnt = 0
            while True:
                it_cnt += 1
                if it_cnt > 3: break
                raw_output = ask_gpt(messages=[{
                    "role": "user",
                    "content": prompt
                }])
                decision_tokens = raw_output.split("@")
                if len(decision_tokens) != len(inputs): continue
                result = []
                for decision_token in decision_tokens:
                    decision_token = self.postprocess(task_types[0], decision_token)
                    if decision_token == "None":
                        continue
                    result.append(decision_token.split("-")[1])
                return result
            result = ["NO" for _ in range(len(inputs))]
            return result
        else:
            result = []
            for task_type, input in zip(task_types, inputs):
                prompt = PROMPT_DICT[task_type].format(**input)
                it_cnt = 0
                while True:
                    it_cnt += 1
                    if it_cnt > 2: break
                    raw_output = ask_gpt(messages=[{
                        "role": "user",
                        "content": prompt
                        }])
                    decision_token = self.postprocess(task_type, raw_output)
                    if decision_token != "None":
                        break
                if it_cnt > 2:
                    if task_type.endswith("ExtraRetr"):
                        result.append("YES")
                    elif task_type.endswith("Retr"):
                        result.append("NO")
                    else:
                        result.append("1")
                else:
                    result.append(decision_token.split("-")[1])
            return result

    def postprocess(self, task_type, raw_output):
        try:
            decision_token = ""
            if "\nExplanation:" in raw_output:
                explanation = raw_output.split("\nExplanation:")[1]
                if explanation[0] == " ":
                    explanation = explanation[1:]
                decision_token = raw_output.split("\nExplanation:")[0]
                if decision_token is None:
                    decision_token = ""
            else:
                decision_token = raw_output

            cnt = 0
            cnt, decision_token1 = check_restrict(task_type, decision_token.lower())
            if cnt == 0:
                cnt, decision_token1 = check(cnt, task_type, decision_token.lower())
            if cnt == 0:
                cnt, decision_token1 = check_restrict(task_type, raw_output.lower())
                if cnt == 0:
                    cnt, decision_token1 = check(cnt, task_type, raw_output.lower())

            if cnt > 1 or cnt == 0:
                return "None"
            else:
                return decision_token1
                
        except Exception:
            pass
        return "None"