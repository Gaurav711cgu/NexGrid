import os
import re

test_dir = 'backend/tests'
conftest = os.path.join(test_dir, 'conftest.py')
with open(conftest, 'w') as f:
    f.write("""import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
""")

for filename in os.listdir(test_dir):
    if not filename.startswith('test_') or not filename.endswith('.py'):
        continue
    filepath = os.path.join(test_dir, filename)
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace 'client = TestClient(app)' with nothing
    content = re.sub(r'client\s*=\s*TestClient\(app\)\n', '', content)

    # Change 'def test_xyz():' to 'def test_xyz(client):'
    content = re.sub(r'def (test_\w+)\(\):', r'def \1(client):', content)
    
    # If the file had my previous 'with TestClient' workaround, remove it
    if 'with TestClient(app) as test_client:' in content:
        lines = content.split('\n')
        new_lines = []
        skip_lines = 0
        for line in lines:
            if 'with TestClient(app) as test_client:' in line:
                continue
            if 'test_client.' in line:
                line = line.replace('test_client.', 'client.')
                # Unindent if it starts with 8 spaces
                if line.startswith('        '):
                    line = line[4:]
            elif line.startswith('        ') or line.startswith('    #') or line == '    ':
                # best effort unindent for the block
                # this is tricky but I know the files exactly
                if line.startswith('        '):
                    line = line[4:]
            
            new_lines.append(line)
        content = '\n'.join(new_lines)
    
    with open(filepath, 'w') as f:
        f.write(content)

print("Done fixing tests")
