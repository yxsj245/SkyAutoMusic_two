import sys
import time
import keyboard
import json
import pygetwindow as gw
import os
import chardet
import codecs
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# 键位映射表
key_mapping = {
    "1Key0": "Y", "1Key1": "U", "1Key2": "I", "1Key3": "O", "1Key4": "P",
    "1Key5": "H", "1Key6": "J", "1Key7": "K", "1Key8": "L", "1Key9": ";",
    "1Key10": "N", "1Key11": "M", "1Key12": ",", "1Key13": ".", "1Key14": "/",
    "2Key0": "Y", "2Key1": "U", "2Key2": "I", "2Key3": "O", "2Key4": "P",
    "2Key5": "H", "2Key6": "J", "2Key7": "K", "2Key8": "L", "2Key9": ";",
    "2Key10": "N", "2Key11": "M", "2Key12": ",", "Key13": ".", "Key14": "/"
}

# 加载JSON文件
def load_json(file_path):
    with open(file_path, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']

    try:
        with codecs.open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        messagebox.showerror('致命错误',f'读取JSON文件出错: {e}')
        sys.exit(1)

# 格式化时间
def format_time(milliseconds):
    seconds = milliseconds / 1000
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02}:{seconds:02}"

# 播放曲谱
def play_song(song_data, stop_event, pause_event, status_window, progress_bar, time_label, total_duration):
    start_time = time.time()
    prev_note_time = song_data[0]['songNotes'][0]["time"]
    total_notes = len(song_data[0]["songNotes"])

    for i, note in enumerate(song_data[0]["songNotes"]):
        if stop_event.is_set():
            break

        while pause_event.is_set():
            time.sleep(0.1)

        delay = note["time"] - prev_note_time
        time.sleep(delay / 1000)
        press_key(note["key"], 6 / song_data[0]["bpm"])
        prev_note_time = note["time"]

        progress_bar['value'] = (i + 1) / total_notes * 100
        status_window.update_idletasks()

        elapsed_time = time.time() - start_time
        time_label.config(text=f"{format_time(elapsed_time * 1000)}/{format_time(total_duration)}")
        status_window.update_idletasks()

    total_time = time.time() - start_time
    status_window.event_generate("<<UpdateStatus>>", when="tail")
    status_window.after_idle(lambda: update_status(status_window, f"曲谱演奏完成！总共用时：{total_time:.2f}秒"))

# 更新状态函数
def update_status(status_window, message):
    status_var.set(message)

# 显示曲谱选择窗口
def show_song_selection_window(songs):
    def on_select():
        selected_index = listbox.curselection()
        if selected_index:
            selected_song = filtered_songs[selected_index[0]]
            root.destroy()
            start_song(selected_song)

    def on_close():
        sys.exit(0)

    def update_listbox(event):
        search_term = search_entry.get().lower()
        filtered_songs.clear()
        for song in songs:
            if search_term in song.lower():
                filtered_songs.append(song)
        listbox.delete(0, tk.END)
        for song in filtered_songs:
            listbox.insert(tk.END, song)

    root = tk.Tk()
    root.title("曲目选择")
    root.geometry("300x400")
    root.attributes('-topmost', True)

    root.protocol("WM_DELETE_WINDOW", on_close)  # 处理窗口关闭事件

    search_label = tk.Label(root, text="搜索:")
    search_label.pack(pady=5)

    search_entry = tk.Entry(root)
    search_entry.pack(pady=5)
    search_entry.bind('<KeyRelease>', update_listbox)

    listbox = tk.Listbox(root)
    listbox.pack(fill=tk.BOTH, expand=True, pady=5)

    filtered_songs = songs.copy()
    for song in filtered_songs:
        listbox.insert(tk.END, song)

    select_button = tk.Button(root, text="选择", command=on_select)
    select_button.pack(pady=5)

    root.mainloop()

# 显示状态窗口并提供暂停、恢复、停止按钮
def show_status_window(song_name, stop_event, pause_event, total_duration, total_time=None):
    def on_close():
        messagebox.showwarning('注意','为保证程序能够正常退出,请先停止播放等待返回主菜单后再进行关闭')
    def on_stop():
        stop_event.set()
        window.destroy()

    def on_pause():
        pause_event.set()
        pause_button.config(state=tk.DISABLED)
        resume_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)

    def on_resume():
        pause_event.clear()
        pause_button.config(state=tk.NORMAL)
        resume_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

    window = tk.Tk()
    window.title("曲谱状态")
    window.geometry("300x250")
    window.attributes('-topmost', True)

    window.protocol("WM_DELETE_WINDOW", on_close)  # 处理窗口关闭事件

    global status_var
    status_var = tk.StringVar()
    status_var.set(f"正在演奏: {song_name}")

    label = tk.Label(window, textvariable=status_var)
    label.pack(expand=True)

    progress_bar = ttk.Progressbar(window, orient="horizontal", length=200, mode="determinate")
    progress_bar.pack(pady=10)

    time_label = tk.Label(window, text=f"00:00/{format_time(total_duration)}")
    time_label.pack(pady=10)

    pause_button = tk.Button(window, text="暂停", command=on_pause)
    pause_button.pack(pady=5)

    resume_button = tk.Button(window, text="恢复", command=on_resume, state=tk.DISABLED)
    resume_button.pack(pady=5)

    stop_button = tk.Button(window, text="停止", command=on_stop)
    stop_button.pack()

    window.bind("<<UpdateStatus>>", lambda e: update_status(window, f"曲谱演奏完成！总共用时：{total_time:.2f}秒"))

    return window, progress_bar, time_label

# 模拟按键
def press_key(key, time_interval):
    if key in key_mapping:
        key_to_press = key_mapping[key]
        keyboard.press(key_to_press)
        time.sleep(time_interval)
        keyboard.release(key_to_press)

# 启动选中的曲目
def start_song(chosen_song):
    songs_folder = "score/score/"
    song_data = load_json(os.path.join(songs_folder, chosen_song))
    if song_data:
        sky_window = None
        window = gw.getWindowsWithTitle("Sky")
        sky_windows = [win for win in window if win.title == "Sky"]
        if sky_windows:
            sky_window = sky_windows[0]
            sky_window.activate()
        else:
            messagebox.showerror('错误','未找到游戏窗口')
            exit()
        try:
            total_duration = song_data[0]["songNotes"][-1]["time"]
        except TypeError as e:
            messagebox.showerror('错误','当前曲谱版本不支持')

        stop_event = threading.Event()
        pause_event = threading.Event()
        status_window, progress_bar, time_label = show_status_window(chosen_song, stop_event, pause_event, total_duration)

        play_thread = threading.Thread(target=play_song, args=(song_data, stop_event, pause_event, status_window, progress_bar, time_label, total_duration))
        play_thread.start()

        status_window.mainloop()

        play_thread.join()

# 获取目录下所有JSON文件（包括子目录）
def get_all_json_files(folder):
    json_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.relpath(os.path.join(root, file), folder).replace('\\', '/'))
    return json_files

# 主程序循环
def main():
    songs_folder = "score/score"
    while True:
        songs = get_all_json_files(songs_folder)
        show_song_selection_window(songs)

if __name__ == "__main__":
    main()
