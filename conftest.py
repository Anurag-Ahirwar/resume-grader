# Presence of this file at the repo root makes pytest insert the repo root onto
# sys.path (default "prepend" import mode), so `parser_engine.*` imports resolve
# the same way they do when the app itself runs from the repo root.
#
# It also redirects the app's database at a throwaway SQLite file *before* any test
# module can import backend.app.db (which binds its engine to RESUME_GRADER_DB_URL at
# import time) -- this must happen here, not in a fixture, since fixtures only run after
# collection has already imported every test module.
import os
import tempfile

if "RESUME_GRADER_DB_URL" not in os.environ:
    _test_db_path = os.path.join(tempfile.gettempdir(), "resume_grader_test.db")
    if os.path.exists(_test_db_path):
        os.remove(_test_db_path)
    os.environ["RESUME_GRADER_DB_URL"] = f"sqlite:///{_test_db_path}"
