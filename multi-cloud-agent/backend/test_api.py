import unittest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAPI(unittest.TestCase):
    def test_prompt_aws(self):
        resp = client.post('/prompt', json={"prompt": "List all EC2 instances on AWS"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('steps', data)
        self.assertIn('aws', str(data))

    def test_prompt_multi_cloud(self):
        resp = client.post('/prompt', json={"prompt": "List all VMs in AWS and Azure"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('aws', str(data))
        self.assertIn('azure', str(data))

    def test_prompt_error(self):
        resp = client.post('/prompt', json={"prompt": "List all VMs in Azure"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Should error if no AZURE_SUBSCRIPTION_ID
        if not data['status'] == 'success':
            self.assertIn('error', str(data))

if __name__ == '__main__':
    unittest.main()