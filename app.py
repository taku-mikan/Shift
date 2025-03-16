import os
import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image
import pandas as pd
from static.utils.plots import generate_time_based_plots, generate_weekday_plots, generate_monthly_plots, generate_total_time_weekday_plots, generate_daily_plots

app = Flask(__name__)

Path_Data = "./Data/shift_data.csv"
PLOT_FOLDER = "static/plots/"

# ファイルを作成する関数
def make_file(path):
    df = pd.DataFrame(columns=['Year', 'Month', 'Date', 'Start Time', 'End Time'])
    df.to_csv(path, index=False)

# プロットフォルダを作成する関数
def make_plot_folder(path):
    os.makedirs(path, exist_ok=True)

# 画像のサイズを取得する関数
def get_image_size(image_path):
    if not os.path.exists(image_path):
        return None  # 画像が存在しない場合はNoneを返す
    with Image.open(image_path) as img:
        return img.size  # (width, height)

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
    # データを読み込む
    df = pd.read_csv(Path_Data)

    # プロットフォルダを作成（存在しない場合）
    make_plot_folder(PLOT_FOLDER)

    # フォームから開始日と終了日を取得
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # 範囲をフィルタリング
        df['Year-Month'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
        filtered_df = df[(df['Year-Month'] >= start_date) & (df['Year-Month'] <= end_date)]
    else:
        filtered_df = df  # 初回起動時は全データを使用

    # グラフ画像を生成
    time_based_plot_path = generate_time_based_plots(filtered_df)
    weekday_plot_path = generate_weekday_plots(filtered_df)
    monthly_plot_path = generate_monthly_plots(filtered_df)

    # 総募集時間の計算
    total_time = generate_total_time(filtered_df)

    return render_template(
        'index.html',
        time_based_plot_url=time_based_plot_path,
        weekday_plot_url=weekday_plot_path,
        monthly_plot_url=monthly_plot_path,
        total_time=total_time,
        start_date=request.form.get('start_date', ''),
        end_date=request.form.get('end_date', '')
    )


@app.route('/month_results', methods=['GET', 'POST'])
def month_results():
    df = pd.read_csv(Path_Data)

    # featch current month as a default value
    current_month = datetime.datetime.now().month
    # featch start date and end date if specified.
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')

    selected_month = request.form.get('month', current_month)

    # 日付の範囲指定
    if start_date and end_date:
        df['Year-Month'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
        df = df[(df['Year-Month'] >= start_date) & (df['Year-Month'] <= end_date)]

    # 月のフィルタリング (もし指定があれば)
    if selected_month:
        df = df[df['Month'] == int(selected_month)]

    # generate graph
    time_based_plot_path = generate_time_based_plots(df)
    weekday_plot_path = generate_weekday_plots(df)
    weekday_total_time_plot_path = generate_total_time_weekday_plots(df)
    daily_plot_path = generate_daily_plots(df)

    return render_template(
        'month_results.html',
        time_based_plot_url=time_based_plot_path,
        weekday_plot_url=weekday_plot_path,
        weekday_total_time_plot_url=weekday_total_time_plot_path,
        daily_plot_url=daily_plot_path,
        start_date=start_date,
        end_date=end_date,
        selected_month=int(selected_month) if selected_month else ""
    )


@app.route('/download_plot/<plot_type>')
def download_plot(plot_type):
    plot_path_map = {
        'shift_requests_time_based': os.path.join(PLOT_FOLDER, "shift_requests_time_based.png"),
        'shift_requests_weekday': os.path.join(PLOT_FOLDER, "shift_requests_weekday.png"),
        'shift_requests_monthly': os.path.join(PLOT_FOLDER, "shift_requests_monthly.png"),
    }
    
    plot_path = plot_path_map.get(plot_type)
    if plot_path and os.path.exists(plot_path):
        return send_file(plot_path, as_attachment=True)
    return "Plot not found", 404

if __name__ == "__main__":
    # 初回実行時のセットアップ
    if not os.path.exists(Path_Data):
        make_file(Path_Data)
    make_plot_folder(PLOT_FOLDER)  # プロットフォルダを必ず作成

    # アプリ起動時に全データのグラフを作成
    df = pd.read_csv(Path_Data)
    generate_time_based_plots(df)
    generate_weekday_plots(df)
    generate_monthly_plots(df)

    # 起動
    app.run(debug=True)
