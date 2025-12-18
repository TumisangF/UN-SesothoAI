import os
from fastapi import FastAPI, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import africastalking
import requests
from openai import AzureOpenAI

# -----------------------------
# Configuration
# -----------------------------

load_dotenv()

AT_API_KEY = os.getenv("AT_API_KEY")
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_SENDER_ID = os.getenv("AT_SENDER_ID", "10946")

# -----------------------------
# App initialization
# -----------------------------

africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

app = FastAPI(title="Sesotho AI Backend")

# -----------------------------
# Azure OpenAI client
# -----------------------------
client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")


# -----------------------------
# Request schema
# -----------------------------
class Query(BaseModel):
    text: str


class SMSResponse(BaseModel):
    message: str
    recipient: str


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
        ),
    }
]
conversations_history = {}


# -----------------------------
# Helper Functions
# -----------------------------
def send_sms_reply(phone_number: str, message: str):
    """
    Sends the generated response back to the user via Africa's Talking.
    Using direct API call (more reliable than SDK for sandbox).
    """
    try:
        url = "https://api.sandbox.africastalking.com/version1/messaging"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": AT_API_KEY,
        }
        data = {
            "username": AT_USERNAME,
            "to": phone_number,
            "message": message,
            "from": AT_SENDER_ID,
        }

        response = requests.post(
            url, headers=headers, data=data, verify=False, timeout=30
        )

        if response.status_code == 201:
            result = response.json()
            print(f"SMS sent to {phone_number}: {result}")
            return result
        else:
            print(f"SMS send returned status {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None


def get_real_ai_response(phone_number: str, user_text: str) -> str:
    """
    Calls Azure OpenAI using the farmer's specific conversation history.
    """
    # 1. Reject empty input
    if not user_text or not user_text.strip():
        return "Ka kōpo kenya potso e hlakileng mabapi le temo."

    # 2. Retrieve the history for this specific farmer
    if phone_number not in conversations_history:
        # Initialize with a System Prompt to ensure the AI speaks Sesotho and gives Ag advice
        conversations_history[phone_number] = [
            {
                "role": "system",
                "content": "O mothusi oa temo ea bohlale ea bitsoang AgriSMS. Araba lipotso tsohle ka Sesotho sa Lesotho. fana ka likeletso tse nepahetseng ka lijalo, mobu le likokoanyana.",
            }
        ]

    # 3. Add user message to their specific history
    conversations_history[phone_number].append(
        {"role": "user", "content": user_text.strip()}
    )

    try:
        # 4. Call Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=conversations_history[phone_number],
            max_completion_tokens=300,
        )

        # 5. Extract reply safely
        assistant_reply = response.choices[0].message.content

        # Defensive fallback
        if not assistant_reply:
            assistant_reply = (
                "Ke kopa o mpotse hape ka mantsoe a mang. "
                "Ha ke a fumana karabo e feletseng."
            )

        # 6. Save assistant reply to history for context awareness
        conversations_history[phone_number].append(
            {"role": "assistant", "content": assistant_reply}
        )

        return assistant_reply

    except Exception as e:
        print(f"Error calling Azure OpenAI: {e}")
        return "Re masoabi, ho bile le phoso ho tšebetsong ea rona. Ka kopo leka hape hamorao."


# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running"}


# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
def chat(query: Query):

    # Reject empty input
    if not query.text or not query.text.strip():
        return {"reply": "Ka kōpo kenya potso e hlakileng mabapi le temo."}

    # Add user message to history
    conversation_history.append({"role": "user", "content": query.text.strip()})

    # Call Azure OpenAI
    response = client.chat.completions.create(
        model=deployment_name, messages=conversation_history, max_completion_tokens=300
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
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return {"reply": assistant_reply}


# -----------------------------
# Incoming SMS Webhook
# -----------------------------
@app.post("/incoming-sms")
async def incoming_sms_webhook(
    background_tasks: BackgroundTasks,
    from_: str = Form(..., alias="from"),
    text: str = Form(...),
):
    print(f"📩 Incoming SMS from {from_}: {text}")

    # 1. Get response from the Real AI (Context Aware per phone number)
    ai_response_text = get_real_ai_response(from_, text)

    # 2. Send SMS back to the farmer asynchronously
    background_tasks.add_task(send_sms_reply, from_, ai_response_text)

    return ""


# -----------------------------
# Optional: Reset conversation
# (Very useful for demos)
# -----------------------------
@app.post("/reset")
def reset_conversation():
    global conversation_history
    conversation_history = conversation_history[:1]
    return {"status": "ok", "message": "Puisano e qaliloe bocha."}


# -----------------------------
# Manual SMS sending
# -----------------------------
@app.post("/send-manual")
async def send_manual_message(payload: SMSResponse):
    """
    Endpoint to manually trigger a message (Useful for testing).
    """
    try:
        result = send_sms_reply(payload.recipient, payload.message)
        if result:
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to send SMS")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
