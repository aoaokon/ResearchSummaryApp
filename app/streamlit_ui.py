# app/streamlit_ui.py
import streamlit as st
import pandas as pd
import tempfile
import sys
import os
import json
import requests
import platform
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.arxiv_search import search_arxiv
from utils.semantic_scholar_search import search_semantic_scholar
from utils.pdf_text_extractor import extract_text_from_pdf, save_text_to_file
from utils.summarizer import summarize_text
from utils.pdf_downloader import download_pdf
from utils.summarizer import save_summary_to_file
from utils.db_manager import init_db, insert_or_update_paper, update_paper_status, update_summary_to_db, fetch_all_papers, delete_paper

init_db()  # データベースの初期化

st.set_page_config(page_title="論文検索＆PDF要約", layout="wide")
st.title("📚 論文検索＆PDF要約アプリ")

# ---------------------------------------
# 🔍 セクション1：キーワード検索（arXiv + Semantic Scholar）
# ---------------------------------------
st.header("🔍 キーワードから論文を検索")

keyword = st.text_input("キーワードを入力してください", placeholder="例: Transformer, Climate Change")
max_results = st.slider("論文を検索するソースはarXivとsemantic scholarです。それぞれのソースで取得する論文数を選択してください。その中からPDFがダウンロードできるもののみ抽出します。", 1, 10, 5)

all_papers = []

if keyword:
    st.success(f"検索キーワード：{keyword}")

    with st.spinner("論文検索中..."):
        arxiv_results = search_arxiv(keyword, max_results=max_results)
        try:
            semsch_results = search_semantic_scholar(keyword, limit=max_results)
        except requests.exceptions.HTTPError as e:
            st.warning(f"Semantic Scholar API制限のため、Semantic Scholarの検索はスキップします。: {e}")
            semsch_results = []

        all_papers = arxiv_results + semsch_results

        for paper in all_papers:
            paper_id = f"{paper['source']}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            paper_record = {
                "id": paper_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "source": paper["source"],
                "query": keyword,
                "searched_at": datetime.now().isoformat(),
                "pdf_path": "",
                "text_path": "",
                "summary_path": "",
                "downloaded": 0,
                "summarized": 0,
                "url": paper.get("url", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "background": "",   # 空文字列で初期化
                "purpose": "",
                "novelty": "",
                "method": "",
                "results": "",
                "discussion": "",
                "concerns": "",
                "conclusion": "",
                "future_work": "",
                "keywords": json.dumps([], ensure_ascii=False)  # 空リストのJSON文字列
            }
            insert_or_update_paper(paper_record)

        if all_papers:
            st.write(f"📄 PDF取得可能な論文数: {len(all_papers)} 件")

            for paper in all_papers:
                st.markdown(f"### [{paper['title']}]({paper['url']})")
                st.markdown(f"- 著者: {paper['authors']}")
                st.markdown(f"- 年: {paper['year']} / 雜誌: {paper['venue']} / ソース: {paper['source']}")
                st.markdown(f"- [📄 PDFを開く]({paper['pdf_url']})")
                st.markdown("---")

            df = pd.DataFrame(all_papers)
            st.dataframe(df[["source", "title", "authors", "year", "venue", "url", "pdf_url"]])

            # OSによってエンコーディングを切り替え
            if platform.system() == "Windows":
                csv = df.to_csv(index=False, encoding="shift_jis").encode("cp932")
                file_name = f"{keyword}_papers_sjis.csv"
            else:
                csv = df.to_csv(index=False).encode("utf-8")
                file_name = f"{keyword}_papers.csv"

            st.download_button("📅 論文一覧をCSVでダウンロード", data=csv, file_name=file_name, mime="text/csv")

            if st.button("🔽 検索結果のPDFを一括ダウンロード＆要約開始"):
                summaries = []

                for paper in all_papers:
                    try:
                        paper_id = f"{paper['source']}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                        safe_title = paper['title'].replace(' ', '_').replace('/', '_')[:30]
                        filename = f"{paper['source']}_{paper['year']}_{safe_title}.pdf"

                        pdf_path = download_pdf(pdf_url=paper["pdf_url"], save_dir="data/pdf", filename=filename)

                        if pdf_path is None or not os.path.exists(pdf_path):
                            st.error(f"❌ PDFのダウンロードに失敗しました: {paper['title']}。")
                            continue

                        update_paper_status(paper_id, pdf_path=pdf_path, downloaded=1)

                        text = extract_text_from_pdf(pdf_path)

                        text_filename = f"{paper['source']}_{paper['year']}_{safe_title}.txt"
                        text_path = os.path.join("data/text", text_filename)
                        save_text_to_file(text, text_path)

                        update_paper_status(paper_id, text_path=text_path)

                        summary = summarize_text(text)
                        summary["タイトル"] = paper["title"]
                        summary["ソース"] = paper["source"]
                        summary["年"] = paper["year"]
                        summaries.append(summary)

                        summary_path = save_summary_to_file(summary, pdf_path)
                        # sammaryの詳細をDBに保存
                        update_summary_to_db(paper_id, summary)
                        #sammaryファイルパスと要約済みフラグを更新
                        update_paper_status(paper_id, summary_path=summary_path, summarized=1)

                        st.success(f"✅ {paper['title']} の要約が完了しました。")

                    except Exception as e:
                        st.error(f"❌ {paper['title']} の処理でエラーが発生しました: {e}")

                if summaries:
                    df_summary = pd.DataFrame(summaries)
                    st.subheader("📝 要約結果")
                    st.dataframe(df_summary)

                    csv_summary = df_summary.to_csv(index=False).encode("utf-8")
                    st.download_button("📅 要約結果をCSVでダウンロード", data=csv_summary, file_name="summaries.csv", mime="text/csv")


        else:
            st.warning("PDF付きの論文が見つかりませんでした。")

