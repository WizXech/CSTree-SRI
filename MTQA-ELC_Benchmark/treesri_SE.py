from treesri_openai_gpt import ask_gpt

class SummaryModel:
    def __init__(self):
        pass

    def generate(self, data_list):
        results = []
        for x in data_list:
            summary = ask_gpt(messages=[{
                "role": "user",
                "content": "Please summarize the content in concise sentences, while retaining logical locators (such as unique IDs that represent paragraphs) and key information. Content: {}".format(x)}])
            results.append(summary)
        return results