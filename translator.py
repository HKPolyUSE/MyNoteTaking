import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent
PROMPT_PATH = ROOT_DIR / "prompts" / "translate_prompt.md"
load_dotenv(ROOT_DIR / ".env")

MODEL_ID = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731")


class TranslationError(Exception):
    """Raised when a translation cannot be completed or validated."""


def translate_note(title: str, content: str) -> dict[str, str]:
    try:
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise TranslationError(f"Could not load translation prompt: {error}") from error

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise TranslationError("OPENROUTER_API_KEY is not configured.")

    try:
        response = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        ).chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"title": title, "content": content},
                        ensure_ascii=False,
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
    except Exception as error:
        raise TranslationError(f"Translation provider request failed: {error}") from error

    if not response.choices:
        raise TranslationError("Translation provider returned no translation choices.")

    try:
        result_text = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise TranslationError("Translation provider returned an invalid response.") from error
    if not isinstance(result_text, str):
        raise TranslationError("Translation provider returned an empty response.")

    try:
        result = json.loads(result_text)
    except json.JSONDecodeError as error:
        raise TranslationError("Translation provider returned invalid JSON.") from error

    if (
        not isinstance(result, dict)
        or not isinstance(result.get("title"), str)
        or not isinstance(result.get("content"), str)
    ):
        raise TranslationError(
            'Translation provider response must contain string "title" and "content" fields.'
        )

    return {"title": result["title"], "content": result["content"]}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print('用法: python translator.py "要翻译的文本"')
        sys.exit(1)

    translated = translate_note("", " ".join(sys.argv[1:]))
    print(json.dumps(translated, ensure_ascii=False))
