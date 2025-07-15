# utils/pdf_downloader.py

import os
import requests
import re

def sanitize_filename(filename: str) -> str:
    """
    ファイル名に使えない文字をアンダースコアに置換し、安全なファイル名に変換する。
    Windowsで禁止されている文字: \ / : * ? " < > |
    """
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def download_pdf(pdf_url: str, save_dir: str, filename: str = None) -> str | None:
    """
    PDFを指定フォルダに保存し、保存したパスを返す。
    filenameが指定されなければURLの末尾から取得。
    失敗した場合は None を返す。
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if filename is None:
        filename = pdf_url.split("/")[-1].split("?")[0]

    # ファイル名を安全化＋拡張子チェック
    filename = sanitize_filename(filename)
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    save_path = os.path.join(save_dir, filename)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(pdf_url, headers=headers, timeout=10)
        r.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(r.content)

        return save_path

    except requests.exceptions.RequestException as e:
        print(f"❌ PDFのダウンロードに失敗しました: {e}")
        print("🔍 手動でPDFをダウンロードしてアップロードしてください。URLによる取得がブロックされています。")
        return None

