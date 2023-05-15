from gpt4free import you, forefront, theb
import toml
import os
import sys
from flask import Flask, Response, request, stream_with_context
from flask_sock import Sock
# CORS
from flask_cors import CORS
import json
import random
import datetime
import re
import codecs
import poe

app = Flask(__name__)
sock = Sock(app)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "headers": ["Content-Type"],
        "max_age": 86400,
    }
})
sock.init_app(app)
client_dict = {}

config = toml.load('config.toml')
print(config)

poe_client = poe.Client(config['poe_token'][0])

def decode_unicode(text):
    pattern = re.compile(r'\\u([0-9a-fA-F]{4})')
    return pattern.sub(lambda m: codecs.decode(m.group(0), 'unicode_escape'), text)


def convert_json_form(content):
    dic = {
        "id":"chatcmpl-" + random.randbytes(8).hex(),
        "object":"chat.completion",
        "created":str(datetime.datetime.now().timestamp()),
        "model":"gpt-3.5-turbo-0301",
        "choices":[
                {"message":{"role":"assistant","content":decode_unicode(content)},
                "finish_reason":"stop","index":0
                }
            ]
        }
    return json.dumps(dic, ensure_ascii=False)

def process_context(messages):
    chat = []
    for i in range(len(messages)):
        if i % 2 == 0 and i < len(messages) - 1:
            chat.append({"question": messages[i]['content'], "answer": messages[i+1]['content']})
    return chat

def get_answer(prompt):
    for token in theb.Completion.create(
        prompt=prompt,
    ):
        yield token

def get_content_to_send(messages):
    leading_map = {
        "system": "Instructions",
        "user": "User",
        "assistant": "Assistant"
    }
    content = ""
    simulate_roles = False
    simulate_roles_conf = 2
    if simulate_roles_conf == 1:
        simulate_roles = True
    elif simulate_roles_conf == 2:
        if (len(messages) == 1 and messages[0]['role'] == "user") or \
                (len(messages) == 1 and messages[0]['role'] == "system") or \
                (len(messages) == 2 and messages[0]['role'] == "system" and messages[1]['role'] == "user"):
            simulate_roles = False
        else:
            simulate_roles = True
    for message in messages:
        if simulate_roles:
            content += "||>" + leading_map[message["role"]] + ":\n" + message["content"] + "\n"
        else:
            content += message["content"] + "\n"
    if simulate_roles:
        content += "||>Assistant:\n"
    return content


@app.route('/v1/chat/poe', methods=['GET', 'POST', 'OPTIONS'])
def test_chat():
    if request.method == 'OPTIONS':
        print('OPTIONS')
        return 'ok'
    content = get_content_to_send(request.json['messages'])
    def stream():
        for chunk in poe_client.send_message("capybara", content, with_chat_break=True):
            print(chunk)
            text = chunk["text_new"]
            if text:
                print("data: %s\n\n" % text.replace("\n","<br>"))
                dic = {
                    "choices":[
                        {
                            "index":0,
                            "delta": {
                                "role": "assistant",
                                "content": text.replace("\n","<br>")
                            }
                        }
                    ],
                    "created":str(datetime.datetime.now().timestamp()),
                    "id":"chatcmpl-" + random.randbytes(8).hex(),
                    "model":"gpt-3.5-turbo-0301",
                    "object":"chat.completion.chunk",
                }
                yield "data: %s\n\n" % json.dumps(dic, ensure_ascii=False)
            else:
                yield "[DONE]"
    return Response(stream(),mimetype="text/event-stream")

@app.route('/v1/chat/you', methods=['GET', 'POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        print('OPTIONS')
        return 'ok'
    content = request.json['messages'][-1]['content']
    response = you.Completion.create(
        prompt=content,
        chat=process_context(request.json['messages'])
    )

    return convert_json_form(response.text)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
