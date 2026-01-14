import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
from groq import Groq

# ==========================================
# 🔑 設定・APIキー管理
# ==========================================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except FileNotFoundError:
    st.error("🚫 APIキーが見つかりません！")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = 'recruitment_db.csv'

# ==========================================
# 📋 項目定義
# ==========================================
COLUMNS = [
    "会社名", "カテゴリ(入力)", "媒体カテゴリ", "主な利用目的", "向いている採用フェーズ", 
    "ターゲット職種", "ターゲット年収帯", "経験レベル", "雇用形態対応",
    "課金形態", "初期費用", "最低契約期間", "想定採用単価", "予算コントロール",
    "登録ユーザー数", "アクティブユーザー傾向", "スカウト到達率",
    "応募導線の簡易さ", "スカウト送信数制限", "開封率目安",
    "管理画面の使いやすさ", "レポート機能", "CSV出力",
    "媒体連携数", "API連携可否", "(Indeed)連携可否", "審査の厳しさ",
    "サポート体制", "導入企業規模"
]

CATEGORY_OPTIONS = ["求人媒体", "スカウト媒体", "ATS", "その他"]

# ==========================================
# 🧠 AIエンジニアリング部分 (精度向上版)
# ==========================================
def research_with_groq(company_name, category_label):
    # ★ここが変更点：指示をめちゃくちゃ具体的にしました
    prompt = f"""
    あなたは日本の採用市場に精通したトップコンサルタントです。
    以下のサービスについて情報を検索し、JSON形式で回答してください。
    
    対象サービス名: {company_name}
    ユーザー指定カテゴリ: {category_label}

    出力JSONキー:
    {", ".join(COLUMNS)}

    【重要：データ抽出の絶対ルール】
    1. **ターゲット年収帯**:
       - ⚠️ 必ず「年収」で回答すること。「月収」は不可。
       - もし情報源が月給表記（例: 30万円）の場合は、×12〜14ヶ月分として年収換算すること（例: "360〜450万円"）。
       - 単位は「万円」で統一すること。
    
    2. **課金形態・費用**:
       - 具体的な金額が不明な場合は「要問い合わせ」とする。
       - 嘘の金額は書かないこと。

    3. **媒体カテゴリ**:
       - "{category_label}" という分類を尊重しつつ、具体的な種別（ダイレクトリクルーティング、掲載課金型など）を書くこと。

    4. **出力形式**:
       - 必ず有効なJSON形式のみを出力すること。余計な解説文は不要。
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "JSON形式で出力する厳格なアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.3, # ★創造性を少し下げて、事実重視の設定にしました
        )
        response_content = completion.choices[0].message.content
        data = json.loads(response_content)
        
        safe_data = {col: data.get(col, "-") for col in COLUMNS}
        safe_data["会社名"] = company_name
        safe_data["カテゴリ(入力)"] = category_label
        
        return safe_data

    except Exception as e:
        return {"会社名": company_name, "エラー": str(e)}

# ==========================================
# 🖥️ UI / アプリケーション本体
# ==========================================
def main():
    st.set_page_config(page_title="AI Recruitment Researcher", layout="wide")
    st.title("🚀 AI採用媒体・ATS比較ダッシュボード")
    st.markdown("powered by Groq (Llama 3.3)")

    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)

    tab1, tab2 = st.tabs(["📝 フロー1：一括登録・リサーチ", "📊 フロー2：比較表出力"])

    with tab1:
        st.header("1. 比較したいサービスを入力")
        st.markdown("以下の表に、調査したい**会社名**と**カテゴリ**を入力してください。")

        input_df = pd.DataFrame([
            {"会社名": "Green", "カテゴリ": "スカウト媒体"},
            {"会社名": "Indeed", "カテゴリ": "求人媒体"},
            {"会社名": "HRMOS", "カテゴリ": "ATS"},
        ])

        edited_df = st.data_editor(
            input_df,
            num_rows="dynamic",
            column_config={
                "カテゴリ": st.column_config.SelectboxColumn(
                    "カテゴリ",
                    options=CATEGORY_OPTIONS,
                    required=True,
                )
            },
            key="input_editor"
        )

        if st.button("🚀 AIリサーチを一括実行", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_rows = len(edited_df)
            new_rows = []

            for i, row in edited_df.iterrows():
                company = row["会社名"]
                category = row["カテゴリ"]

                if company:
                    if company in df["会社名"].values:
                        status_text.info(f"⏭️ {company} は既に登録済みです。スキップします。")
                    else:
                        status_text.info(f"🤖 AIが『{company}』を詳細分析中...")
                        result = research_with_groq(company, category)
                        new_rows.append(result)
                        time.sleep(0.5) 
                
                progress_bar.progress((i + 1) / total_rows)

            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.success(f"✅ {len(new_rows)}件の分析が完了しました！（年収精度向上版）")
                st.dataframe(new_rows)
            else:
                st.info("新規に追加されたデータはありませんでした。")

        st.divider()
        
        st.subheader("📚 現在蓄積されているデータベース")
        col_reset, col_dummy = st.columns([1, 3])
        with col_reset:
            is_reset = st.checkbox("⚠️ データを全消去する")
            if is_reset:
                if st.button("実行してリセット"):
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        st.rerun()
        
        st.dataframe(df)

    with tab2:
        st.header("📊 比較表の生成")
        category_filter = st.selectbox("表示するカテゴリ", ["全て"] + CATEGORY_OPTIONS)
        
        if category_filter == "全て":
            target_df = df
        else:
            target_df = df[df["カテゴリ(入力)"] == category_filter]

        if not target_df.empty:
            st.write(f"### 比較表：{category_filter}")
            comparison_table = target_df.set_index("会社名").transpose()
            st.dataframe(comparison_table, height=800)

            csv_data = comparison_table.to_csv().encode('utf-8')
            st.download_button(
                label="📥 比較表をCSVでダウンロード",
                data=csv_data,
                file_name=f'comparison_{category_filter}.csv',
                mime='text/csv'
            )
        else:
            st.warning("データがありません。フロー1で追加してください。")

if __name__ == "__main__":
    main()
