import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "paper_db.sqlite")

#データベースがないときに自動的に作成する
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            year TEXT,
            source TEXT,
            query TEXT,
            searched_at TEXT,
            pdf_path TEXT,
            text_path TEXT,
            summary_path TEXT,
            downloaded INTEGER,
            summarized INTEGER,
            url TEXT,
            pdf_url TEXT,
            background TEXT,
            purpose TEXT,
            novelty TEXT,
            method TEXT,
            results TEXT,
            discussion TEXT,
            concerns TEXT,
            conclusion TEXT,
            future_work TEXT,
            keywords TEXT
        )
    ''')
    conn.commit()
    conn.close()

# データベースの初期化
def insert_or_update_paper(paper_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO papers (
            id, title, authors, year, source, query, searched_at,
            pdf_path, text_path, summary_path, downloaded, summarized,
            url, pdf_url,
            background, purpose, novelty, method, results,
            discussion, concerns, conclusion, future_work, keywords
        ) VALUES (
            :id, :title, :authors, :year, :source, :query, :searched_at,
            :pdf_path, :text_path, :summary_path, :downloaded, :summarized,
            :url, :pdf_url,
            :background, :purpose, :novelty, :method, :results,
            :discussion, :concerns, :conclusion, :future_work, :keywords
        )
    ''', paper_dict)
    conn.commit()
    conn.close()

# 更新論文のステータス
def update_paper_status(paper_id, pdf_path=None, text_path=None, summary_path=None, downloaded=None, summarized=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updates = []
    params = {}

    if pdf_path is not None:
        updates.append("pdf_path = :pdf_path")
        params["pdf_path"] = pdf_path
    if text_path is not None:
        updates.append("text_path = :text_path")
        params["text_path"] = text_path
    if summary_path is not None:
        updates.append("summary_path = :summary_path")
        params["summary_path"] = summary_path
    if downloaded is not None:
        updates.append("downloaded = :downloaded")
        params["downloaded"] = downloaded
    if summarized is not None:
        updates.append("summarized = :summarized")
        params["summarized"] = summarized

    if not updates:
        conn.close()
        return

    params["id"] = paper_id
    sql = f'''
        UPDATE papers
        SET {", ".join(updates)}
        WHERE id = :id
    '''
    c.execute(sql, params)
    conn.commit()
    conn.close()


# 要約をファイルに保存
def update_summary_to_db(paper_id, summary):
    import json
    keywords_json = json.dumps(summary.get("キーワード", []), ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE papers SET
            background = :background,
            purpose = :purpose,
            novelty = :novelty,
            method = :method,
            results = :results,
            discussion = :discussion,
            concerns = :concerns,
            conclusion = :conclusion,
            future_work = :future_work,
            keywords = :keywords
        WHERE id = :id
    ''', {
        "background": summary.get("背景", ""),
        "purpose": summary.get("目的", ""),
        "novelty": summary.get("新規性", ""),
        "method": summary.get("方法", ""),
        "results": summary.get("結果", ""),
        "discussion": summary.get("考察", ""),
        "concerns": summary.get("懸念点", ""),
        "conclusion": summary.get("結論", ""),
        "future_work": summary.get("今後の展望", ""),
        "keywords": keywords_json,
        "id": paper_id
    })
    conn.commit()
    conn.close()

def fetch_all_papers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM papers ORDER BY searched_at DESC")
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    # dictのリストで返す
    papers = [dict(zip(columns, row)) for row in rows]
    return papers
