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
# 📋 カテゴリ定義（階層構造）
# ==========================================
# ユーザー要望の階層構造を定義
CATEGORY_HIERARCHY = {
    "求人媒体": [
        "求人媒体（新卒向け）",
        "求人媒体（中途向け）",
        "求人媒体（アルバイト・パート向け）",
        "求人媒体（インターン・学生バイト向け）",
        "求人媒体（業務委託・フリーランス向け）"
    ],
    "スカウト媒体": [
        "スカウト媒体（新卒向け）",
        "スカウト媒体（中途向け）",
        "スカウト媒体（業務委託向け）"
    ],
    "ATS": [
        "ATS（国産）",
        "ATS（外資系・グローバル）"
    ]
}

# ==========================================
# 📋 項目定義
# ==========================================
COLUMNS = [
    "会社名", "大項目", "カテゴリ(詳細)", # ★項目を追加しました
    "導入メリット", "導入デメリット", 
    "媒体カテゴリ", "主な利用目的", "向いている採用フェーズ", 
    "ターゲット職種", "ターゲット年収帯", "経験レベル", "雇用形態対応",
    "課金形態", "初期費用", "最低契約期間", "想定採用単価", "予算コントロール",
    "登録ユーザー数", "アクティブユーザー傾向", "スカウト到達率",
    "応募導線の簡易さ", "スカウト送信数制限", "開封率目安",
    "管理画面の使いやすさ", "レポート機能", "CSV出力",
    "媒体連携数", "API連携可否", "(Indeed)連携可否", "審査の厳しさ",
    "サポート体制", "導入企業規模"
]

