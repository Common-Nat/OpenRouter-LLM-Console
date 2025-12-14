import pytest
import aiosqlite
from app import repo
from app.db import init_db
from app.core.config import settings

@pytest.fixture
async def test_db():
    """Create a test database with FTS5 search enabled"""
    settings.db_path = ":memory:"
    await init_db()
    
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Run migrations manually for test
        await db.executescript(open("migrations/001_initial_schema.sql").read())
        await db.executescript(open("migrations/003_add_fts_search.sql").read())
        
        yield db

@pytest.mark.asyncio
async def test_search_basic_keyword(test_db):
    """Test basic keyword search"""
    # Create test session
    session_data = {"session_type": "chat", "title": "Test Session"}
    session_id = await repo.create_session(test_db, session_data)
    
    # Add test messages
    await repo.add_message(test_db, session_id, "user", "How do I fix an API error?")
    await repo.add_message(test_db, session_id, "assistant", "To fix API errors, check the logs.")
    await repo.add_message(test_db, session_id, "user", "The database connection is slow.")
    
    # Search for "API"
    results = await repo.search_messages(test_db, "API")
    
    assert len(results) == 2
    assert "API" in results[0]["content"] or "API" in results[0]["snippet"]

@pytest.mark.asyncio
async def test_search_phrase_exact(test_db):
    """Test exact phrase search"""
    session_data = {"session_type": "chat"}
    session_id = await repo.create_session(test_db, session_data)
    
    await repo.add_message(test_db, session_id, "user", "connection timeout occurred")
    await repo.add_message(test_db, session_id, "user", "timeout and connection issues")
    
    # Search for exact phrase
    results = await repo.search_messages(test_db, '"connection timeout"')
    
    assert len(results) == 1
    assert "connection timeout" in results[0]["content"].lower()

@pytest.mark.asyncio
async def test_search_with_session_type_filter(test_db):
    """Test filtering by session type"""
    # Create different session types
    chat_id = await repo.create_session(test_db, {"session_type": "chat"})
    code_id = await repo.create_session(test_db, {"session_type": "code"})
    
    await repo.add_message(test_db, chat_id, "user", "debugging error")
    await repo.add_message(test_db, code_id, "user", "debugging error")
    
    # Search with filter
    results = await repo.search_messages(test_db, "debugging", session_type="chat")
    
    assert len(results) == 1
    assert results[0]["session_type"] == "chat"

@pytest.mark.asyncio
async def test_search_with_date_filter(test_db):
    """Test date range filtering"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    await repo.add_message(test_db, session_id, "user", "old message")
    
    # Search with future date range (should return nothing)
    results = await repo.search_messages(
        test_db,
        "old",
        start_date="2030-01-01"
    )
    
    assert len(results) == 0

@pytest.mark.asyncio
async def test_search_exclude_term(test_db):
    """Test excluding terms with minus operator"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    await repo.add_message(test_db, session_id, "user", "python error in code")
    await repo.add_message(test_db, session_id, "user", "javascript error in code")
    
    # Search for error but exclude python
    results = await repo.search_messages(test_db, "error -python")
    
    assert len(results) == 1
    assert "javascript" in results[0]["content"].lower()

@pytest.mark.asyncio
async def test_search_prefix_matching(test_db):
    """Test prefix matching with asterisk"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    await repo.add_message(test_db, session_id, "user", "testing the api")
    await repo.add_message(test_db, session_id, "user", "tested successfully")
    await repo.add_message(test_db, session_id, "user", "tester found bug")
    
    # Search with prefix
    results = await repo.search_messages(test_db, "test*")
    
    assert len(results) == 3

@pytest.mark.asyncio
async def test_search_ranking(test_db):
    """Test that results are ranked by relevance"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    # Message with multiple occurrences should rank higher
    await repo.add_message(test_db, session_id, "user", "error error error fix")
    await repo.add_message(test_db, session_id, "user", "minor error occurred")
    
    results = await repo.search_messages(test_db, "error")
    
    assert len(results) == 2
    # First result should have better rank (lower BM25 score in negative)
    assert results[0]["rank"] <= results[1]["rank"]

@pytest.mark.asyncio
async def test_search_pagination(test_db):
    """Test pagination with limit and offset"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    # Add 10 messages
    for i in range(10):
        await repo.add_message(test_db, session_id, "user", f"test message {i}")
    
    # First page
    page1 = await repo.search_messages(test_db, "test", limit=5, offset=0)
    assert len(page1) == 5
    
    # Second page
    page2 = await repo.search_messages(test_db, "test", limit=5, offset=5)
    assert len(page2) == 5
    
    # Ensure no overlap
    page1_ids = [r["id"] for r in page1]
    page2_ids = [r["id"] for r in page2]
    assert len(set(page1_ids) & set(page2_ids)) == 0

@pytest.mark.asyncio
async def test_search_empty_query_handling(test_db):
    """Test handling of empty or whitespace query"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    await repo.add_message(test_db, session_id, "user", "some content")
    
    # Empty string should return no results (or be handled gracefully)
    results = await repo.search_messages(test_db, "   ")
    # This might raise an exception or return empty - adjust based on implementation
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_search_snippet_highlighting(test_db):
    """Test that snippets contain highlight markers"""
    session_id = await repo.create_session(test_db, {"session_type": "chat"})
    
    await repo.add_message(
        test_db,
        session_id,
        "user",
        "This is a long message with the keyword somewhere in the middle of the text"
    )
    
    results = await repo.search_messages(test_db, "keyword")
    
    assert len(results) == 1
    snippet = results[0]["snippet"]
    # Check for highlight markers
    assert "<mark>" in snippet
    assert "</mark>" in snippet
    assert "keyword" in snippet.lower()
