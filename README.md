# 📷 P4M IMAGE CONVERTER
Convert P4 Multispectral images to Radiance/Reflectance with a simple web app.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-brightgreen)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ 概要

**P4M IMAGE CONVERTER** は、マルチスペクトルTIF画像をもとに「放射輝度 / 反射率」画像を生成するための Streamlit GUI アプリです。  
黒レベル補正・ビネット補正・照度補正・歪み補正などを自動適用し、簡単な操作で高精度な画像処理が行えます。

## ⚙️ 動作環境

| 項目 | 推奨内容 |
|------|----------|
| Python | 3.8 以上 |
| OS | Windows / macOS / Linux |
| 仮想環境 | Anaconda または `venv` 推奨 |

---

## 🛠️ セットアップ手順

```bash
# 仮想環境作成（任意）
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# exiftool をインストール（Exif情報読み取りに必要）
# macOS/Linux
brew install exiftool
# Windows: https://exiftool.org から exe をダウンロードしパスを通す
```

---

## 🚀 アプリの起動

```bash
streamlit run app.py
```

アプリがブラウザで自動表示されます。  
手動でアクセスする場合は http://localhost:8501 にアクセスしてください。

---

## 📝 使用方法

1. TIF画像をアップロード（複数可）
2. モード選択：「反射率」または「放射輝度」
3. 「🔄 一括変換する」をクリック
4. 変換後の画像が画面に表示、`result/` フォルダに保存されます

---

## 📁 出力ファイル

- 出力先：`result/` フォルダ
- ファイル名：元画像名に `_reflectance` または `_radiance` が追加されます
- 形式：16bit TIF形式

---

## ⚠️ 注意点

- `1.TIF`（青バンド）は自動スキップされます
- 必要なExif情報が含まれていない画像はスキップされます
- `pyexifinfo` のため `exiftool` の導入が必要です

---

## 🧰 開発ファイル構成

```
├── app.py
├── band_reflectance_app.py
├── undistort_calib.py
├── vignette_calib.py
├── requirements.txt
└── README.md
```

---

## 📄 ライセンス

このプロジェクトは MIT ライセンスのもとで公開されています。
