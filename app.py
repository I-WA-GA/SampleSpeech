from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import re
import sys
import queue
from google.cloud import speech
import pyaudio
from six.moves import queue

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')  # 'gevent' を指定

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')  # ここで非同期モードを指定

# 環境変数 GOOGLE_APPLICATION_CREDENTIALS にキーのパスを設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "googleAPI_01.json"

# オーディオ録音のパラメータ
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# MicrophoneStream クラスは以前のまま

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_listening')
def handle_start_listening():
    language_code = "ja-JP"
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            emit('response', {'data': transcript})  # テキストをブラウザに送信

            if result.is_final:
                break

if __name__ == "__main__":
    socketio.run(app, debug=True)
