import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"

# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0):    
    client = OpenAI(base_url=endpoint,api_key=token)
    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature, top_p=top_p, model=model)
    return response.choices[0].message.content

# A function to translate to target language
def translate(language, text):
    messages = [
        {
            "role": "system",
            "content": f"Translate the following text to {language}.",
        },
        {
            "role": "user",
            "content": text,
        }
    ]
    response_content = call_llm_model(model, messages)
    return response_content

# Run the main function if this script is executed
if __name__ == "__main__":
    result = translate("Chinese", "Hello how are you?")
    print(result)

