import os
import re

test_dir = 'backend/tests'

# 1. Create conftest.py
with open(os.path.join(test_dir, 'conftest.py'), 'w') as f:
    f.write('''import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
''')

# 2. Rewrite test files
for filename in os.listdir(test_dir):
    if not filename.startswith('test_') or not filename.endswith('.py'):
        continue
    filepath = os.path.join(test_dir, filename)
    with open(filepath, 'r') as f:
        content = f.read()

    # Remove global client
    content = re.sub(r'client\s*=\s*TestClient\(app\)\n', '', content)
    
    # Remove with TestClient(app) as test_client: and unindent
    if 'with TestClient(app) as test_client:' in content:
        content = content.replace('with TestClient(app) as test_client:', '')
        content = content.replace('test_client.', 'client.')
        # We also need to fix indentation, but this is getting complicated with regex.
        # Let's just fix the files manually or with sed.

print("Done")
