"""Tools for the agent."""
from langchain_core.tools import tool
import json
from pathlib import Path
from .sandbox import get_session_sandbox, invalidate_session_sandbox
import re
from playwright.sync_api import sync_playwright
from langchain_tavily import TavilySearch
import os

def create_tools(session_id: str):
    """Create a tool list bound to one session sandbox."""

    @tool
    def bash(command: str) -> str:
        """Executes a command inside an E2B sandbox and returns output or error."""

        wrapped_command = json.dumps(command)
        code = f"""
import subprocess

try:
    result = subprocess.run(
        {wrapped_command},
        shell=True,
        executable='/bin/bash',
        capture_output=True,
        text=True,
        timeout=30,
    )
    print(result.stdout if result.returncode == 0 else result.stderr, end='')
except subprocess.TimeoutExpired:
    print('Error: Command timed out after 30 seconds.', end='')
except Exception as e:
    print(f'Unexpected Error: {{str(e)}}', end='')
"""

        max_retries = 2
        for attempt in range(max_retries):
            try:
                sandbox = get_session_sandbox(session_id)
                execution = sandbox.run_code(code)
                if getattr(execution, "error", None):
                    return f"Error: {execution.error}"

                logs = getattr(execution, "logs", None)
                if logs is None:
                    return str(execution)

                stdout_logs = getattr(logs, "stdout", [])
                stderr_logs = getattr(logs, "stderr", [])
                stdout = "\n".join(str(line) for line in stdout_logs).strip()
                stderr = "\n".join(str(line) for line in stderr_logs).strip()

                if stdout and stderr:
                    return f"{stdout}\n{stderr}"
                if stdout:
                    return stdout
                if stderr:
                    return stderr
                return ""
            except Exception as e:
                error_msg = str(e)
                # If sandbox appears to be dead, invalidate and retry
                if attempt < max_retries - 1 and ("dead" in error_msg.lower() or "timeout" in error_msg.lower() or "connection" in error_msg.lower()):
                    print(f"Sandbox error detected: {error_msg}. Restarting sandbox...")
                    invalidate_session_sandbox(session_id)
                    continue
                else:
                    return f"Unexpected Error: {error_msg}"

    @tool
    def read_file(path: str) -> str:
        """Reads and returns the content of a file at the specified path."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: The file at {path} was not found."
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @tool
    def write_file(path: str, content: str) -> str:
        """Writes content to a file, creating parent directories if they don't exist."""
        try:
            file_path = Path(path)
            # Create directories if they are missing (similar to 'mkdir -p')
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding='utf-8')
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing to {path}: {str(e)}"
        
    @tool
    def browse_url(url: str) -> str:
        """Browse a url and return content"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://docs.python.org/3/library/asyncio.html", wait_until="networkidle")
            raw_text = page.locator("body").inner_text()
            clean_text = re.sub(r'\s+', ' ', raw_text).strip()
            result = clean_text[:4000]
            browser.close()
            return result
    
    tavily_tool = TavilySearch(
        api_key = os.getenv("TAVILY_API_KEY"),
        max_results = 5
    )

    return [bash, read_file, write_file, browse_url, tavily_tool]

__all__ = ['create_tools']