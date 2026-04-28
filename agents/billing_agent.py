import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from mcp_servers.finance_mcp import (
    generate_invoice,
    fetch_payment_status,
    download_invoice,
    mark_invoice_paid
)

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    model="openai/gpt-4o-mini"
)

extract_prompt = ChatPromptTemplate.from_template("""
Extract billing details from this user request and return ONLY a JSON object.

User request: {request}

Return JSON with these fields:
- action: one of "generate_invoice", "fetch_payment_status", "download_invoice", "mark_paid"
- user_id: "user_001" (default)
- invoice_id: invoice ID if mentioned (e.g. INV-XXXX), else null
- amount: amount if mentioned, else null

Return ONLY the JSON, no explanation.
""")

def handle_billing_request(user_request: str) -> str:
    chain = extract_prompt | llm
    response = chain.invoke({"request": user_request})
    
    try:
        raw = re.sub(r"```json|```", "", response.content.strip()).strip()
        data = json.loads(raw)
        action = data.get("action")
        user_id = data.get("user_id", "user_001")

        if action == "generate_invoice":
            amount = data.get("amount")
            result = generate_invoice(user_id, amount)
            return result["message"]

        elif action == "fetch_payment_status":
            result = fetch_payment_status(user_id)
            if not result["success"]:
                return result["message"]
            response_text = result["message"] + "\n\n"
            for inv in result["invoices"]:
                status_emoji = "✅" if inv["status"] == "paid" else "⏳"
                response_text += f"{status_emoji} {inv['invoice_id']} — ${inv['amount']} — {inv['status'].upper()} — Due: {inv['due_date']}\n"
            return response_text

        elif action == "download_invoice":
            invoice_id = data.get("invoice_id")
            if not invoice_id:
                return "Please provide an invoice ID to download."
            result = download_invoice(invoice_id)
            if not result["success"]:
                return result["message"]
            inv = result["invoice"]
            return (
                f"📄 Invoice Details:\n"
                f"ID: {inv['invoice_id']}\n"
                f"Amount: ${inv['amount']}\n"
                f"Status: {inv['status'].upper()}\n"
                f"Due Date: {inv['due_date']}\n"
                f"Created: {inv['created_at']}"
            )

        elif action == "mark_paid":
            invoice_id = data.get("invoice_id")
            if not invoice_id:
                return "Please provide an invoice ID to mark as paid."
            result = mark_invoice_paid(invoice_id, user_id)
            return result["message"]

        else:
            return "I couldn't understand that billing request. Please try again."

    except Exception as e:
        return f"Error processing billing request: {str(e)}"