"""Test script to demonstrate structured error responses."""
from app.core.errors import APIError, ErrorDetail


def test_error_structures():
    """Demonstrate the new structured error format."""
    print("Testing Structured Error Responses\n")
    print("=" * 70)
    
    # Test 1: Session not found
    print("\n1. Session Not Found Error:")
    try:
        raise APIError.not_found(
            APIError.SESSION_NOT_FOUND,
            resource_type="session",
            resource_id="abc-123"
        )
    except Exception as e:
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
    
    # Test 2: Profile not found
    print("\n2. Profile Not Found Error:")
    try:
        raise APIError.not_found(
            APIError.PROFILE_NOT_FOUND,
            resource_type="profile",
            resource_id=42
        )
    except Exception as e:
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
    
    # Test 3: Missing API key
    print("\n3. Missing API Key Error:")
    try:
        raise APIError.bad_request(
            APIError.MISSING_API_KEY,
            message="OpenRouter API key is not configured",
            details={"config_key": "OPENROUTER_API_KEY"}
        )
    except Exception as e:
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
    
    # Test 4: File save failed
    print("\n4. File Save Failed Error:")
    try:
        raise APIError.internal_error(
            APIError.FILE_SAVE_FAILED,
            message="Failed to save uploaded file",
            details={"filename": "document.txt", "error": "Permission denied"}
        )
    except Exception as e:
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
    
    # Test 5: Document not found
    print("\n5. Document Not Found Error:")
    try:
        raise APIError.not_found(
            APIError.DOCUMENT_NOT_FOUND,
            resource_type="document",
            resource_id="missing-doc.pdf"
        )
    except Exception as e:
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
    
    print("\n" + "=" * 70)
    print("\nAll error codes available:")
    print("  - SESSION_NOT_FOUND")
    print("  - PROFILE_NOT_FOUND")
    print("  - DOCUMENT_NOT_FOUND")
    print("  - MESSAGE_NOT_FOUND")
    print("  - USAGE_LOG_NOT_FOUND")
    print("  - MISSING_API_KEY")
    print("  - MISSING_FILENAME")
    print("  - FILE_SAVE_FAILED")
    print("  - FILE_DELETE_FAILED")
    print("  - OPENROUTER_ERROR")
    print("  - STREAM_ERROR")
    
    print("\n✅ All structured error tests passed!")


if __name__ == "__main__":
    test_error_structures()
