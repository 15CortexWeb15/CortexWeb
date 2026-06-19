"""Knowledge retrieval for CORTEX using Wikipedia."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from core.memory import MemoryManager


class WikipediaSearch:
    """Search Wikipedia and return a concise summary."""

    API_URL = "https://en.wikipedia.org/w/api.php"
    CACHE_KEY = "wikipedia_cache"

    def __init__(self) -> None:
        self.memory = MemoryManager()
        self.memory.load()
        self.cache = self.memory.recall(self.CACHE_KEY) or {}

    def search(self, query: str, offline_only: bool = False) -> Optional[str]:
        """Search Wikipedia and return a short extract from the first result."""
        if not query:
            return None

        normalized_query = self._normalize_query(query)
        cache_key = normalized_query.strip().lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        if offline_only:
            return None

        search_url = self._build_url(
            {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": normalized_query,
                "srlimit": "5",
                "utf8": "1",
            }
        )
        search_data = self._fetch_json(search_url)
        if not search_data:
            return None

        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return self._no_results_summary(query)

        best_result = self._select_best_result(search_results, normalized_query)
        pageid = best_result.get("pageid")
        title = best_result.get("title")
        if pageid and title:
            extract_url = self._build_url(
                {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "exintro": "1",
                    "explaintext": "1",
                    "pageids": str(pageid),
                    "utf8": "1",
                }
            )
            extract_data = self._fetch_json(extract_url)
            if extract_data:
                pages = extract_data.get("query", {}).get("pages", {})
                page = pages.get(str(pageid), {})
                extract = page.get("extract")
                if extract:
                    result = self._format_summary(title, extract)
                    self._cache_query(cache_key, result)
                    return result

        result = self._related_topics_summary(query, search_results)
        self._cache_query(cache_key, result)
        return result

    def _cache_query(self, query: str, result: str) -> None:
        self.cache[query] = result
        self.memory.remember(self.CACHE_KEY, self.cache)

    def _build_url(self, params: dict) -> str:
        return f"{self.API_URL}?{urllib.parse.urlencode(params)}"

    def _format_summary(self, title: str, extract: str) -> str:
        text = " ".join(line.strip() for line in extract.splitlines() if line.strip())
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 2:
            text = " ".join(sentences[:2])
        else:
            text = text.strip()

        if not text.endswith(('.', '!', '?')):
            text = text + '.'

        return text

    def _normalize_query(self, query: str) -> str:
        query_lower = query.strip().lower()
        # common query correction for fuzzy or typoed user input
        query_lower = query_lower.replace('healhty', 'healthy').replace('alchol', 'alcohol')
        query_lower = re.sub(r"\b(healthy|health)\b\s+to\s+eat\s+([a-z ]+?)\??$", r"\2", query_lower)
        query_lower = re.sub(r"^is it healthy to eat\s+([a-z ]+?)\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^is\s+([a-z ]+?)\s+healthy\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^can i\s+(eat|drink|use|take)\s+([a-z ]+?)\?*$", r"\2", query_lower)
        query_lower = re.sub(r"^should i\s+(eat|drink|use|take)\s+([a-z ]+?)\?*$", r"\2", query_lower)
        query_lower = re.sub(r"^is it safe to\s+(eat|drink|use|take)\s+([a-z ]+?)\?*$", r"\2", query_lower)
        query_lower = re.sub(r"^what does (?:the )?(.+?) mean\?*$", r"\1 meaning", query_lower)
        query_lower = re.sub(r"^what is the meaning of (.+?)\?*$", r"\1 meaning", query_lower)
        query_lower = re.sub(r"^what does (?:the )?(.+?) do\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^what is the difference between (.+?) and (.+?)\?*$", r"\1 vs \2", query_lower)
        query_lower = re.sub(r"^compare (.+?) and (.+?)\?*$", r"\1 vs \2", query_lower)
        query_lower = re.sub(r"^what are the benefits of (.+?)\?*$", r"\1 benefits", query_lower)
        query_lower = re.sub(r"^what are the risks of (.+?)\?*$", r"\1 risks", query_lower)
        query_lower = re.sub(r"^what are the advantages of (.+?)\?*$", r"\1 advantages", query_lower)
        query_lower = re.sub(r"^what are the disadvantages of (.+?)\?*$", r"\1 disadvantages", query_lower)
        query_lower = re.sub(r"^where can i find (.+?)\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^when did (?:the )?first (.+?) happen\?*$", r"first \1", query_lower)
        query_lower = re.sub(r"^when did (.+?)\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^how (?:can|do) i (?:build|make|create|design) (.+?)\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^how to (?:build|make|create|design) (.+?)\?*$", r"\1", query_lower)
        query_lower = re.sub(r"^what does cpu mean\?*$", r"central processing unit", query_lower)
        query_lower = re.sub(r"^what does gpu mean\?*$", r"graphics processing unit", query_lower)
        query_lower = re.sub(r"^what does ram mean\?*$", r"random access memory", query_lower)
        query_lower = re.sub(r"^what does api mean\?*$", r"application programming interface", query_lower)

        should_match = re.search(r"\bshould i\s+(?:drink|eat|use|take|have)\s+([a-z ]+?)\??$", query_lower)
        if should_match:
            item = should_match.group(1).strip()
            return f"{item} health benefits"

        can_match = re.search(r"\b(?:can i|could i|may i)\s+(?:drink|eat|use|take|have)\s+([a-z ]+?)\??$", query_lower)
        if can_match:
            item = can_match.group(1).strip()
            return f"{item} health effects"

        match = re.search(r"what does (?:the )?name\s+([a-z'-]+)\s+mean", query_lower)
        if match:
            name = match.group(1).strip()
            return f"{name} name"

        match = re.search(r"meaning of (?:the )?name\s+([a-z'-]+)", query_lower)
        if match:
            name = match.group(1).strip()
            return f"{name} name"

        inventor_match = re.search(r"\bwho invented\s+(.+?)\?*$", query_lower)
        if inventor_match:
            item = inventor_match.group(1).strip()
            return f"{item} inventor"

        discover_match = re.search(r"\bwho discovered\s+(.+?)\?*$", query_lower)
        if discover_match:
            item = discover_match.group(1).strip()
            return f"{item} discoverer"

        why_match = re.search(r"\bwhy is\s+(.+?)\?*$", query_lower)
        if why_match:
            item = why_match.group(1).strip()
            return f"{item} cause"

        why_does_match = re.search(r"\bwhy does\s+(.+?)\?*$", query_lower)
        if why_does_match:
            item = why_does_match.group(1).strip()
            return f"{item} reason"

        question_match = re.match(
            r"^(?:what is|what are|who is|who was|where is|when is|why is|why does|why can|define|explain|is it|are|should|can|could|may|does|do)\s+(.+?)\?*$",
            query_lower,
        )
        if question_match:
            return question_match.group(1).strip()

        return query_lower

    def _select_best_result(self, search_results: list[dict], query: str) -> dict:
        query_lower = query.lower()
        name_match = re.search(r"(?:name\s+)([a-z'-]+)", query_lower)
        if name_match:
            base_name = name_match.group(1).strip()
            for candidate in search_results:
                title = candidate.get("title", "")
                if re.fullmatch(fr"{re.escape(base_name)}\s*\(name\)", title, re.IGNORECASE):
                    return candidate
            for candidate in search_results:
                title = candidate.get("title", "")
                if base_name.lower() in title.lower() and "name" in title.lower():
                    return candidate

        cleaned_query = re.sub(r"[^a-z0-9 ]", "", query_lower)
        query_words = set(cleaned_query.split())
        best_candidate = search_results[0]
        best_score = -1

        if any(keyword in query_lower for keyword in (" inventor", " discoverer", "invention", "discovered", "invented", "cause", "reason")):
            subject = re.sub(r"\b(inventor|discoverer|invention|discovered|invented|cause|reason)\b", "", query_lower).strip()
            subject = re.sub(r"\b(of|the|a|an|for|about|in|on|with)\b", "", subject).strip()
            if subject:
                for candidate in search_results:
                    title = candidate.get("title", "")
                    snippet = self._clean_snippet(candidate.get("snippet", "")).lower()
                    if subject in title.lower() and any(term in snippet for term in ("inventor", "invented", "discoverer", "discovered", "cause", "reason")):
                        return candidate

        health_subject_match = re.match(r"^([a-z0-9 ]+?)\s+(?:safety|health|nutrition|benefits|effects|risk|risks|safe|healthy)\b", query_lower)
        if health_subject_match:
            subject = health_subject_match.group(1).strip()
            for candidate in search_results:
                title = candidate.get("title", "").lower()
                if subject in title:
                    return candidate

        stopwords = {
            "a", "an", "the", "of", "and", "or", "for", "to", "in", "on", "with",
            "is", "are", "was", "were", "be", "by", "do", "does", "did", "can", "could",
            "may", "should", "would", "will", "have", "has", "had", "this", "that", "these",
            "those", "it", "what", "who", "why", "how", "when", "where", "if", "as", "from",
            "into", "about", "than", "then", "most", "many", "other", "some", "health", "healthy",
            "safety", "effects", "benefits", "nutrition", "food", "how", "build", "make", "create",
            "design", "use", "using", "meaning", "compare", "vs", "versus", "happen", "first",
            "question", "item", "something", "someone", "things",
        }
        subject_terms = [
            word for word in cleaned_query.split()
            if word not in stopwords and len(word) > 1
        ]
        if not subject_terms:
            subject_terms = [word for word in cleaned_query.split() if len(word) > 1]

        primary_subject = None
        if subject_terms:
            # Prefer the longest meaningful word as the subject for better matching.
            primary_subject = max(subject_terms, key=len)

        if primary_subject:
            for candidate in search_results:
                title = candidate.get("title", "").lower()
                if primary_subject in title:
                    return candidate

        for candidate in search_results:
            title = candidate.get("title", "").lower()
            snippet = self._clean_snippet(candidate.get("snippet", "")).lower()
            title_words = set(re.sub(r"[^a-z0-9 ]", "", title).split())
            snippet_words = set(re.sub(r"[^a-z0-9 ]", "", snippet).split())
            score = len(query_words & title_words) * 3 + len(query_words & snippet_words)
            if any(term in title for term in subject_terms):
                score += 2
            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate

    def _related_topics_summary(self, query: str, search_results: list[dict]) -> str:
        lines = [
            f"I could not find a direct Wikipedia article for '{query}'. Here are related topics and what they suggest:",
        ]
        for result in search_results[:3]:
            title = result.get("title", "Unknown topic")
            snippet = self._clean_snippet(result.get("snippet", ""))
            if snippet:
                lines.append(f"- {title}: {snippet}.")
            else:
                lines.append(f"- {title}.")

        lines.append(
            "These results show what the query may refer to. Try a more specific phrase or use one of the related topics above."
        )
        return "\n".join(lines)

    def _no_results_summary(self, query: str) -> str:
        return (
            f"I couldn't find a Wikipedia match for '{query}'. "
            "It may refer to an uncommon term or a very specific concept. "
            "Try asking in a different way or provide more detail."
        )

    def _clean_snippet(self, snippet: str) -> str:
        return re.sub(r'<.*?>', '', snippet or '').strip()

    def _fetch_json(self, url: str) -> Optional[dict]:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CORTEX/1.0"})
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.URLError:
            return None
        except json.JSONDecodeError:
            return None


class BritannicaSearch:
    """Search Encyclopaedia Britannica for a concise summary."""

    BASE_URL = "https://www.britannica.com"
    SEARCH_PATH = "/search?query="
    CACHE_KEY = "britannica_cache"

    def __init__(self) -> None:
        self.memory = MemoryManager()
        self.memory.load()
        self.cache = self.memory.recall(self.CACHE_KEY) or {}

    def search(self, query: str, offline_only: bool = False) -> Optional[str]:
        if not query or offline_only:
            return None

        normalized_query = self._normalize_query(query)
        cache_key = normalized_query.strip().lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        search_url = f"{self.BASE_URL}{self.SEARCH_PATH}{urllib.parse.quote(normalized_query)}"
        search_html = self._fetch_html(search_url)
        if not search_html:
            return None

        article_path = self._extract_article_path(search_html)
        if not article_path:
            return None

        article_url = f"{self.BASE_URL}{article_path}"
        article_html = self._fetch_html(article_url)
        if not article_html:
            return None

        summary = self._extract_article_summary(article_html)
        if not summary:
            return None

        result = (
            f"According to Encyclopaedia Britannica, {normalized_query.title()}: {summary}\n\n"
            f"Source: {article_url}"
        )
        self._cache_query(cache_key, result)
        return result

    def _cache_query(self, query: str, result: str) -> None:
        self.cache[query] = result
        self.memory.remember(self.CACHE_KEY, self.cache)

    def _fetch_html(self, url: str) -> Optional[str]:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CORTEX/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.URLError:
            return None

    def _extract_article_path(self, html: str) -> Optional[str]:
        patterns = [
            r'href="(/topic/[^"]+)"',
            r'href="(/biography/[^"]+)"',
            r'href="(/science/[^"]+)"',
            r'href="(/technology/[^"]+)"',
            r'href="(/history/[^"]+)"',
            r'href="(/[^\"?]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                path = match.group(1)
                if path.startswith("/search"):
                    continue
                return path
        return None

    def _extract_article_summary(self, html: str) -> Optional[str]:
        paragraphs = re.findall(r"<p>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
        for paragraph in paragraphs:
            cleaned = self._clean_html(paragraph)
            if len(cleaned) >= 120:
                sentences = re.split(r'(?<=[.!?])\s+', cleaned)
                summary = " ".join(sentences[:2]).strip()
                if summary:
                    return summary if summary.endswith(('.', '!', '?')) else f"{summary}."
        return None

    def _normalize_query(self, query: str) -> str:
        query_lower = query.strip().lower()
        question_match = re.match(
            r"^(?:what is|what are|who is|who was|where is|when is|define|explain|tell me about)\s+(.+?)\?*$",
            query_lower,
        )
        if question_match:
            return question_match.group(1).strip()
        return query

    def _clean_html(self, html: str) -> str:
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'&nbsp;|&#160;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class KnowledgeSearch:
    """Unified knowledge retrieval for CORTEX."""

    def __init__(self) -> None:
        self.wikipedia = WikipediaSearch()
        self.britannica = BritannicaSearch()

    def search(self, query: str, offline_only: bool = False) -> Optional[str]:
        if not query:
            return None

        result = self.wikipedia.search(query, offline_only=offline_only)
        if result:
            return result

        if offline_only:
            return None

        result = self.britannica.search(query, offline_only=offline_only)
        if result:
            return result

        return None