# ---------------------------------------
# 📄 セクション2：PDFをアップロードして要約
# ---------------------------------------
st.header("🧠 PDFをアップロードして要約")

uploaded_files = st.file_uploader("📎 PDFファイルをアップロード（複数可）", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    summaries = []

    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        with st.spinner(f"{uploaded_file.name} を要約中..."):
            try:
                # テキスト抽出
                text = extract_text_from_pdf(tmp_file_path)

                # テキスト保存
                safe_name = uploaded_file.name.replace(' ', '_').replace('/', '_')[:30]
                text_path = os.path.join("data/text", safe_name + ".txt")
                save_text_to_file(text, text_path)

                # 要約生成
                summary = summarize_text(text)
                summary["ファイル名"] = uploaded_file.name
                summaries.append(summary)

                # 要約をJSONファイルに保存
                summary_path = save_summary_to_file(summary, tmp_file_path)

                # DB保存処理（ファイルアップロードなのでIDがない場合はファイル名で仮ID）
                paper_id = safe_name  # もしID体系があるなら適宜変えてください

                # まず論文レコードを登録 or 更新
                paper_record = {
                    "id": paper_id,
                    "title": uploaded_file.name,
                    "authors": "",
                    "year": "",
                    "source": "uploaded_pdf",
                    "query": "",
                    "searched_at": datetime.now().isoformat(),
                    "pdf_path": tmp_file_path,
                    "text_path": text_path,
                    "summary_path": summary_path,
                    "downloaded": 1,
                    "summarized": 1,
                    "url": "",
                    "pdf_url": "",
                    "background": summary.get("背景", ""),
                    "purpose": summary.get("目的", ""),
                    "novelty": summary.get("新規性", ""),
                    "method": summary.get("方法", ""),
                    "results": summary.get("結果", ""),
                    "discussion": summary.get("考察", ""),
                    "concerns": summary.get("懸念点", ""),
                    "conclusion": summary.get("結論", ""),
                    "future_work": summary.get("今後の展望", ""),
                    "keywords": json.dumps(summary.get("キーワード", []), ensure_ascii=False)
                }
                insert_or_update_paper(paper_record)

            except Exception as e:
                st.error(f"{uploaded_file.name} の要約に失敗しました：{e}")

    if summaries:
        df_summary = pd.DataFrame(summaries)
        st.subheader("📝 要約結果")
        st.dataframe(df_summary)

        # OSによってエンコーディングを切り替え
        if platform.system() == "Windows":
            csv_summary = df_summary.to_csv(index=False, encoding="shift_jis").encode("cp932")
            file_name = "summaries_sjis.csv"
        else:
            csv_summary = df_summary.to_csv(index=False).encode("utf-8")
            file_name = "summaries.csv"

        st.download_button("📅 要約結果をCSVでダウンロード", data=csv_summary, file_name=file_name, mime="text/csv")


# ---------------------------------------
# 📄 セクション3：保存ずみの論文一覧の表示
# ---------------------------------------

st.header("📚 保存済み論文一覧")

papers = fetch_all_papers()

if st.session_state.get("just_deleted"):
    st.success(f"{st.session_state['deleted_count']}件の論文を削除しました。")
    del st.session_state["deleted_count"]
    del st.session_state["just_deleted"]
    if "selected_ids" in st.session_state:
        del st.session_state["selected_ids"]

if papers:
    df = pd.DataFrame(papers)
    display_cols = [
    "id", "title", "authors", "year", "source", "downloaded", "summarized",
    "background", "purpose", "novelty", "method", "results", "discussion",
    "concerns", "conclusion", "future_work", "keywords"
    ]
    df_display = df[display_cols]


    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()

    # グリッド表示
    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme="material",
        height=400,
    )

    selected_rows = grid_response['selected_rows']  # 選択された行はDataFrame

    if selected_rows is not None and not selected_rows.empty:
    # DataFrameを辞書のリストに変換
        rows_list = selected_rows.to_dict(orient="records")
        selected_ids = [row['id'] for row in rows_list]

        st.session_state["selected_ids"] = selected_ids#セッションに保存（削除直後のrerunで消えないように）
        st.write(f"選択中の論文（{len(selected_ids)}件）:")
        st.dataframe(selected_rows)

        # ここに要約表示を追加
        for row in rows_list:
            with st.expander(f"📝 要約: {row['title']}"):
                st.markdown(f"- **背景**: {row.get('background', '')}")
                st.markdown(f"- **目的**: {row.get('purpose', '')}")
                st.markdown(f"- **新規性**: {row.get('novelty', '')}")
                st.markdown(f"- **方法**: {row.get('method', '')}")
                st.markdown(f"- **結果**: {row.get('results', '')}")
                st.markdown(f"- **考察**: {row.get('discussion', '')}")
                st.markdown(f"- **懸念点**: {row.get('concerns', '')}")
                st.markdown(f"- **結論**: {row.get('conclusion', '')}")
                st.markdown(f"- **今後の展望**: {row.get('future_work', '')}")
                st.markdown(f"- **キーワード**: {row.get('keywords', '')}")


        # 削除ボタンの処理
        if st.button("🗑️ 選択した論文を一括削除"):
            try:
                for pid in st.session_state.get("selected_ids", []):
                    delete_paper(pid)
                st.session_state["deleted_count"] = len(st.session_state["selected_ids"])
                st.session_state["just_deleted"] = True
                st.rerun()
            except Exception as e:
                st.error(f"削除中にエラーが発生しました: {e}")

        # 削除後のメッセージ表示
        if "deleted_count" in st.session_state:
            st.success(f"{st.session_state['deleted_count']}件の論文を削除しました。")
            del st.session_state["deleted_count"]
    else:
        st.info("削除したい論文をチェックボックスで選択してください。")
else:
    st.info("まだ論文データがありません。")