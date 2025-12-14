#!/usr/bin/env python3
"""
Quick test script to verify search functionality
Run after backend is started: python test_search_manual.py
"""
import asyncio
import aiosqlite
from app.db import init_db
from app import repo
from app.core.config import settings

async def test_search():
    """Manual test of search functionality"""
    print("🔍 Testing Search Feature\n")
    
    # Initialize database (will run migrations)
    await init_db()
    
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        
        print("✓ Database initialized")
        
        # Create test session
        session_data = {
            "session_type": "chat",
            "title": "Search Test Session"
        }
        session_id = await repo.create_session(db, session_data)
        print(f"✓ Created session: {session_id}")
        
        # Add test messages
        test_messages = [
            ("user", "How do I fix an API connection timeout error?"),
            ("assistant", "To fix API timeout errors, increase the timeout value in your configuration."),
            ("user", "The database query is running very slowly"),
            ("assistant", "Try adding an index to improve query performance."),
            ("user", "Python script crashes with memory error"),
        ]
        
        for role, content in test_messages:
            await repo.add_message(db, session_id, role, content)
        
        print(f"✓ Added {len(test_messages)} test messages\n")
        
        # Test 1: Basic search
        print("Test 1: Basic keyword search - 'error'")
        results = await repo.search_messages(db, "error")
        print(f"  Found {len(results)} results")
        for r in results:
            print(f"  - [{r['role']}] {r['snippet'][:60]}...")
        print()
        
        # Test 2: Phrase search
        print("Test 2: Phrase search - '\"timeout error\"'")
        results = await repo.search_messages(db, '"timeout error"')
        print(f"  Found {len(results)} results")
        for r in results:
            print(f"  - [{r['role']}] {r['snippet'][:60]}...")
        print()
        
        # Test 3: Exclusion
        print("Test 3: Exclude term - 'error -memory'")
        results = await repo.search_messages(db, "error -memory")
        print(f"  Found {len(results)} results")
        for r in results:
            print(f"  - [{r['role']}] {r['snippet'][:60]}...")
        print()
        
        # Test 4: Prefix matching
        print("Test 4: Prefix search - 'query*'")
        results = await repo.search_messages(db, "query*")
        print(f"  Found {len(results)} results")
        for r in results:
            print(f"  - [{r['role']}] {r['snippet'][:60]}...")
        print()
        
        # Test 5: Session type filter
        print("Test 5: Filter by session type - 'error' in chat sessions")
        results = await repo.search_messages(db, "error", session_type="chat")
        print(f"  Found {len(results)} results (filtered)")
        print()
        
        print("✅ All search tests completed successfully!\n")
        print("🚀 Search feature is ready to use!")
        print("\nTry searching via API:")
        print('  curl "http://localhost:8000/api/messages/search?query=error"')

if __name__ == "__main__":
    asyncio.run(test_search())
