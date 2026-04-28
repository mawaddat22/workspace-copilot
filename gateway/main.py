from fastapi import FastAPI
from pydantic import BaseModel
from agents.knowledge_agent import answer_policy_question
from agents.booking_agent import handle_booking_request
from agents.billing_agent import handle_billing_request

app = FastAPI(title="Workspace Copilot")

class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_001"

class ChatResponse(BaseModel):
    response: str
    agent_used: str

def detect_intent(message: str) -> str:
    msg = message.lower()

    # Knowledge keywords take priority
    knowledge_keywords = ["policy", "hours", "amenities", "membership", "wifi", "guest", "payment terms", "rules"]
    if any(word in msg for word in knowledge_keywords):
        return "knowledge"

    # Billing keywords
    billing_keywords = ["invoice", "payment", "bill", "pay", "charge", "receipt", "finance", "subscription"]
    if any(word in msg for word in billing_keywords):
        return "billing"

    # Booking keywords
    booking_keywords = ["book", "reserve", "cancel booking", "availability", "available", "desk", "meeting room"]
    if any(word in msg for word in booking_keywords):
        return "booking"

    return "knowledge"

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    intent = detect_intent(request.message)

    if intent == "billing":
        response = handle_billing_request(request.message)
        agent = "Billing Agent"
    elif intent == "booking":
        response = handle_booking_request(request.message)
        agent = "Booking Agent"
    else:
        response = answer_policy_question(request.message)
        agent = "Knowledge Agent"

    return ChatResponse(response=response, agent_used=agent)

@app.get("/health")
def health():
    return {"status": "ok", "message": "Workspace Copilot is running!"}