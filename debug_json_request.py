import json
import os
from unittest.mock import MagicMock, patch
from backend.app.llm.orchestrator import OpenRouterClient, LLMOrchestrator, SectionSpec

# Mock environment variables
os.environ["OPENROUTER_API_KEY"] = "test_key"

def test_payload_structure():
    print("--- ЗАПУСК ТЕСТА СТРУКТУРЫ ЗАПРОСА ---\n")
    
    # Initialize client
    client = OpenRouterClient.from_env()
    
    # Mock urllib.request.urlopen to intercept the request
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Setup the mock to return a valid fake response so the client doesn't crash
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "{\"section_id\": \"test\", \"title\": \"Test\", \"content\": \"Success\"}"}}]
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Define a test section
        section = SectionSpec(
            section_id="horary_test",
            title="Тест Хорара",
            prompt="Ответь на вопрос."
        )
        
        # Context with the new 'question' field
        context = {
            "client": {"name": "Test User"},
            "question": "Где мои ключи?",
            "chart": {"positions": []}
        }

        # Run orchestrator (which calls client.generate)
        orchestrator = LLMOrchestrator(client)
        try:
            orchestrator.generate_sections([section], context)
        except Exception as e:
            print(f"Error during execution: {e}")

        # Extract the sent data
        # call_args[0][0] is the Request object
        sent_request = mock_urlopen.call_args[0][0]
        sent_data = sent_request.data
        decoded_json = json.loads(sent_data)

        print(">>> ЗАГОЛОВКИ ЗАПРОСА:")
        print(sent_request.headers)
        print("\n>>> ТЕЛО ЗАПРОСА (JSON):")
        print(json.dumps(decoded_json, indent=2, ensure_ascii=False))
        
        # Verify specific fields
        print("\n>>> ПРОВЕРКА:")
        if sent_request.headers.get("Content-type") == "application/json":
            print("[OK] Header Content-Type is application/json")
        else:
            print("[FAIL] Header Content-Type is wrong")
            
        messages = decoded_json.get("messages", [])
        system_msg = next((m for m in messages if m["role"] == "system"), None)
        user_msg = next((m for m in messages if m["role"] == "user"), None)
        
        if system_msg and "JSON" in system_msg["content"]:
             print("[OK] System prompt enforces JSON output")
        
        if user_msg and "Где мои ключи?" in user_msg["content"]:
             print("[OK] User prompt contains the question")

if __name__ == "__main__":
    test_payload_structure()
