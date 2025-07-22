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
    c.execute("""
        SELECT id, title, authors, year, source, downloaded, summarized,
               background, purpose, novelty, method, results, discussion,
               concerns, conclusion, future_work, keywords
        FROM papers
    """)
    rows = c.fetchall()
    conn.close()

    # カラム名をつけて辞書のリストに変換
    papers = []
    for row in rows:
        papers.append({
            "id": row[0],
            "title": row[1],
            "authors": row[2],
            "year": row[3],
            "source": row[4],
            "downloaded": row[5],
            "summarized": row[6],
            "background": row[7],
            "purpose": row[8],
            "novelty": row[9],
            "method": row[10],
            "results": row[11],
            "discussion": row[12],
            "concerns": row[13],
            "conclusion": row[14],
            "future_work": row[15],
            "keywords": row[16],
        })
    return papers

def delete_paper(paper_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()
