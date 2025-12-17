from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import AzureOpenAI

app = FastAPI(title="Sesotho AI Backend")

# Azure OpenAI client
client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

class Query(BaseModel):
    text: str

@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running"}

@app.post("/chat")
def chat(query: Query):
    response = client.chat.completions.create(
        model=deployment_name,
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
        max_completion_tokens=200
    )

    return {
        "reply": response.choices[0].message.content
    }
