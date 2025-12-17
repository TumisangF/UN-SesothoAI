from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Sesotho-First Conversational AI")

class ChatRequest(BaseModel):
    message: str
    district: str = "Maseru"
    crop: str = "poone"

@app.post("/chat")
def chat(req: ChatRequest):
    prompt = f"""
Araba KA SESOTHO FEELA.
Se ke oa sebelisa Senyesemane.

U mohlohlelletsi oa temo Lesotho.

Boemo:
- Setereke: {req.district}
- Sejalo: {req.crop}

Melao:
- Fana ka keletso e ka lateloang
- Haeba tlhahisoleseding e haella, botsa potso e le nngwe

Potso:
"{req.message}"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200
    )

    return {
        "reply": response.choices[0].message.content.strip(),
        "language": "sesotho"
    }
