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


# When User inputs free-form notes, the LLM processes the text to extract and organize information into predefined structured fields in JSON format
system_prompt = '''
Extract the user's notes into the following structured fields:
1. Title: A concise title of the notes less than 5 words
2. Notes: The notes based on user input written in full sentences.
3. Tags (A list):  At most 3 Keywords or tags that categorize the content of the notes.


Output in JSON format without ```json. Output title and notes in the language: {lang}.
Example:
Input: "Badminton tmr 5pm @polyu".
Output:
{{
  "Title": "Badminton at PolyU", 
  "Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
  "Tags": ["badminton", "sports"]
}}

'''

def process_user_notes(language, user_input):
    system_prompt_filled = system_prompt.format(
        lang=language
    )
    
    messages = [
        {
            "role": "system",
            "content": system_prompt_filled,
        },
        {
            "role": "user",
            "content": user_input,
        }
    ]
    
    response_content = call_llm_model(model, messages)
    return response_content
    
# Run the main function if this script is executed
if __name__ == "__main__":
   # result = translate("Chinese", "Git is a version control system")
   # print(result)

   result = process_user_notes("Chinese", "Get up tomorrow 7am")
   print(result)

   result = process_user_notes("English", "Learn python programming and docker")
   print(result)
   