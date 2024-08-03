import time
import keyboard
import json
import pygetwindow as gw
import os
import chardet
import codecs
import threading
import tkinter as tk

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
        print(f"读取JSON文件出错: {e}")
        return None


# 播放曲谱
def play_song(song_data, stop_event, status_window):
    start_time = time.time()
    prev_note_time = song_data[0]['songNotes'][0]["time"]
    for note in song_data[0]["songNotes"]:
        if stop_event.is_set():
            break

        delay = note["time"] - prev_note_time
        time.sleep(delay / 1000)
        press_key(note["key"], 6 / song_data[0]["bpm"])
        prev_note_time = note["time"]

    end_time = time.time()
    total_time = end_time - start_time

    # 使用事件机制将GUI更新任务放到主线程
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
            selected_song = songs[selected_index[0]]
            root.destroy()
            start_song(selected_song)

    root = tk.Tk()
    root.title("曲目选择")
    root.geometry("300x300")
    root.attributes('-topmost', True)

    listbox = tk.Listbox(root)
    for song in songs:
        listbox.insert(tk.END, song)
    listbox.pack(fill=tk.BOTH, expand=True)

    select_button = tk.Button(root, text="选择", command=on_select)
    select_button.pack()

    root.mainloop()


# 显示状态窗口并提供停止按钮
def show_status_window(song_name, stop_event, status_window=None, total_time=None):
    def on_stop():
        stop_event.set()
        window.destroy()

    window = tk.Tk()
    window.title("曲谱状态")
    window.geometry("300x100")
    window.attributes('-topmost', True)

    global status_var
    status_var = tk.StringVar()
    status_var.set(f"正在演奏: {song_name}")

    label = tk.Label(window, textvariable=status_var)
    label.pack(expand=True)

    stop_button = tk.Button(window, text="停止", command=on_stop)
    stop_button.pack()

    # 绑定事件
    window.bind("<<UpdateStatus>>", lambda e: update_status(status_window, f"曲谱演奏完成！总共用时：{total_time:.2f}秒"))

    return window


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
    song_data = load_json(os.path.join(songs_folder, chosen_song + '.json'))
    if song_data:
        sky_windows = None
        window = gw.getWindowsWithTitle("Sky")
        sky_windows = [win for win in window if win.title == "Sky"]
        if sky_windows:
            sky_window = window[0]
            sky_window.activate()
        else:
            print("未找到名为'Sky'的窗口")
            print(window)
            input("按任意键退出")
            exit()

        stop_event = threading.Event()
        status_window = show_status_window(chosen_song, stop_event)

        # 使用线程安全地启动播放曲谱的线程
        play_thread = threading.Thread(target=play_song, args=(song_data, stop_event, status_window))
        play_thread.start()

        status_window.mainloop()

        # 等待播放线程结束
        play_thread.join()


# 主程序循环
def main():
    songs_folder = "score/score/"
    while True:
        songs = [f.replace('.json', '') for f in os.listdir(songs_folder) if f.endswith('.json')]
        show_song_selection_window(songs)


if __name__ == "__main__":
    main()
