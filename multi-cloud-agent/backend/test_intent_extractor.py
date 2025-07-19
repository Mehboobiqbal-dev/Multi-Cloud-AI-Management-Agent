import unittest
from intent_extractor import extract_intents

class TestIntentExtractor(unittest.TestCase):
    def test_single_cloud(self):
        prompt = "List all EC2 instances on AWS"
        intents = extract_intents(prompt)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0]['cloud'], 'aws')
        self.assertEqual(intents[0]['operation'], 'list')
        self.assertEqual(intents[0]['resource'], 'vm')

    def test_multi_cloud(self):
        prompt = "List all VMs in AWS and Azure"
        intents = extract_intents(prompt)
        self.assertIn({'cloud': 'aws', 'operation': 'list', 'resource': 'vm'}, intents)
        self.assertIn({'cloud': 'azure', 'operation': 'list', 'resource': 'vm'}, intents)
        self.assertEqual(len(intents), 2)

    def test_unknown_cloud(self):
        prompt = "List all VMs"
        intents = extract_intents(prompt)
        self.assertEqual(len(intents), 3)  # Defaults to all clouds

    def test_storage(self):
        prompt = "List all storage buckets in GCP"
        intents = extract_intents(prompt)
        self.assertEqual(intents[0]['cloud'], 'gcp')
        self.assertEqual(intents[0]['resource'], 'storage')

if __name__ == '__main__':
    unittest.main()