# ==========================================
# 🧠 AIエンジニアリング部分
# ==========================================
def research_with_groq(company_name, major_category, sub_category):
    # ★プロンプトに大項目と中項目の両方を渡して精度を高めます
    prompt = f"""
    あなたは日本の採用市場に精通したトップコンサルタントです。
    以下のサービスについて情報を検索し、JSON形式で回答してください。
    
    対象サービス名: {company_name}
    サービス分類: {major_category} > {sub_category}
    (この分類に基づき、適切なコンテキストで情報を抽出してください)

    出力JSONキー:
    {", ".join(COLUMNS)}

    【重要：データ抽出ルール】
    1. **導入メリット / 導入デメリット**:
       - 採用担当者視点で、それぞれ3点ほど簡潔に挙げること。
       - **禁止事項**: 文頭や文末に「」『』() [] などの括弧記号は一切つけないこと。
       - **形式**: 各項目の頭に「・」をつけ、改行で区切ること。

    2. **ターゲット年収帯**:
       - ⚠️ 必ず「年収」表記にすること（月収×12〜14で換算）。単位は「万円」。
    
    3. **全体ルール**:
       - 数値は目安でOK。不明な場合は「要問い合わせ」。
       - 必ず有効なJSON形式のみを出力すること。
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "JSON形式で出力する厳格なアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        response_content = completion.choices[0].message.content
        data = json.loads(response_content)
        
        # データの整形
        safe_data = {col: data.get(col, "-") for col in COLUMNS}
        safe_data["会社名"] = company_name
        safe_data["大項目"] = major_category
        safe_data["カテゴリ(詳細)"] = sub_category
        
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

    # データベース読み込み
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # カラム互換性チェック
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "-"
    else:
        df = pd.DataFrame(columns=COLUMNS)

    # セッション状態で「リサーチ待ちリスト」を管理
    if "research_queue" not in st.session_state:
        st.session_state.research_queue = []

    tab1, tab2 = st.tabs(["📝 フロー1：ラベリング・リサーチ", "📊 フロー2：比較表出力"])

    with tab1:
        st.header("1. リサーチ対象の追加")
        st.markdown("会社名を入力し、カテゴリを選択してリストに追加してください。")

        # --- 入力フォーム ---
        with st.container(border=True):
            col_input1, col_input2, col_input3, col_btn = st.columns([2, 2, 2, 1])
            
            with col_input1:
                input_company = st.text_input("会社名", placeholder="例: Wantedly")
            
            with col_input2:
                # 大項目の選択
                input_major = st.selectbox("① 大項目", list(CATEGORY_HIERARCHY.keys()))
            
            with col_input3:
                # 選ばれた大項目に基づいて、中項目の選択肢を変える
                sub_options = CATEGORY_HIERARCHY[input_major]
                input_sub = st.selectbox("② 中項目", sub_options)
            
            with col_btn:
                st.write("") # ボタン位置調整用の空白
                st.write("") 
                if st.button("リストに追加", type="secondary"):
                    if input_company:
                        # リストに追加
                        st.session_state.research_queue.append({
                            "会社名": input_company,
                            "大項目": input_major,
                            "中項目": input_sub,
                            "ステータス": "待機中"
                        })
                    else:
                        st.warning("会社名を入力してください")

        # --- リサーチ待ちリストの表示 ---
        if st.session_state.research_queue:
            st.subheader("リサーチ待ちリスト")
            
            # 編集可能なデータフレームとして表示
            queue_df = pd.DataFrame(st.session_state.research_queue)
            edited_queue = st.data_editor(
                queue_df,
                num_rows="dynamic",
                key="queue_editor"
            )
            
            # リサーチ実行ボタン
            if st.button("🚀 リストのAIリサーチを一括実行", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                new_rows = []
                total_items = len(edited_queue)
                
                for i, row in edited_queue.iterrows():
                    company = row["会社名"]
                    major = row["大項目"]
                    sub = row["中項目"]

                    # 既にDBにあるかチェック
                    if company in df["会社名"].values:
                        status_text.info(f"⏭️ {company} は既にデータベースに存在します。スキップします。")
                    else:
                        status_text.info(f"🤖 AIが『{company}』を調査中... ({major} > {sub})")
                        # AIリサーチ実行
                        result = research_with_groq(company, major, sub)
                        new_rows.append(result)
                        time.sleep(0.5)
                    
                    progress_bar.progress((i + 1) / total_items)

                # 結果を保存
                if new_rows:
                    new_df = pd.DataFrame(new_rows)
                    df = pd.concat([df, new_df], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"✅ {len(new_rows)}件のリサーチが完了しました！")
                    
                    # リストを空にする
                    st.session_state.research_queue = []
                    st.rerun() # 画面更新
                else:
                    st.info("新規データはありませんでした。")
                    st.session_state.research_queue = []
                    st.rerun()

        st.divider()
        
        # --- 既存データ ---
        st.subheader("📚 蓄積されたデータベース")
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
        
        # フィルタリング機能の強化（大項目・中項目で絞り込み）
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            # ユニークな大項目を取得
            available_majors = ["全て"] + list(df["大項目"].unique()) if "大項目" in df.columns else ["全て"]
            filter_major = st.selectbox("大項目で絞り込み", available_majors)
            
        with filter_col2:
            # 選ばれた大項目に含まれる中項目だけを表示
            if filter_major == "全て":
                available_subs = ["全て"] + list(df["カテゴリ(詳細)"].unique()) if "カテゴリ(詳細)" in df.columns else ["全て"]
            else:
                subset = df[df["大項目"] == filter_major]
                available_subs = ["全て"] + list(subset["カテゴリ(詳細)"].unique())
            
            filter_sub = st.selectbox("中項目で絞り込み", available_subs)

        # データの抽出
        target_df = df.copy()
        if filter_major != "全て":
            target_df = target_df[target_df["大項目"] == filter_major]
        if filter_sub != "全て":
            target_df = target_df[target_df["カテゴリ(詳細)"] == filter_sub]

        if not target_df.empty:
            st.write(f"### 比較表：{len(target_df)}社")
            comparison_table = target_df.set_index("会社名").transpose()
            st.dataframe(comparison_table, height=800)

            csv_data = comparison_table.to_csv().encode('utf-8')
            st.download_button(
                label="📥 比較表をCSVでダウンロード",
                data=csv_data,
                file_name=f'comparison_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        else:
            st.warning("該当するデータがありません。")

if __name__ == "__main__":
    main()
