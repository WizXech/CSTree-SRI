import time, json, requests

def ask_openai(messages):
    url = '***'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': '***'
    }
    data = {
        "model": "***",
        "messages": messages
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(e)
        return ask_openai(messages)

def ask_gpt(str):
    messages = [
        {
            "role": "system",
            "content": "You are a professional translation expert, and you need to translate the input into Chinese"
        },
        {
            "role": "user",
            "content": "Please translate the following English into Chinese: " + str
        }
    ]
    return ask_openai(messages)


if __name__ == "__main__":
    print(ask_gpt("Hello, world!"))