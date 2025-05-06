from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import csv
import traceback
import ijson  # streaming JSON parser

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB max upload

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

                with open(path, 'rb') as f:  # use binary mode for ijson
                    for conv in ijson.items(f, 'conversations.item'):
                        for msg in conv.get("messages", []):
                            chat_messages.append({
                                "timestamp": msg.get("timestamp", ""),
                                "sender": msg.get("from", "Unknown"),
                                "text": msg.get("text", "")
                            })

        except Exception as e:
            print("❌ Error while processing the uploaded file:")
            print(traceback.format_exc())
            return f"<h2>Error processing file:</h2><pre>{e}</pre>", 500

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

if __name__ == '__main__':
    app.run(debug=True)
