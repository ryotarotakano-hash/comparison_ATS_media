import streamlit as st
import pandas as pd
import os
import json
import time
import random
from datetime import datetime
from groq import Groq, RateLimitError, APIError

# ==========================================
# 🔑 設定・APIキー管理
# ==========================================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except FileNotFoundError:
    st.error("🚫 APIキーが見つかりません！Streamlit CloudのSecretsを設定してください。")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = 'recruitment_db.csv'

# ==========================================
# 📋 カテゴリ定義
# ==========================================
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
    ],
    "その他": [
        "SNS・その他"
    ]
}

# ==========================================
# 📚 デフォルト・マスターデータ（完全版）
# ==========================================
DEFAULT_TARGETS = [
    # --- 求人媒体：新卒 ---
    {"company": "マイナビ2027", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "リクナビ2027", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "キャリタス就活", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "ONE CAREER", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "OfferBox", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "ジョブコミット", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "Future Finder", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "LabBase", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "TECH OFFER", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "Paiza新卒", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "Re就活", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "Goodfind", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "外資就活ドットコム", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "チアキャリア", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},
    {"company": "JobSpring", "major": "求人媒体", "sub": "求人媒体（新卒向け）"},

    # --- 求人媒体：中途 ---
    {"company": "Indeed", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "リクナビNEXT", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "マイナビ転職", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "doda", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "エン転職", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "type", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "女の転職type", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "はたらいく", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "FromA NAVI", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "イーキャリア", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "CareerCross", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "Daijob", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "OpenWork求人", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "ミドルの転職", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "エン ミドルハイクラス", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "AMBI", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "Liiga", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "Wantedly", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "JobQ転職", "major": "求人媒体", "sub": "求人媒体（中途向け）"},
    {"company": "Googleしごと検索", "major": "求人媒体", "sub": "求人媒体（中途向け）"},

    # --- 求人媒体：アルバイト ---
    {"company": "タウンワーク", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "バイトル", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "マイナビバイト", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "Indeed", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "ショットワークス", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "フロムエー", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "LINEバイト", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "ギガバイト", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},
    {"company": "an", "major": "求人媒体", "sub": "求人媒体（アルバイト・パート向け）"},

    # --- 求人媒体：インターン ---
    {"company": "Wantedly", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "マイナビインターンシップ", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "リクナビインターン", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "Infra", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "ゼロワンインターン", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "キャリアバイト", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "エンジニアインターン", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "Paizaインターン", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "LabBaseインターン", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "Chegg Internships", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},
    {"company": "Intern Street", "major": "求人媒体", "sub": "求人媒体（インターン・学生バイト向け）"},

    # --- 求人媒体：業務委託 ---
    {"company": "CrowdWorks", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Lancers", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Workship", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Midworks", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "ITプロパートナーズ", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "レバテックフリーランス", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "ココナラ", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "SOKUDAN", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "フリーランススタート", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Anycrew", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Offers", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "HiPro Direct", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "Saleshub", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "複業クラウド", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},
    {"company": "ProSharing", "major": "求人媒体", "sub": "求人媒体（業務委託・フリーランス向け）"},

    # --- スカウト：新卒 ---
    {"company": "OfferBox", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "LabBase", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "TECH OFFER", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "Paiza新卒スカウト", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "Future Finder", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "キャリアチケットスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "キミスカ", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "dodaキャンパス", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "iroots", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},
    {"company": "Re就活スカウト", "major": "スカウト媒体", "sub": "スカウト媒体（新卒向け）"},

    # --- スカウト：中途 ---
    {"company": "ビズリーチ", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "リクルートダイレクトスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "dodaダイレクト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "AMBI", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "ミドルの転職", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "OpenWorkスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Green", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Wantedlyスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "CareerCrossスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Daijobスカウト", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Eight Career Design", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Liiga", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "YOUTRUST", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Findy", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Forkwell Jobs", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "LAPRAS", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},
    {"company": "Paiza転職", "major": "スカウト媒体", "sub": "スカウト媒体（中途向け）"},

    # --- スカウト：業務委託 ---
    {"company": "SOKUDAN", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "Offers", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "Anycrew", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "HiPro Direct", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "Workship", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "ITプロパートナーズ", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "Saleshub", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "複業クラウド", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},
    {"company": "ProSharing", "major": "スカウト媒体", "sub": "スカウト媒体（業務委託向け）"},

    # --- ATS：国産 ---
    {"company": "HRMOS採用", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "HERP Hire", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "ジョブカン採用管理", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "SONAR ATS", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "RPM", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "i-web", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "Talentio", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "Engage", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "Airワーク", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "採用一括かんりくん", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "HITO-Link", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "e2R PRO", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "WORKL", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "TORoo", "major": "ATS", "sub": "ATS（国産）"},
    {"company": "RecoRu", "major": "ATS", "sub": "ATS（国産）"},

    # --- ATS：外資 ---
    {"company": "Greenhouse", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "Lever", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "Workday", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "SmartRecruiters", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "SAP SuccessFactors", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "iCIMS", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "Taleo", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "BambooHR", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "JazzHR", "major": "ATS", "sub": "ATS（外資系・グローバル）"},
    {"company": "Bullhorn", "major": "ATS", "sub": "ATS（外資系・グローバル）"},

    # --- その他 ---
    {"company": "LinkedIn", "major": "その他", "sub": "SNS・その他"},
    {"company": "X（旧Twitter）", "major": "その他", "sub": "SNS・その他"},
    {"company": "Facebook", "major": "その他", "sub": "SNS・その他"},
    {"company": "Instagram", "major": "その他", "sub": "SNS・その他"},
    {"company": "note", "major": "その他", "sub": "SNS・その他"},
    {"company": "自社採用サイト", "major": "その他", "sub": "SNS・その他"},
    {"company": "Googleフォーム", "major": "その他", "sub": "SNS・その他"},
    {"company": "LINE公式アカウント", "major": "その他", "sub": "SNS・その他"},
]

# ==========================================
# 📋 項目定義
# ==========================================
COLUMNS = [
    "会社名", "大項目", "カテゴリ(詳細)",
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
# 🧠 AIエンジニアリング部分 (リトライ強化版)
# ==========================================
def research_with_groq(company_name, major_category, sub_category):
    prompt = f"""
    あなたは日本の採用市場に精通したトップコンサルタントです。
    以下のサービスについて情報を検索し、JSON形式で回答してください。
    
    対象サービス名: {company_name}
    サービス分類: {major_category} > {sub_category}

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

    # リトライ設定
    max_retries = 3
    base_delay = 5 # 秒

    for attempt in range(max_retries):
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
            
            # データ整形
            safe_data = {col: data.get(col, "-") for col in COLUMNS}
            safe_data["会社名"] = company_name
            safe_data["大項目"] = major_category
            safe_data["カテゴリ(詳細)"] = sub_category
            
            return safe_data

        except RateLimitError as e:
            # レート制限にかかった場合
            wait_time = 60 + random.randint(5, 15) # 1分ちょっと待つ
            if attempt < max_retries - 1:
                st.toast(f"⏳ 制限検出: {company_name} の処理を {wait_time}秒 待機して再試行します...", icon="⚠️")
                time.sleep(wait_time)
                continue
            else:
                return create_error_row(company_name, major_category, sub_category, f"レート制限エラー: {str(e)}")

        except Exception as e:
            # その他のエラー
            if attempt < max_retries - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
            else:
                return create_error_row(company_name, major_category, sub_category, f"エラー: {str(e)}")

    return create_error_row(company_name, major_category, sub_category, "不明なエラー")

def create_error_row(company, major, sub, error_msg):
    """エラー時でも行が消えないように、全カラム埋まった辞書を返す"""
    error_row = {col: "⚠️取得失敗" for col in COLUMNS}
    error_row["会社名"] = company
    error_row["大項目"] = major
    error_row["カテゴリ(詳細)"] = sub
    error_row["導入メリット"] = error_msg # エラー内容を見える場所に書く
    return error_row

# ==========================================
# 🖥️ UI / アプリケーション本体
# ==========================================
def main():
    st.set_page_config(page_title="AI Recruitment Researcher", layout="wide")
    st.title("🚀 AI採用媒体・ATS比較ダッシュボード")
    st.markdown("powered by Groq (Llama 3.3) - **完全リスト・自動リトライ版**")

    # 1. データロードとクレンジング
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # 重複整理: 会社名＋カテゴリが同じなら最新を残す
            df.drop_duplicates(subset=['会社名', '大項目', 'カテゴリ(詳細)'], keep='last', inplace=True)
            # カラム補完
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = "-"
        except Exception:
            df = pd.DataFrame(columns=COLUMNS)
    else:
        df = pd.DataFrame(columns=COLUMNS)

    if "research_queue" not in st.session_state:
        st.session_state.research_queue = []

    tab1, tab2 = st.tabs(["📝 フロー1：ラベリング・リサーチ", "📊 フロー2：比較表出力"])

    with tab1:
        st.header("1. リサーチ対象の追加")

        with st.expander("📚 有名サービスの一括登録はこちら（クリックで開く）", expanded=True):
            if st.button("🚀 デフォルトの全サービスをリサーチ待ちリストに追加", type="primary"):
                count = 0
                target_list = DEFAULT_TARGETS 
                
                for item in target_list:
                    # リスト内の重複チェック
                    is_in_queue = any(
                        (q['会社名'] == item['company'] and q['中項目'] == item['sub']) 
                        for q in st.session_state.research_queue
                    )
                    # DB内の重複チェック
                    is_in_db = False
                    if not df.empty:
                        is_in_db = ((df['会社名'] == item['company']) & (df['カテゴリ(詳細)'] == item['sub'])).any()

                    if not is_in_queue and not is_in_db:
                        st.session_state.research_queue.append({
                            "会社名": item["company"],
                            "大項目": item["major"],
                            "中項目": item["sub"],
                            "ステータス": "待機中"
                        })
                        count += 1
                
                if count > 0:
                    st.success(f"{count}件のサービスを追加しました。")
                else:
                    st.info("全てのサービスは既に追加済みです。")

        st.divider()

        # 手動入力エリア
        with st.container(border=True):
            col_input1, col_input2, col_input3, col_btn = st.columns([2, 2, 2, 1])
            with col_input1:
                input_company = st.text_input("会社名", placeholder="例: Wantedly")
            with col_input2:
                input_major = st.selectbox("① 大項目", list(CATEGORY_HIERARCHY.keys()))
            with col_input3:
                sub_options = CATEGORY_HIERARCHY[input_major]
                input_sub = st.selectbox("② 中項目", sub_options)
            with col_btn:
                st.write("") 
                st.write("") 
                if st.button("リストに追加", type="secondary"):
                    if input_company:
                        st.session_state.research_queue.append({
                            "会社名": input_company,
                            "大項目": input_major,
                            "中項目": input_sub,
                            "ステータス": "待機中"
                        })
                    else:
                        st.warning("会社名を入力してください")

        # リサーチ実行エリア
        if st.session_state.research_queue:
            st.subheader(f"リサーチ待ちリスト（全 {len(st.session_state.research_queue)} 件）")
            
            queue_df = pd.DataFrame(st.session_state.research_queue)
            st.dataframe(queue_df, height=200)
            
            if st.button("🚀 リストのAIリサーチを一括実行", type="primary"):
                progress_bar = st.progress(0)
                status_box = st.container(border=True)
                
                new_rows = []
                total_items = len(queue_df)
                
                for i, row in queue_df.iterrows():
                    company = row["会社名"]
                    major = row["大項目"]
                    sub = row["中項目"]

                    status_box.info(f"🤖 ({i+1}/{total_items}) 『{company}』を調査中... ({sub})")
                    
                    # リサーチ実行（リトライロジック込み）
                    result = research_with_groq(company, major, sub)
                    new_rows.append(result)
                    
                    # 進捗バー更新
                    progress_bar.progress((i + 1) / total_items)
                    
                    # API制限回避のための待機時間（重要）
                    time.sleep(3) 

                # 全件終了後の保存処理
                if new_rows:
                    new_df = pd.DataFrame(new_rows)
                    # 既存データと結合
                    df = pd.concat([df, new_df], ignore_index=True)
                    # 重複排除して保存
                    df.drop_duplicates(subset=['会社名', '大項目', 'カテゴリ(詳細)'], keep='last', inplace=True)
                    df.to_csv(DB_FILE, index=False)
                    
                    st.success(f"✅ {len(new_rows)}件のリサーチが完了しました！")
                    st.session_state.research_queue = [] # キューを空にする
                    time.sleep(2)
                    st.rerun() # 画面更新
                else:
                    st.warning("データが取得できませんでした。")

        st.divider()
        
        # データベース管理
        st.subheader("📚 蓄積されたデータベース")
        col_reset, col_dummy = st.columns([1, 3])
        with col_reset:
            is_reset = st.checkbox("⚠️ データを全消去してリセット")
            if is_reset:
                if st.button("実行"):
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        st.rerun()
        
        st.dataframe(df)

    with tab2:
        st.header("📊 比較表の生成")
        
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            available_majors = ["全て"] + list(df["大項目"].unique()) if "大項目" in df.columns else ["全て"]
            filter_major = st.selectbox("大項目で絞り込み", available_majors)
            
        with filter_col2:
            if filter_major == "全て":
                available_subs = ["全て"] + list(df["カテゴリ(詳細)"].unique()) if "カテゴリ(詳細)" in df.columns else ["全て"]
            else:
                subset = df[df["大項目"] == filter_major]
                available_subs = ["全て"] + list(subset["カテゴリ(詳細)"].unique())
            
            filter_sub = st.selectbox("中項目で絞り込み", available_subs)

        target_df = df.copy()
        if filter_major != "全て":
            target_df = target_df[target_df["大項目"] == filter_major]
        if filter_sub != "全て":
            target_df = target_df[target_df["カテゴリ(詳細)"] == filter_sub]

        if not target_df.empty:
            st.write(f"### 比較表：{len(target_df)}社")
            
            # 表示用データ作成
            df_display = target_df.copy()
            df_display["unique_header"] = df_display.apply(
                lambda row: f"{row['会社名']} ({row['カテゴリ(詳細)']})", axis=1
            )
            
            # 強制ユニーク化（エラー回避）
            if df_display["unique_header"].duplicated().any():
                df_display["unique_header"] = df_display["unique_header"] + " #" + df_display.index.astype(str)
            
            # 見出し整理
            company_counts = df_display["会社名"].value_counts()
            def final_header_name(row):
                if company_counts[row["会社名"]] == 1:
                    return row["会社名"]
                else:
                    return row["unique_header"]

            df_display["display_name"] = df_display.apply(final_header_name, axis=1)
            
            # 転置して表示
            comparison_table = df_display.set_index("display_name").transpose()
            st.dataframe(comparison_table, height=800)

            csv_data = comparison_table.to_csv().encode('utf-8')
            st.download_button(
                label="📥 比較表をCSVでダウンロード",
                data=csv_data,
                file_name=f'comparison_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        else:
            st.info("データがありません。フロー1でリサーチを実行してください。")

if __name__ == "__main__":
    main()
