from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post(
    "/documents/upload",
    files={"file": ("sample.pdf", b"%PDF-1.4\n%test", "application/pdf")},
)
print(response.status_code)
print(response.json())
