import json
import os
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="USD/KRW AI Assistant", version="1.0.0")
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db = None

def db():
    global _db
    if _db is not None:
        return _db
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise HTTPException(503, "Firestore is not configured")
    try:
        info = json.loads(raw)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(info))
        _db = firestore.client()
        return _db
    except Exception as exc:
        raise HTTPException(503, f"Firestore initialization failed: {exc}") from exc

class DataInput(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    value: float = Field(gt=0, le=100000)
    memo: str = Field(default="", max_length=500)

class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None

class ConversationInput(BaseModel):
    messages: list[dict[str, Any]] = Field(min_length=1)

def records():
    docs = db().collection("data").stream()
    result = [{"id": d.id, **d.to_dict()} for d in docs]
    return sorted(result, key=lambda x: x.get("date", ""))

def summarize(rows):
    if not rows:
        return {"period": None, "count": 0, "metrics": {}, "trend": "데이터 없음"}
    values = [float(r["value"]) for r in rows]
    first, last = values[0], values[-1]
    change = ((last - first) / first * 100) if first else 0
    trend = "상승" if change > 0.1 else "하락" if change < -0.1 else "보합"
    return {
        "period": f'{rows[0]["date"]} ~ {rows[-1]["date"]}',
        "count": len(values),
        "metrics": {"average": round(sum(values) / len(values), 2), "max": max(values), "min": min(values), "latest": last, "change_percent": round(change, 2)},
        "trend": f"{trend} ({change:+.2f}%)",
        "unit": "KRW per USD",
    }

@app.get("/")
def root():
    return {"service": "USD/KRW AI Assistant", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/data")
def create_data(item: DataInput):
    ref = db().collection("data").document()
    ref.set(item.model_dump())
    return {"id": ref.id, **item.model_dump()}

@app.get("/api/data")
def list_data():
    return records()

@app.put("/api/data/{item_id}")
def update_data(item_id: str, item: DataInput):
    ref = db().collection("data").document(item_id)
    if not ref.get().exists:
        raise HTTPException(404, "Data record not found")
    ref.set(item.model_dump())
    return {"id": item_id, **item.model_dump()}

@app.delete("/api/data/{item_id}")
def delete_data(item_id: str):
    ref = db().collection("data").document(item_id)
    if not ref.get().exists:
        raise HTTPException(404, "Data record not found")
    ref.delete()
    return {"deleted": item_id}

@app.get("/api/data/summary")
def data_summary():
    return summarize(records())

@app.post("/api/conversations")
def save_conversation(item: ConversationInput):
    now = datetime.now(timezone.utc).isoformat()
    ref = db().collection("conversations").document()
    ref.set({"messages": item.messages, "updated_at": now, "created_at": now})
    return {"id": ref.id, "messages": item.messages, "updated_at": now}

@app.get("/api/conversations")
def list_conversations():
    docs = db().collection("conversations").order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    snap = db().collection("conversations").document(conversation_id).get()
    if not snap.exists:
        raise HTTPException(404, "Conversation not found")
    return {"id": snap.id, **snap.to_dict()}

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    ref = db().collection("conversations").document(conversation_id)
    if not ref.get().exists:
        raise HTTPException(404, "Conversation not found")
    ref.delete()
    return {"deleted": conversation_id}

@app.post("/api/chat")
def chat(item: ChatInput):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(503, "Gemini is not configured")
    summary = data_summary()
    system = (
        "당신은 USD/KRW 환율 데이터 분석 비서입니다. 환율은 USD 1달러당 KRW입니다. "
        "환율 상승은 달러 강세/원화 약세, 하락은 달러 약세/원화 강세로 설명하세요. "
        "제공된 요약만 근거로 답하고 데이터에 없는 사실을 만들어내지 마세요. "
        "미래 환율을 확정적으로 예측하지 말고 투자 조언으로 말하지 마세요. "
        f"데이터 요약: {json.dumps(summary, ensure_ascii=False)}"
    )
    conv_ref = db().collection("conversations").document(item.conversation_id) if item.conversation_id else db().collection("conversations").document()
    old = conv_ref.get().to_dict() if item.conversation_id else None
    messages = old.get("messages", []) if old else []
    messages += [{"role": "user", "content": item.message}]
    try:
        contents = [
            types.Content(
                role="user" if message.get("role") == "user" else "model",
                parts=[types.Part(text=message["content"])],
            )
            for message in messages
            if message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        ]
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30_000),
        )
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=350,
                ),
            )
        finally:
            client.close()
        answer = response.text or "답변을 만들지 못했습니다."
    except Exception as exc:
        raise HTTPException(502, f"Gemini request failed: {exc}") from exc
    messages.append({"role": "assistant", "content": answer})
    now = datetime.now(timezone.utc).isoformat()
    conv_ref.set({"messages": messages, "updated_at": now, "created_at": old.get("created_at", now) if old else now})
    return {"conversation_id": conv_ref.id, "answer": answer, "summary": summary}
