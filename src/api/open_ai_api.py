from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5-nano-2025-08-07",
    input="Write back ok, i undesrand"
)

print(response.output_text)

