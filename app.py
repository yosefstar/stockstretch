from jinja2 import Template
from flask import Flask, render_template, request, make_response, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import chromedriver_binary
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")
import sys
sys.path.append('/path/to/project')
import importlib
import os
import re
import secrets
import requests
import random
import asyncio


app = Flask(__name__, static_folder='static')

# デフォルトのCSVファイルの保存場所を定義する
app.config['UPLOAD_FOLDER'] = 'uploads/'

# 許可されるアップロード拡張子を定義する
app.config['ALLOWED_EXTENSIONS'] = set(['csv'])

app.config['JSON_AS_ASCII'] = False
app.secret_key = secrets.token_hex(16)

# WebDriverを初期化する
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

app = Flask(__name__)

options = webdriver.ChromeOptions()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")  # 追加: 環境変数からChromeのバイナリの場所を取得
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")  # 追加: 共有メモリを無効にする
options.add_argument("--no-sandbox")  # 追加: サンドボックスモードを無効にする
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)  # 追加: 環境変数からChromeDriverのパスを取得

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        csv_file = request.files['file1']
        if csv_file:
            stream = io.StringIO(csv_file.stream.read().decode("utf-8-sig"), newline="")
            csv_reader = csv.reader(stream)
            urls = [row[0] for row in csv_reader]
            session['urls'] = urls
            link_count = count_links(urls)
            return render_template('result.html', link_count=link_count)
    return render_template('index.html')

def count_links(urls):
    link_count = 0
    for url in urls:
        if 'mercari.com' in url:
            link_count += 1
    return link_count

@app.route('/start_process', methods=['POST'])
def start_process():
    urls = session.get('urls')
    if urls:
        # リンク毎にページを読み込み、購入手続きへの有無を判定する
        results = []
        for url in urls:
            driver.get(url)
            time.sleep(1)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            if soup.select_one('body:contains("購入手続きへ")'):
                results.append("○")
            else:
                results.append("×")

        # 結果をCSVファイルに保存する
        pairs = list(zip(urls, results))
        session['pairs'] = pairs

        # ビデオのファイル名をsessionに保存する
        session['video_file'] = random.choice(['video1.mp4', 'video2.mp4', 'video3.mp4'])
        return render_template('start_process.html', pairs=pairs)

    else:
        return 'CSVファイルがアップロードされていません。'


@app.route('/csv_download', methods=['POST'])
def csv_download():
    # リンクのチェック結果を取得
    pairs = session.get('pairs')
    if not pairs:
        return 'リンクのチェック結果がありません。'

    # 結果をCSVに書き込む
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['URL', '判定結果'])
    for url, result in pairs:
        writer.writerow([url, result])

    # レスポンスを作成して返す
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=result.csv'
    response.headers['Content-type'] = 'text/csv'
    return response


@app.route('/upload_hyper', methods=['GET', 'POST'])
def upload_hyper():
    if request.method == 'POST':
        csv_file = request.files['file2']
        if csv_file:
            # バイト列から文字列へ変換する
            stream = io.StringIO(csv_file.stream.read().decode("utf-8-sig"), newline="")
            csv_reader = csv.reader(stream)
            urls = [row[0] for row in csv_reader]
            # リンク毎にページを読み込み、情報を取得する
            rows = [["リンク", "販売中", "価格", "商品名", "送料込み"]]
            for url in urls:
                driver.get(url)
                time.sleep(4)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                # 販売中の判定
                if soup.select_one('body:contains("購入手続きへ")'):
                    selling = "販売中"
                else:
                    selling = "×"
                # 価格の取得
                try:
                    price = soup.select_one('div[data-testid="price"] span:nth-of-type(2)').text.strip()
                except AttributeError:
                    price = "×"
                # 商品名の取得
                try:
                    name = soup.select_one('div[class^="labelContainer"] h1').text.strip()
                except AttributeError:
                    name = "×"
                # 送料込みの取得
                try:
                    shipping = soup.select_one('mer-display-row:nth-of-type(3) span[slot="body"]').text.strip()
                except AttributeError:
                    shipping = "×"
                # 1行の情報を作成
                row = [url, selling, price, name, shipping]
                rows.append(row)
            
            # 結果をHTMLに渡す
            pairs = rows[1:]
            session['pairs'] = pairs
            return render_template('upload_hyper_result.html', rows=rows)
        else:
            return 'CSVファイルがアップロードされていません。'
    return render_template('upload_form_hyper.html')

@app.route('/csv_hyper_download', methods=['GET', 'POST'])
def csv_hyper_download():
    if request.method == 'POST':
        # ペアをCSVに書き込む
        pairs = session.get('pairs', [])
        if not pairs:
            return 'ペアがありません。'
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['リンク', '販売中', '価格', '商品名', '送料込み'])
        writer.writerows(pairs)
        output.seek(0)

        # CSVをダウンロードする
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=pairs.csv'
        response.mimetype = 'text/csv'
        return response
    else:
        return 'Method Not Allowed'

def random_choice(lst):
    return random.choice(lst)

app.jinja_env.filters['random_choice'] = random_choice
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
random_video = random.choice(video_files)


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, port=8000, host='localhost')

