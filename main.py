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

# In-memory conversation history
conversation_history = [
    {
        "role": "system",
        "content": (
            "You are a Sesotho-first AI assistant for farmers in Lesotho. "
            "Always respond ONLY in Sesotho. "
            "Give clear, practical agricultural advice suitable for smallholder farmers."
        )
    }
]

@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running"}

@app.post("/chat")
def chat(query: Query):
    # Add user message
    conversation_history.append({"role": "user", "content": query.text})

    response = client.chat.completions.create(
        model=deployment_name,
        messages=conversation_history,
        max_completion_tokens=500
    )

    assistant_reply = response.choices[0].message.content

    # Save assistant reply to history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return {"reply": assistant_reply}
