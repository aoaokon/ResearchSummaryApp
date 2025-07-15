# utils/pdf_text_extractor.py

import fitz  # PyMuPDF
import re
import os

def extract_text_from_pdf(file_path: str) -> str:
    """
    指定されたPDFファイルから本文を抽出し、整形したテキストを返す。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"指定されたPDFが存在しません: {file_path}")

    try:
        with fitz.open(file_path) as doc:
            raw_text = "\n".join(page.get_text() for page in doc)
    except Exception as e:
        raise RuntimeError(f"PDF読み取りエラー: {e}")

    return clean_pdf_text(raw_text)


def clean_pdf_text(text: str) -> str:
    """
    PDF抽出後のテキストを整形する（改行削除、記号除去など）。
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"[^\x00-\x7Fぁ-んァ-ン一-龥。、．，：；！？「」『』（）【】]", "", text)

    return text.strip()


def save_text_to_file(text: str, output_path: str):
    """
    テキストを指定されたパスに保存する。拡張子 .txt がなければ追加。
    """
    # 拡張子が .txt でなければ追加
    if not output_path.lower().endswith(".txt"):
        output_path += ".txt"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
