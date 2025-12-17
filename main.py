from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

app = FastAPI(title="Sesotho AI Backend (Azure)")

# Connect to Azure OpenAI
client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_type="azure",
    api_version="2023-07-01-preview"
)

class Query(BaseModel):
    text: str

@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running on Azure"}

@app.post("/chat")
def chat(query: Query):
    response = client.chat.completions.create(
        engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # your Azure deployment
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

    return {"reply": response.choices[0].message.content}
