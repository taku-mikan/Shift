import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image
import pandas as pd
from static.utils.plots import generate_time_based_plots, generate_weekday_plots, generate_monthly_plots

app = Flask(__name__)

Path_Data = "./Data/shift_data.csv"
PLOT_FOLDER = "static/plots/"

# ファイルを作成する関数
def make_file(path):
    df = pd.DataFrame(columns=['Year', 'Month', 'Day', 'Start Time', 'End Time'])
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

    # 画像のパス
    time_based_image_path = os.path.join(PLOT_FOLDER, "shift_requests_time_based.png")
    weekday_image_path = os.path.join(PLOT_FOLDER, "shift_requests_weekday.png")
    monthly_image_path = os.path.join(PLOT_FOLDER, "shift_requests_monthly.png")

    # グラフ画像を毎回生成して保存
    time_based_plot_path = generate_time_based_plots(df)
    weekday_plot_path = generate_weekday_plots(df)
    monthly_plot_path = generate_monthly_plots(df)

    # 画像の横幅と縦幅を取得
    time_based_size = get_image_size(time_based_image_path)
    weekday_size = get_image_size(weekday_image_path)
    monthly_size = get_image_size(monthly_image_path)

    # 画像が存在しない場合はデフォルトの比率を設定
    time_based_ratio = (time_based_size[0] / time_based_size[1]) if time_based_size else 1
    weekday_ratio = (weekday_size[0] / weekday_size[1]) if weekday_size else 1
    monthly_ratio = (monthly_size[0] / monthly_size[1]) if monthly_size else 1

    # フォームから開始日と終了日を取得
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        # 範囲をフィルタリング
        df['Year-Month'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
        filtered_df = df[(df['Year-Month'] >= start_date) & (df['Year-Month'] <= end_date)]
    else:
        filtered_df = df

    # 総募集時間の計算
    total_time = generate_total_time(filtered_df)

    return render_template(
        'index.html',
        time_based_plot_url=time_based_plot_path,
        weekday_plot_url=weekday_plot_path,
        monthly_plot_url=monthly_plot_path,
        total_time=total_time,
        time_based_ratio=time_based_ratio,
        weekday_ratio=weekday_ratio,
        monthly_ratio=monthly_ratio
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


@app.route('/add_shift', methods=['POST'])
def add_shift():
    # make empty DataFrame if not exist csv file.
    if not os.path.exists(Path_Data):
        df = pd.DataFrame(columns=['Year', 'Month', 'Date', 'Start Time', 'End Time'])
    else:
        df = pd.read_csv(Path_Data)

    # featch data from inputted form
    year = request.form['year']
    month = request.form['month']
    dates = request.form.getlist('date[]')
    start_times = request.form.getlist('start_time[]')
    end_times = request.form.getlist('end_time[]')

    # data to list
    new_data = []
    for i in range(len(dates)):
        new_data.append([int(year), int(month), int(dates[i]), start_times[i], end_times[i]])

    # Add new data
    new_df = pd.DataFrame(new_data, columns=['Year', 'Month', 'Date', 'Start Time', 'End Time'])
    df = pd.concat([df, new_df], ignore_index=True)

    # sort (Year → Month → Date → Start Time)
    df.sort_values(by=['Year', 'Month', 'Date', 'Start Time'], ascending=[True, True, True, True], inplace=True)

    # save csv
    df.to_csv(Path_Data, index=False)

    return redirect(url_for('index'))


if __name__ == "__main__":
    # 初回実行時のセットアップ
    if not os.path.exists(Path_Data):
        make_file(Path_Data)
    make_plot_folder(PLOT_FOLDER)  # プロットフォルダを必ず作成

    # 起動
    app.run(debug=True)
