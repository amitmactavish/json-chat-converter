from flask import Flask, request, render_template, send_file, redirect, url_for
import traceback
import json
import os
import csv

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

chat_messages = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_messages
    chat_messages = []

    if request.method == 'POST':
        try:
            file = request.files['json_file']
            if file and file.filename.endswith('.json'):
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for conv in data.get("conversations", []):
                        for msg in conv.get("messages", []):
                            chat_messages.append({
                                "timestamp": msg.get("timestamp", ""),
                                "sender": msg.get("from", "Unknown"),
                                "text": msg.get("text", "")
                            })
        except Exception as e:
            return f"Error processing file: {e}", 500

    return render_template('index.html', messages=chat_messages)


@app.route('/download/<filetype>')
def download(filetype):
    if not chat_messages:
        return redirect(url_for('index'))

    file_path = os.path.join(DOWNLOAD_FOLDER, f'chatlog.{filetype}')

    if filetype == 'txt':
        with open(file_path, 'w', encoding='utf-8') as f:
            for msg in chat_messages:
                f.write(f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}\n")
                
    elif filetype == 'csv':
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "sender", "text"])
            writer.writeheader()
            writer.writerows(chat_messages)
    else:
        return "Unsupported file type", 400

    return send_file(file_path, as_attachment=True)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

