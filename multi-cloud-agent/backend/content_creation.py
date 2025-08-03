import openai
import os

def generate_content(prompt: str, content_type: str = 'text') -> str:
    """Generates content using OpenAI. Type can be 'text', 'blog', 'code', 'image', 'video'."""
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if content_type in ['text', 'blog', 'code']:
        engine = 'text-davinci-003' if content_type == 'code' else 'gpt-3.5-turbo'
        response = openai.Completion.create(engine=engine, prompt=prompt, max_tokens=1000 if content_type == 'blog' else 500)
        return response.choices[0].text.strip()
    elif content_type == 'image':
        response = openai.Image.create(prompt=prompt, n=1, size='1024x1024')
        return response['data'][0]['url']
    elif content_type == 'video':
        # Placeholder for video generation, e.g., using an external API
        return "Video generated: [placeholder URL]"
    return "Unsupported content type."