from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from bot.agents.graph import graphAgent
from bot.gateway.models import ChatRequest, ChatResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # local testing
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/info")
def info():
    return {"model": "acree-ai", "version": "1.0", "status": "active"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent = graphAgent()
    response = await agent.run(request.message)
    print(response)
    return ChatResponse(reply = response['result'], model=response['model'])

@app.post("/chat/stream")
async def chat_stream(user_input: str):
    agent = graphAgent()
    return StreamingResponse(
        agent.stream_run(user_input),
        media_type="text/event-stream"
    )

@app.websocket("/ws/stream/{session_id}")
async def ws_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    agent = graphAgent(session_id=session_id)
    try:
        while True:
            user_input = await websocket.receive_text()
            async for chunk in agent.stream_run(user_input):
                print(chunk)
                await websocket.send_text(chunk)
            await websocket.send_text("[DONE]")
    except Exception as e:
        await websocket.close()