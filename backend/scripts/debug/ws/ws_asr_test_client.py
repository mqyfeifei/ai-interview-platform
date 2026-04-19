"""
WebSocket ASR test client.
Usage: run this script to stream a WAV file in small PCM chunks to the server WebSocket endpoint.
It connects to ws://localhost:5000/socket.io/?EIO=4&transport=websocket (Socket.IO protocol).
This script uses python-socketio client to speak with Flask-SocketIO server.

Note: for microphone live capture you'd replace the file read with sounddevice stream and send frames.
"""

import sys
import time
import base64
import wave
import argparse
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('[CLIENT] connected to server')

@sio.event
def disconnect():
    print('[CLIENT] disconnected from server')

@sio.on('asr_partial')
def on_partial(data):
    print(f"[CLIENT] partial seq={data.get('seq')} text={data.get('text')} elapsed_ms={data.get('elapsed_ms')}")

@sio.on('asr_error')
def on_error(data):
    print('[CLIENT] server error:', data)


def stream_wav(path, chunk_ms=100):
    # chunk_ms milliseconds per chunk (默认100ms)
    with wave.open(path, 'rb') as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        bytes_per_ms = rate * channels * sampwidth / 1000.0
        chunk_bytes = int(bytes_per_ms * chunk_ms)
        voice_id = str(int(time.time() * 1000))
        seq = 0
        while True:
            frames = wf.readframes(chunk_bytes // sampwidth)
            if not frames:
                # send final empty packet with is_end=1
                sio.emit('audio_chunk', {
                    'voice_id': voice_id, 'seq': seq, 'chunk_b64': '', 'is_end': 1
                })
                break
            b64 = base64.b64encode(frames).decode('utf-8')
            sio.emit('audio_chunk', {'voice_id': voice_id, 'seq': seq, 'chunk_b64': b64, 'is_end': 0})
            seq += 1
            time.sleep(chunk_ms/1000.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('wav', help='path to wav file')
    parser.add_argument('--url', default='http://localhost:5000', help='server base url')
    args = parser.parse_args()

    server = args.url
    print('[CLIENT] connecting to', server)
    sio.connect(server)
    try:
        stream_wav(args.wav, chunk_ms=120)
        # wait a little for server to finish
        time.sleep(2)
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()
