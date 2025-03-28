import streamlit as st
import os
import numpy as np
import cv2
from band_reflectance_app import run_processing_pipeline  # アプリ専用の処理関数

st.set_page_config(page_title="P4M 画像変換ツール", page_icon="📷", layout="centered")

st.markdown("""
<style>
/* Notion風の雰囲気とライトテーマに適合したスタイル */
body, html {
    background-color: #F9F9F9;
    font-family: 'Segoe UI', sans-serif;
    color: #2E2E2E;
}
[data-testid="stAppViewContainer"] {
    background-color: #F9F9F9;
}
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
}
.card {
    background-color: white;
    color: #2E2E2E;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
label, .stRadio > div, .stFileUploader, .stButton, .stAlert, .stTextInput, .stMarkdown {
    color: #2E2E2E !important;
}
div[data-baseweb="radio"] label span {
    color: #2E2E2E !important;
    font-weight: normal;
}
button[kind="primary"] {
    color: #2E2E2E !important;
}
/* アップロードコンポーネントの説明テキストを暗めに */
section[data-testid="stFileUploader"] label div span {
    color: #444444 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h1 style="margin-bottom:0.2em; color: #2E2E2E; font-size: 2.2em; font-weight: 600;">
📷 P4M IMAGE CONVERTER
</h1>
<p style="margin-top:0; font-size: 1.1em; color: #666666;">
Smart conversion to Radiance & Reflectance.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<p style="color:#2E2E2E; font-weight:bold;">画像ファイルをアップロード (TIF, 複数選択可)</p>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("画像ファイルをアップロード", type=["tif", "TIF"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<p style="color:#2E2E2E; font-weight:bold;">変換モードを選択</p>', unsafe_allow_html=True)
mode = st.radio("変換モードを選択", ("反射率", "放射輝度"), horizontal=True, label_visibility="collapsed")

if uploaded_files:
    if st.button("🔄 一括変換する"):
        with st.spinner("全画像を処理中... 少々お待ちください。"):
            results = []
            script_dir = os.path.dirname(os.path.abspath(__file__))
            out_dir = os.path.join(script_dir, "result")
            os.makedirs(out_dir, exist_ok=True)

            for uploaded_file in uploaded_files:
                in_path = os.path.join(out_dir, uploaded_file.name)
                with open(in_path, "wb") as f:
                    f.write(uploaded_file.read())

                try:
                    out_path = run_processing_pipeline(in_path, out_dir, mode=mode)

                    if out_path == "blue_band_skipped":
                        st.info(f"ℹ️ 青バンドのためスキップされました: {uploaded_file.name}")
                    elif out_path and os.path.exists(out_path):
                        img_16bit = cv2.imread(out_path, cv2.IMREAD_UNCHANGED)
                        img_preview = cv2.normalize(img_16bit, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                        results.append({
                            "name": uploaded_file.name,
                            "img_preview": img_preview,
                            "mode": mode
                        })
                    else:
                        st.warning(f"⚠️ 出力ファイルが生成されませんでした: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} の処理中にエラーが発生しました: {e}")

        if results:
            st.markdown("""
            <div class="card">
            <h3 style="color:#2E2E2E">✅ 全ての処理が完了しました！</h3>
            </div>
            """, unsafe_allow_html=True)
            cols = st.columns(4)
            for i, r in enumerate(results):
                with cols[i % 4]:
                    st.markdown(f"<p style='font-weight:bold; color:#2E2E2E'>{r['name']}</p>", unsafe_allow_html=True)
                    label = "Radiance" if r["mode"] == "放射輝度" else "Reflectance"
                    st.image(r["img_preview"], use_container_width=True, channels="GRAY", caption=f"Converted ({label})")
else:
    st.markdown('<p style="color:#2E2E2E">📂 左のパネルから画像をアップロードしてください。</p>', unsafe_allow_html=True)
