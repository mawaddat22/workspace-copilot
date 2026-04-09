import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from mcp_servers.booking_mcp import check_availability, create_booking, cancel_booking

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    model="openai/gpt-4o-mini"
)

extract_prompt = ChatPromptTemplate.from_template("""
Extract booking details from this user request and return ONLY a JSON object.

User request: {request}

Return JSON with these fields:
- action: one of "check_availability", "create_booking", "cancel_booking"
- date: in YYYY-MM-DD format
- time: in HH:MM format (24hr), if mentioned
- room_type: "meeting_room" or "desk"
- room_id: specific room if mentioned, else null
- user_id: "user_001" (default)
- booking_id: integer if cancelling, else null

Today's date: {today}
Return ONLY the JSON, no explanation.
""")

def handle_booking_request(user_request: str) -> str:
    from datetime import date
    today = date.today().isoformat()
    chain = extract_prompt | llm
    response = chain.invoke({"request": user_request, "today": today})
    try:
        raw = re.sub(r"```json|```", "", response.content.strip()).strip()
        data = json.loads(raw)
        action = data.get("action")

        
        if action == "check_availability":
            date = data.get("date") or today
            room_type = data.get("room_type") or "meeting_room"
            result = check_availability(date, room_type)
            if result["is_available"]:
                return f"✅ {result['available_slots']} slot(s) available for {result['room_type']} on {result['date']}."
            else:
                return f"❌ No {result['room_type']} available on {result['date']}."    

        elif action == "create_booking":
            room_id = data.get("room_id") or f"{data.get('room_type', 'meeting_room')}_A"
            result = create_booking(
                user_id=data.get("user_id", "user_001"),
                room_id=room_id,
                date=data["date"],
                time=data.get("time", "09:00")
            )
            return result["message"]

        elif action == "cancel_booking":
            result = cancel_booking(int(data["booking_id"]))
            return result["message"]

        else:
            return "I couldn't understand that booking request. Please try again."

    except Exception as e:
        return f"Error processing booking: {str(e)}"