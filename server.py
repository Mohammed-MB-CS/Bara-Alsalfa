"""PC side: serves the word lists to the phone over Wi-Fi.

Run it:  python server.py
Test it: open http://localhost:8000/data in a browser
"""

import json
import pathlib
import socket

import uvicorn
from fastapi import FastAPI

WORDS_FILE = pathlib.Path(__file__).with_name("words.json")

app = FastAPI()


def read_words():
    # Read the file on every request, so editing words.json shows up
    # without restarting the server.
    return json.loads(WORDS_FILE.read_text(encoding="utf-8"))


@app.get("/version")
def version():
    # Tiny answer, used by the phone to decide if it needs the big one.
    return {"version": read_words()["version"]}


@app.get("/data")
def data():
    # The full word list.
    return read_words()


def my_ip():
    # Trick to find this PC's address on the Wi-Fi network.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # nothing is sent, it just picks a route
        return s.getsockname()[0]
    finally:
        s.close()


if __name__ == "__main__":
    print(f"PC address for the phone:  {my_ip()}:8000")
    print("Stop the server with Ctrl+C")
    # 0.0.0.0 = listen on all network cards, so the phone can reach us.
    uvicorn.run(app, host="0.0.0.0", port=8000)
