from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI()

# Пользователи
users = {}

# Сообщения
messages = []

# Подключенные WebSocket клиенты
connections: Dict[str, WebSocket] = {}


class RegisterModel(BaseModel):
    username: str
    password: str


class MessageModel(BaseModel):
    sender: str
    receiver: str
    text: str


@app.get("/")
async def root():
    return {"status": "online"}


@app.post("/register")
async def register(user: RegisterModel):
    if user.username in users:
        return {"success": False, "error": "User exists"}

    users[user.username] = {
        "password": user.password
    }

    return {"success": True}


@app.post("/login")
async def login(user: RegisterModel):
    if user.username not in users:
        return {"success": False}

    if users[user.username]["password"] != user.password:
        return {"success": False}

    return {"success": True}


@app.post("/send")
async def send_message(msg: MessageModel):

    message = {
        "sender": msg.sender,
        "receiver": msg.receiver,
        "text": msg.text
    }

    messages.append(message)

    if msg.receiver in connections:
        await connections[msg.receiver].send_json(message)

    return {"success": True}


@app.get("/messages/{username}")
async def get_messages(username: str):

    result = []

    for msg in messages:
        if (
            msg["sender"] == username
            or
            msg["receiver"] == username
        ):
            result.append(msg)

    return result


@app.websocket("/ws/{username}")
async def websocket_endpoint(ws: WebSocket, username: str):

    await ws.accept()

    connections[username] = ws

    try:
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        if username in connections:
            del connections[username]
