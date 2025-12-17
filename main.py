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


# --- Mock satellite data (for demo / hackathon) ---
def get_mock_satellite_data():
    return {
        "ndvi": "mahareng",
        "soil_moisture": "mahareng",
        "rainfall_forecast": "e teng"
    }


# --- Initialize conversation with satellite-aware system prompt ---
satellite = get_mock_satellite_data()

conversation_history = [
    {
        "role": "system",
        "content": (
            "U mothusi oa temo ea buang Sesotho feela bakeng sa balemi ba banyenyane Lesotho.\n"
            "U fana ka likeletso tsa temo u sebelisa tlhahisoleseling e tsoang ho satalaete.\n\n"
            f"Boemo ba limela (NDVI): {satellite['ndvi']}.\n"
            f"Mongobo oa mobu: {satellite['soil_moisture']}.\n"
            f"Ponelopele ea pula: {satellite['rainfall_forecast']}.\n\n"
            "Fana ka likeletso tse khutšoanyane, tse tobileng le tse sebetsang.\n"
            "Lipotso tsohle tse latelang li lokela ho arajoa ho ipapisitse le tlhahisoleseling ena.\n"
            "Kamehla araba ka Sesotho feela."
        )
    }
]


@app.get("/")
def health():
    return {"status": "ok", "message": "Sesotho AI backend running"}


@app.post("/chat")
def chat(query: Query):
    # Add user input to conversation
    conversation_history.append(
        {"role": "user", "content": query.text}
    )

    response = client.chat.completions.create(
        model=deployment_name,
        messages=conversation_history,
        max_completion_tokens=300
    )

    assistant_reply = response.choices[0].message.content

    # Store assistant reply for follow-ups
    conversation_history.append(
        {"role": "assistant", "content": assistant_reply}
    )

    return {"reply": assistant_reply}
