import json
import os

class KnowledgeBase:
    def __init__(self, db_path='knowledge_base.json'):
        self.db_path = db_path
        self.knowledge = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.knowledge, f, indent=4)

    def add(self, key, value):
        self.knowledge[key] = value
        self._save()

    def get(self, key):
        return self.knowledge.get(key)

    def get_all(self):
        return self.knowledge

    def delete(self, key):
        if key in self.knowledge:
            del self.knowledge[key]
            self._save()

# Example usage:
if __name__ == '__main__':
    kb = KnowledgeBase()
    kb.add('aws_credentials', {'access_key': 'YOUR_ACCESS_KEY', 'secret_key': 'YOUR_SECRET_KEY'})
    print(kb.get('aws_credentials'))
    kb.delete('aws_credentials')
    print(kb.get('aws_credentials'))