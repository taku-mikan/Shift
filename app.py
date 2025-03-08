import os

from flask import Flask, render_template, request
import pandas as pd


app = Flask(__name__)


Path_Data = "./Data/shift_data.csv"

# ファイルを作成する関数
def make_file(path):
    df = pd.DataFrame(columns=['Year', 'Month', 'Day', 'Start Time', 'End Time'])
    df.to_csv(path, index=False)


# 総募集時間を計算する関数
def generate_total_time(df):
    if df.empty:
        return "No Data"
    
    total_time = 0
    for _, row in df.iterrows():
        start_time = row['Start Time']
        end_time = row['End Time']

        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))

        total_minutes = (end_hour - start_hour) * 60 + (end_minute - start_minute)
        total_time += total_minutes

    hours = total_time // 60
    minutes = total_time % 60
    return f"{hours} 時間 {minutes} 分"

@app.route('/', methods=['GET', 'POST'])
def index():
    df = pd.read_csv(Path_Data)

    # デフォルトの開始日と終了日を設定
    start_date = end_date = None

    # 初回アクセス時に最も古い日付と最新の日付を取得
    if request.method == "GET":
        # 'Year'と'Month'列を使って年月を作成
        df['Year-Month'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
        # 最も古い日付と最新の日付を取得
        start_date = df['Year-Month'].min()  # 最も古い年月
        end_date = df['Year-Month'].max()    # 最も新しい年月

    # フォームから開始日および終了日を取得（POST時）
    if request.method == "POST":
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # 範囲をフィルタリング
        df['Year-Month'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
        filterd_df = df[(df["Year-Month"] >= start_date) & (df['Year-Month'] <= end_date)]
    else:
        # 初回アクセス時にデフォルトの範囲でフィルタリング（最も古いと新しいデータを使用）
        filterd_df = df[(df["Year-Month"] >= start_date) & (df['Year-Month'] <= end_date)]

    # 総募集時間を計算
    total_time = generate_total_time(filterd_df)

    return render_template('index.html', total_time=total_time, start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    # 初回実行時、ファイルを作成
    if not os.path.exists(Path_Data):
        make_file(Path_Data)
    # 起動
    app.run(debug=True)

