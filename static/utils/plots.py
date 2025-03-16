import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas import DataFrame

# GUIに依存しないバックエンドを設定
matplotlib.use("Agg")

PLOT_FOLDER = "static/plots/"

# 月ごとのシフトリクエスト数をプロット
def generate_time_based_plots(df: DataFrame) -> str:
    if df.empty:
        return "No data"
    
    # 5:00 ~ 23:59までの30分単位でカウントするため、時間帯を設定
    time_slots = []
    for hour in range(5, 24):  # 5:00 ~ 23:00
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            time_slots.append(time_str)
    
    # 30分単位の時間帯をカウント
    time_counts = {slot: 0 for slot in time_slots}
    
    # シフトの開始時間と終了時間から、各30分単位にシフトが重なっているかをチェック
    for _, row in df.iterrows():
        start_time = row['Start Time']
        end_time = row['End Time']
        
        # 30分ごとの時間帯に分割
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour, end_minute = map(int, end_time.split(":"))
        
        # 開始から終了まで30分単位でカウント
        current_hour = start_hour
        current_minute = start_minute
        
        while (current_hour < end_hour) or (current_hour == end_hour and current_minute < end_minute):
            time_slot = f"{current_hour:02d}:{current_minute:02d}"
            if time_slot in time_counts:
                time_counts[time_slot] += 1
            
            current_minute += 30
            if current_minute == 60:
                current_minute = 0
                current_hour += 1

    times = list(time_counts.keys())
    counts = list(time_counts.values())

    plt.figure(figsize=(15, 6))
    sns.set_palette("coolwarm")
    sns.barplot(x=times, y=counts, linewidth=0)
    plt.xticks(rotation=90)
    plt.xlabel("Time Slot", color="white")
    plt.ylabel("Number of Shifts", color="white")
    plt.title("Shift Requests by 30-min Time Slot (5:00 - 23:59)", color="white")

    # 軸の色を変更
    plt.tick_params(axis="both", labelcolor="black", labelsize=14)  # メモリの色とサイズを設定
    plt.xticks(fontsize=14)  # x軸のラベルのフォントサイズを設定
    plt.yticks(fontsize=14)  # y軸のラベルのフォントサイズを設定
    
    plot_path = os.path.join(PLOT_FOLDER, "shift_requests_time_based.png")
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()

    return plot_path

# 曜日ごとのシフトリクエスト数をプロット
def generate_weekday_plots(df):
    if df.empty:
        return "No data"

    # Date, Month, Year 列を数値に変換
    df['Date'] = pd.to_numeric(df['Date'], errors='coerce')
    df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    # 'Date'、'Month'、'Year'を連結して日付として変換
    df['Weekday'] = pd.to_datetime(df['Date'].astype(str) + '-' + df['Month'].astype(str) + '-' + df['Year'].astype(str), format='%d-%m-%Y').dt.weekday
    weekday_counts = df['Weekday'].value_counts().sort_index()

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    counts = [weekday_counts.get(i, 0) for i in range(7)]

    plt.figure(figsize=(10, 6))
    sns.set_palette("coolwarm")
    sns.barplot(x=weekdays, y=counts, linewidth=0, color="lightblue")
    plt.title("Shift Requests by Weekday", color="white")
    plt.xlabel("Weekday", color="white")
    plt.ylabel("Number of Shifts", color="white")

    # 軸の色を変更
    plt.tick_params(axis="both", labelcolor="black", labelsize=14)  # メモリの色とサイズを設定
    plt.xticks(fontsize=14)  # x軸のラベルのフォントサイズを設定
    plt.yticks(fontsize=14)  # y軸のラベルのフォントサイズを設定


    plt.tick_params(axis="both", labelcolor="black")
    plot_path = os.path.join(PLOT_FOLDER, "shift_requests_weekday.png")
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()

    return plot_path


# 月ごとのシフトリクエスト数をプロット
def generate_monthly_plots(df):
    if df.empty:
        return "No data"

    monthly_counts = df.groupby(['Year', 'Month']).size().reset_index(name='Counts')

    plt.figure(figsize=(10, 6))
    sns.set_palette("coolwarm")
    sns.lineplot(x='Month', y='Counts', data=monthly_counts, hue='Year', marker='o', linewidth=2)
    plt.title("Shift Requests by Month", color="white")
    plt.xlabel("Month", color="white")
    plt.ylabel("Number of Shifts", color="white")
    # 軸の色を変更
    plt.tick_params(axis="both", labelcolor="black", labelsize=14)  # メモリの色とサイズを設定
    plt.xticks(fontsize=14)  # x軸のラベルのフォントサイズを設定
    plt.yticks(fontsize=14)  # y軸のラベルのフォントサイズを設定

    plot_path = os.path.join(PLOT_FOLDER, "shift_requests_monthly.png")
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()

    return plot_path


def generate_total_time_weekday_plots(df):
    if df.empty:
        return "No data"
    
    # 年・月・日を連結して日付型に変換し、曜日を取得
    df['Weekday'] = pd.to_datetime(
        df['Date'].astype(str) + '-' + df['Month'].astype(str) + '-' + df['Year'].astype(str),
        format='%d-%m-%Y'
    ).dt.weekday

    # シフトの開始時間・終了時間を datetime 型に変換
    df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M')
    df['End Time'] = pd.to_datetime(df['End Time'], format='%H:%M')

    # シフトの総時間（時間単位）を計算
    df['Total Time (Hours)'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / (60*60)

    # 曜日ごとの総募集時間を計算
    weekday_total_time = df.groupby('Weekday')['Total Time (Hours)'].sum()

    # 曜日ラベルを設定
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    total_time = [weekday_total_time.get(i, 0) for i in range(7)]

    # グラフを作成
    plt.figure(figsize=(10, 6))
    sns.set_palette("coolwarm")
    sns.barplot(x=weekdays, y=total_time, linewidth=0, color="lightcoral")

    # plt.title("Shift Requests Total Time by Weekday", color="black")
    plt.xlabel("Weekday", color="black")
    plt.ylabel("Total Time (Hours)", color="black")

    # 軸の色とラベルサイズを統一
    plt.tick_params(axis="both", labelcolor="black", labelsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 画像保存
    plot_path = os.path.join(PLOT_FOLDER, "shift_requests_weekday_total_time.png")
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()

    return plot_path


# 各日における募集数の推移
def generate_daily_plots(df):
    # 月と日を基にグループ化して、各日のシフト数をカウント
    daywise_counts = df.groupby(['Year', 'Month', 'Date']).size().reset_index(name='Counts')
    
    # プロットの作成
    plt.figure(figsize=(15, 6))
    sns.set_palette("coolwarm")
    sns.lineplot(x='Date', y='Counts', data=daywise_counts, hue='Month', marker='o', linewidth=2)
    plt.title("Shift Requests by Day", color="white")
    plt.xlabel("Day", color="white")
    plt.ylabel("Number of Shifts", color="white")

    # 軸の色を変更
    plt.tick_params(axis="both", labelcolor="black", labelsize=14)  # メモリの色とサイズを設定
    plt.xticks(fontsize=14)  # x軸のラベルのフォントサイズを設定
    plt.yticks(fontsize=14)  # y軸のラベルのフォントサイズを設定
    
    plot_path = os.path.join(PLOT_FOLDER, "shift_requests_by_day.png")
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()

    return plot_path

