from e2b_code_interpreter import Sandbox
import os
from threading import Lock

class SandBox:
    """Sandbox for safe execution"""
    def __init__(self):
        self.sandbox = Sandbox.create(
            api_key = os.getenv("E2B_API_KEY"), 
            timeout = 10 * 60,
            lifecycle={
                "on_timeout": "pause"
            },
        )
        print('Sandbox created', self.sandbox.sandbox_id)
    
    def pause_sandbox(self):
        self.sandbox.pause() 
        print('Sandbox paused', self.sandbox.sandbox_id)

    def resume_sandbox(self):
        self.sandbox.connect()
        print('Connected to the sandbox', self.sandbox.sandbox_id)
    
    def close_sandbox(self):
        self.sandbox.kill()


_sandboxes = {}
_lock = Lock()


def get_session_sandbox(session_id: str):
    """Return an existing sandbox for this session or create one."""
    with _lock:
        if session_id not in _sandboxes:
            _sandboxes[session_id] = SandBox()
        return _sandboxes[session_id].sandbox


def close_session_sandbox(session_id: str):
    """Close and remove the sandbox bound to the given session."""
    with _lock:
        sbx = _sandboxes.pop(session_id, None)
    if sbx is not None:
        sbx.close_sandbox()


def invalidate_session_sandbox(session_id: str):
    """Mark sandbox as dead, remove it, and create a fresh one on next call."""
    with _lock:
        sbx = _sandboxes.pop(session_id, None)
    if sbx is not None:
        try:
            sbx.close_sandbox()
        except Exception as e:
            print(f"Error closing dead sandbox {sbx.sandbox.sandbox_id}: {e}")
    print(f"Sandbox invalidated for session {session_id}. Will auto-restart on next use.")