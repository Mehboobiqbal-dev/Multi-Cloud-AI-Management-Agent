import re
from typing import Dict, List

# Optionally, you can integrate OpenAI or HuggingFace here
# For now, use a simple rule-based parser for demo

def extract_intents(prompt: str) -> List[Dict]:
    prompt = prompt.lower()
    clouds = []
    if 'aws' in prompt or 'amazon' in prompt:
        clouds.append('aws')
    if 'azure' in prompt:
        clouds.append('azure')
    if 'gcp' in prompt or 'google' in prompt:
        clouds.append('gcp')
    if not clouds:
        # Try to infer all if not specified
        clouds = ['aws', 'azure', 'gcp']

    # Simple resource and operation extraction
    if 'create' in prompt:
        operation = 'create'
    elif 'delete' in prompt:
        operation = 'delete'
    elif 'list' in prompt:
        operation = 'list'
    elif 'start' in prompt:
        operation = 'start'
    elif 'stop' in prompt:
        operation = 'stop'
    else:
        operation = 'unknown'

    # Resource extraction (very basic)
    if 'vm' in prompt or 'ec2' in prompt or 'virtual machine' in prompt:
        resource = 'vm'
    elif 'bucket' in prompt or 'storage' in prompt:
        resource = 'storage'
    elif 'database' in prompt:
        resource = 'database'
    else:
        resource = 'unknown'

    return [
        {'cloud': cloud, 'operation': operation, 'resource': resource}
        for cloud in clouds
    ]