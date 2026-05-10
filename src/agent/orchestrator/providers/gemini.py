from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_orchestrator(model_name: str, api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key
    )