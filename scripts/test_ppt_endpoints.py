import json
import sys
from typing import List

import httpx


BASE_URL = "http://localhost:8000"
OUTLINE_ENDPOINT = f"{BASE_URL}/api/ppt/outline/generate"
SLIDES_ENDPOINT = f"{BASE_URL}/api/ppt/slides/generate"


def read_sse_content_lines(lines: List[str]) -> List[str]:
    contents: List[str] = []
    for line in lines:
        if line.startswith("data: "):
            payload = line[6:]
            try:
                data = json.loads(payload)
                content = data.get("content")
                if content:
                    contents.append(content)
            except json.JSONDecodeError:
                continue
    return contents


def test_outline() -> bool:
    payload = {
        "prompt": "人工智能发展概述",
        "numberOfCards": 6,
        "language": "zh-CN",
    }

    print("[outline] Requesting SSE stream...")
    try:
        with httpx.Client(timeout=60) as client:
            with client.stream("POST", OUTLINE_ENDPOINT, json=payload) as resp:
                if resp.status_code != 200:
                    print(f"[outline] FAIL: status={resp.status_code} body={resp.text}")
                    return False

                lines = []
                for line in resp.iter_lines():
                    if line:
                        lines.append(line)
                    if len(lines) >= 5:
                        break

        contents = read_sse_content_lines(lines)
        if not contents:
            print("[outline] FAIL: no content chunks found in SSE stream")
            return False

        print("[outline] OK: received content chunks")
        return True

    except Exception as exc:
        print(f"[outline] FAIL: {exc}")
        return False


def test_slides() -> bool:
    payload = {
        "title": "AI in Healthcare",
        "outline": [
            "背景与趋势",
            "核心应用场景",
            "关键技术与挑战",
            "监管与伦理",
            "未来展望",
            "结论",
        ],
        "language": "en-US",
        "tone": "professional",
        "numSlides": 6,
    }

    print("[slides] Requesting NDJSON stream...")
    try:
        with httpx.Client(timeout=120) as client:
            with client.stream("POST", SLIDES_ENDPOINT, json=payload) as resp:
                if resp.status_code != 200:
                    print(f"[slides] FAIL: status={resp.status_code} body={resp.text}")
                    return False

                events = []
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        events.append({"type": "raw", "data": line})
                    if len(events) >= 5:
                        break

        if not events:
            print("[slides] FAIL: no events received")
            return False

        has_error = any(e.get("type") == "error" for e in events if isinstance(e, dict))
        if has_error:
            print(f"[slides] FAIL: error event received: {events}")
            return False

        print("[slides] OK: received events")
        return True

    except Exception as exc:
        print(f"[slides] FAIL: {exc}")
        return False


def main() -> int:
    outline_ok = test_outline()
    slides_ok = test_slides()

    if outline_ok and slides_ok:
        print("\nAll tests passed.")
        return 0

    print("\nSome tests failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
