"""Safely download a public webpage for private, local-model summarization."""

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx


class PageFetchError(RuntimeError):
    """A URL could not be fetched safely or did not contain readable text."""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "footer", "header"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "footer", "header"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise PageFetchError("Please provide a public http or https webpage link.")
    if parsed.port not in (None, 80, 443):
        raise PageFetchError("Links using custom network ports are not supported.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))}
    except OSError as exc:
        raise PageFetchError("I could not find that webpage. Check the link and try again.") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise PageFetchError("For safety, I can only open public websites, not private network addresses.")


async def fetch_webpage_text(url: str) -> tuple[str, str]:
    current = url
    headers = {"User-Agent": "MiniJARVIS/1.0 (public page summary)"}
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False, headers=headers) as client:
            for _ in range(4):
                _validate_public_url(current)
                async with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise PageFetchError("That webpage redirected without a valid destination.")
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        raise PageFetchError("That link is not a readable webpage. Please send an HTML page link.")
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > 1_000_000:
                            break
                        chunks.append(chunk)
                    body = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
                    parser = _TextExtractor()
                    parser.feed(body)
                    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
                    if not text:
                        raise PageFetchError("I could open the link, but it has no readable page text.")
                    return current, text[:12000]
        raise PageFetchError("That webpage redirected too many times.")
    except PageFetchError:
        raise
    except (httpx.HTTPError, UnicodeError, ValueError) as exc:
        raise PageFetchError("I could not load that webpage. Check that the link is public and try again.") from exc


def find_url(message: str) -> str | None:
    match = re.search(r"https?://[^\s<>\"']+", message, flags=re.IGNORECASE)
    return match.group(0).rstrip(".,!?;:)]}") if match else None
