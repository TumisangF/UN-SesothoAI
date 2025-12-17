from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import AzureOpenAI

# -----------------------------
# App initialization
# -----------------------------
app = FastAPI(title="Sesotho AI Backend")

# -----------------------------
# Azure OpenAI client
# -----------------------------
client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# -----------------------------
# Request schema
# -----------------------------
class Query(BaseModel):
    text: str

# -----------------------------
# In-memory conversation history
# (Hackathon-safe, single-session)
# -----------------------------
conversation_history = [
    {
        "role": "system",
        "content": (
            "U mothusi oa AI ea qalang ka Sesotho bakeng sa balemi ba Lesotho. "
            "Arabela KA SESOTHO FEELA. "
            "Fana ka likeletso tse khutšoane, tse hlakileng, le tse sebetsang mabapi le temo. "
            "Etsa likhakanyo tse bonolo u ipapisitse le tlhaiso-leseling ea maemo a leholimo "
            "le boemo ba masimo joalokaha eka e tsoa ho data ea disathalaete. "
            "Arabela lipotso tsohle tse latelang u latela moelelo oa puisano."
        )
    }
]

# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def health():
    return {
        "status": "ok",
        "message": "Sesotho AI backend running"
    }

# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
def chat(query: Query):

    # Reject empty input
    if not query.text or not query.text.strip():
        return {
            "reply": "Ka kōpo kenya potso e hlakileng mabapi le temo."
        }

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": query.text.strip()
    })

    # Call Azure OpenAI
    response = client.chat.completions.create(
        model=deployment_name,
        messages=conversation_history,
        max_completion_tokens=300
    )

    # Extract reply safely
    assistant_reply = response.choices[0].message.content

    # Defensive fallback (VERY IMPORTANT)
    if not assistant_reply:
        assistant_reply = (
            "Ke kopa o mpotse hape ka mantsoe a mang. "
            "Ha ke a fumana karabo e feletseng."
        )

    # Save assistant reply
    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })

    return {
        "reply": assistant_reply
    }

# -----------------------------
# Optional: Reset conversation
# (Very useful for demos)
# -----------------------------
@app.post("/reset")
def reset_conversation():
    global conversation_history
    conversation_history = conversation_history[:1]
    return {
        "status": "ok",
        "message": "Puisano e qaliloe bocha."
    }
