# semantic scholarでキーワードに対する論文検索を行う
import requests

def search_semantic_scholar(keyword: str, limit: int = 10):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"# Semantic ScholarのAPIエンドポイント
    params = {
        "query": keyword,
        "limit": limit,
        "fields": "title,authors,year,venue,url,openAccessPdf,abstract"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json().get("data", [])
    papers = []

    for paper in results:
        pdf_url = paper.get("openAccessPdf", {}).get("url", "")
        if pdf_url:
            papers.append({
                "source": "SemanticScholar",
                "title": paper.get("title", ""),
                "authors": ", ".join(a["name"] for a in paper.get("authors", [])),
                "year": str(paper.get("year", "")),
                "venue": paper.get("venue", "不明"),
                "url": paper.get("url", ""),
                "pdf_url": pdf_url,
                "summary": paper.get("abstract", "")
            })

    return papers

