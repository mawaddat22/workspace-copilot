import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from rag.retriever import retrieve

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    model="openai/gpt-4o-mini"
)

prompt = ChatPromptTemplate.from_template("""
You are a helpful workspace assistant.
Use the following context from the knowledge base to answer the user's question.
If the answer is not in the context, say you don't have that information.

Context:
{context}

Question: {question}

Answer:
""")

def answer_policy_question(question: str) -> str:
    context = retrieve(question)
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})
    return response.content