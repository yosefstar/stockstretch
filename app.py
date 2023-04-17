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


app = Flask(__name__, static_folder='static')

# デフォルトのCSVファイルの保存場所を定義する
app.config['UPLOAD_FOLDER'] = 'uploads/'

# 許可されるアップロード拡張子を定義する
app.config['ALLOWED_EXTENSIONS'] = set(['csv'])

app.config['JSON_AS_ASCII'] = False
app.secret_key = secrets.token_hex(16)

# WebDriverを初期化する
options = Options()
options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-extensions')
options.add_argument('--disable-infobars')
driver = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=options)

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
try:
driver.get(url)
time.sleep(1)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
if soup.select_one('body:contains("購入手続きへ")'):
results.append("○")
else:
results.append("×")
except Exception as e:
# ページの読み込みが失敗した場合、エラーをログに出力する
app.logger.error('Error occurred while checking link: ' + url)
app.logger.error(str(e))
results.append("エラー")
    # 結果をCSVファイルに保存する
    pairs = list(zip(urls, results))
    session['pairs'] = pairs

    # ビデオのファイル名をsessionに保存する
    session['video_file'] = random.choice(['video1.mp4', 'video2.mp4', 'video3.mp4'])
    return render_template('start_process.html', pairs=pairs)

else:
    return 'CSVファイルがアップロードされていません。'