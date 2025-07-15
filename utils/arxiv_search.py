#arxivでキーワード検索を行う関数
import feedparser
from urllib.parse import quote

def search_arxiv(keyword: str, max_results: int = 10):#10件をデフォルトに設定
    base_url = "http://export.arxiv.org/api/query"# arXivのAPIエンドポイント
    query = f"search_query=all:{quote(keyword)}&start=0&max_results={max_results}"
    url = f"{base_url}?{query}"

    feed = feedparser.parse(url)
    papers = []

    for entry in feed.entries:
        pdf_url = next((link.href for link in entry.links if link.type == "application/pdf"), None)
        if pdf_url:
            papers.append({
                "source": "arXiv",
                "title": entry.title,
                "authors": ", ".join(author.name for author in entry.authors),
                "year": entry.published[:4],
                "venue": "arXiv",
                "url": entry.id,
                "pdf_url": pdf_url,
                "summary": entry.summary
            })

    return papers

