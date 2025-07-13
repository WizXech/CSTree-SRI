import time

from openai import OpenAI

def ask_gpt(messages):
    try:
        client = OpenAI(
            api_key="***",
            base_url="***"
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        if completion.choices[0].message.content == None:
            return ask_gpt(messages)
        return completion.choices[0].message.content
    except Exception as e:
        print(e)
        time.sleep(3)
        return ask_gpt(messages)