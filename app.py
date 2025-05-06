from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import csv
import ijson
import html

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
        file = request.files.get('json_file')
        if file and file.filename.endswith('.json'):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            try:
                with open(path, 'rb') as f:
                    # Parse Skype-exported messages
                    parser = ijson.items(f, 'conversations.item.messages.item')
                    for msg in parser:
                        chat_messages.append({
                            "timestamp": msg.get("originalarrivaltime", "N/A"),
                            "sender": msg.get("from", "Unknown"),
                            "text": html.escape(msg.get("content", ""))
                        })
                        # Limit to 5000 for performance
                        if len(chat_messages) >= 5000:
                            break

                # Log sample output to Render log for debugging
                print("Parsed sample messages:", chat_messages[:3])

            except Exception as e:
                print("Error parsing JSON:", e)
                return "Error parsing the uploaded file.", 500

    return render_template('index.html', messages=chat_messages)

@app.route('/download/<filetype>')
def download(filetype):
    if not chat_messages:
        return redirect(url_for('index'))

    file_path = os.path.join(DOWNLOAD_FOLDER, f'chatlog.{filetype}')

    try:
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

    except Exception as e:
        print("File writing error:", e)
        return "Failed to generate file", 500

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
