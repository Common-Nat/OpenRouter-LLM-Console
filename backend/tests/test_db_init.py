import pytest, os, tempfile
from app.core.config import Settings
from app import db as dbmod

@pytest.mark.asyncio
async def test_init_db_creates_file(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.db")
        # override settings via env for this test module
        monkeypatch.setenv("DB_PATH", p)
        # reload settings-dependent module cautiously
        # call init_db directly using new settings by re-importing settings
        from importlib import reload
        from app.core import config as cfg
        reload(cfg)
        reload(dbmod)
        await dbmod.init_db()
        assert os.path.exists(p)
