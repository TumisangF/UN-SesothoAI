from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

app = FastAPI(title="Sesotho AI Backend")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Query(BaseModel):
    text: str

@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running"}

@app.post("/chat")
def chat(query: Query):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Sesotho-first AI assistant for farmers in Lesotho. "
                    "Always respond ONLY in Sesotho. "
                    "Give clear, practical agricultural advice suitable for smallholder farmers."
                )
            },
            {"role": "user", "content": query.text}
        ],
        temperature=0.3,
        max_tokens=200
    )

    return {
        "reply": response.choices[0].message.content
    }
