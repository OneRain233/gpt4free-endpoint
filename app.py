from gpt4free import you
import toml
import os
import sys
from flask import Flask, request
from flask_sock import Sock
# CORS
from flask_cors import CORS
import json
import random
import datetime
import re
import codecs

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



@app.route('/v1/chat/completions', methods=['GET', 'POST', 'OPTIONS'])
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
