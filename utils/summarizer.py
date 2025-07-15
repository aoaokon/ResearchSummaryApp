# utils/summarizer.py

import openai
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- JSONスキーマをファイルから読み込む ---
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    JSON_SCHEMA = json.load(f)


def summarize_text(text: str) -> dict:
    """
    論文本文テキストをGPT-4に渡して、要約（10項目）を辞書形式で返す。
    schema.json で検証。
    """
    def clean_json_response(raw_response: str) -> str:
        return re.sub(r"^```json|```$", "", raw_response.strip())

    prompt = f"""
以下の論文本文を読み、次の10項目ごとに簡潔にまとめてください。

1. 背景
2. 目的
3. 新規性
4. 方法
5. 結果
6. 考察
7. 懸念点
8. 結論
9. 今後の展望
10. キーワード

出力は次の形式のJSONで返してください。キーワードはリスト形式で返してください：
{{
  "背景": "...",
  "目的": "...",
  "新規性": "...",
  "方法": "...",
  "結果": "...",
  "考察": "...",
  "懸念点": "...",
  "結論": "...",
  "今後の展望": "...",
  "キーワード": ["...", "...", "..."]
}}

以下が論文本文です：
{text}

必ずJSON形式のみを返してください。説明文や前置きは一切不要です。
"""

    try:
        print("\n=== 💬 GPTへのプロンプト送信内容 ===\n")
        print(prompt[:1000] + " ...（以下省略）")
        print("\n=== 🔄 要約開始 ===")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        message = response.choices[0].message.content

        print("\n=== 📥 GPTからの応答 ===\n")
        print(message)

        cleaned = clean_json_response(message)

        try:
            summary_dict = json.loads(cleaned)
            validate(instance=summary_dict, schema=JSON_SCHEMA)
            return summary_dict
        except json.JSONDecodeError as e:
            print("❌ JSONのパースに失敗しました：")
            print(cleaned)
            raise e
        except ValidationError as ve:
            print("❌ スキーマ検証に失敗しました：")
            print(f"原因: {ve.message}")
            raise ve

    except Exception as e:
        raise RuntimeError(f"要約失敗: {e}")


def sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を除去"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def save_summary_to_file(summary: dict, pdf_path: str) -> str:
    # ここでファイル名安全化関数を実装・呼び出しする必要があります
    def sanitize_filename(name: str) -> str:
        import re
        return re.sub(r'[\\/*?:"<>|]', "_", name)

    pdf_path = Path(pdf_path)
    safe_name = sanitize_filename(pdf_path.stem)
    output_dir = Path("data/summaries")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / f"{safe_name}.json"

    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ 要約結果を保存しました: {summary_path}")
        return str(summary_path)
    except Exception as e:
        print(f"❌ 要約結果の保存に失敗しました: {e}")
        raise e

