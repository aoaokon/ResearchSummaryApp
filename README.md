# 📚 論文検索＆要約アプリ（ResearchSummaryApp）

このアプリは、**arXiv** や **Semantic Scholar** から論文を検索・取得し、**OpenAI API（ChatGPT）** によって論文を自動要約・データベースに保存する Streamlit アプリです。

---

## 🔧 セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourname/ResearchSummaryApp.git
cd ResearchSummaryApp
```

### 2. ライブラリのインストール
pip install -r requirements.txt


### 3. .envファイルの作成（OpenAI APIキー）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

### 4. アプリの起動
streamlit run app/streamlit_ui.py

###ディレクトリ構成
ResearchSummaryApp/
├── app/
│   └── streamlit_ui.py
├── utils/
│   ├── arxiv_search.py
│   ├── semantic_scholar_search.py
│   ├── summarizer.py
│   ├── pdf_text_extractor.py
│   ├── pdf_downloader.py
│   ├── schema.json
│   ├── croma_maneger.py
│   └── db_maneger.py
├── data/ 
│   ├── pdf/
│   │    ├── arXiv_1999_Multilevel_blocking_Monte_Carl.pdf
│   │    └── ・・・省略・・・
│   ├── text/
│   │    ├── arXiv_1999_Multilevel_blocking_Monte_Carl.txt
│   │    └── ・・・省略・・・
│   ├── json/
│   │    ├── arXiv_1999_Multilevel_blocking_Monte_Carl.json
│   │    └── ・・・省略・・・
|   └── paper_db.sqlite
├──.env
├──.gitignore
├──README.md
└── requirements.txt