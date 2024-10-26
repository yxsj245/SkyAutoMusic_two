import os
import subprocess
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox
from tkinter import filedialog
import re

import psutil
from tkinterdnd2 import DND_FILES, TkinterDnD
import shutil
import glob
import zipfile

#--初始化变量---
process = None
is_running = False


# ---方法库---
# 删除后缀.txt文件
def delete_txt_files():
    # 定义目标目录
    target_directory = os.path.join(os.getcwd(), 'score', 'score')

    # 使用 os.walk 递归遍历目录
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                os.remove(file_path)  # 删除 .txt 文件
                # print(f"已删除文件: {file_path}")
# 自动创建曲谱目录
def create_score_directory():
    # 定义目录路径
    directory_path = os.path.join(os.getcwd(), 'score', 'score')

    # 创建目录层级，如果已存在则忽略
    os.makedirs(directory_path, exist_ok=True)
# 拖拽文件并移动
def create_drag_and_drop_window():
    # 创建顶层窗口
    root = TkinterDnD.Tk()
    root.title("拖拽文件并复制")
    root.geometry("300x200")

    # 设置窗口在最前面
    root.attributes('-topmost', True)

    # 标签显示提示
    label = tk.Label(root, text="将文件拖拽到这里，或点击选择文件", pady=20)
    label.pack(expand=True)

    # 定义目标目录
    target_directory = os.path.join(os.getcwd(), 'score', 'score')
    os.makedirs(target_directory, exist_ok=True)

    # 文件复制方法
    def copy_files_to_score_directory(file_paths):
        # print(file_paths)
        for file_path in file_paths:
            if os.path.isfile(file_path):  # 确保路径是文件
                shutil.copy(file_path, target_directory)
                # print(f"已复制文件: {file_path} 到 {target_directory}")
        rename_files_to_json()  # 复制完成后调用重命名方法
        delete_txt_files() #清理文件
        messagebox.showinfo('成功','完毕')

    # 文件拖拽回调
    def drop(event):
        file_paths = event.data # 拆分为列表
        # 去除大括号
        cleaned_data = file_paths.strip('{}')
        # 使用正则表达式提取以 .txt 或 .json 结尾的文件路径
        file_paths = re.findall(r'([A-Z]:[\\/].+?\.(txt|json))', cleaned_data)
        # 提取文件路径并保留绝对路径
        file_paths = [match[0] for match in file_paths]
        # print(file_paths)
        copy_files_to_score_directory(file_paths)

    # 绑定拖拽事件
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', drop)

    # 点击选择文件
    def select_file():
        file_paths = filedialog.askopenfilenames()  # 允许选择多个文件
        if file_paths:
            copy_files_to_score_directory(file_paths)

    # 点击事件
    label.bind("<Button-1>", lambda e: select_file())

    # 窗口关闭时执行的操作
    def on_closing():
        show_main_menu()  # 调用主菜单函数
        root.destroy()  # 销毁窗口

    root.protocol("WM_DELETE_WINDOW", on_closing)  # 绑定关闭事件

    # 启动主循环
    root.mainloop()

# 重命名目录下所有文件后缀
def rename_files_to_json():
    # 定义目标目录
    target_directory = os.path.join(os.getcwd(), 'score', 'score')

    # 获取目录下所有文件
    for file_path in glob.glob(os.path.join(target_directory, '*')):
        # 检查是否为文件
        if os.path.isfile(file_path):
            # 获取文件名和扩展名
            base = os.path.splitext(file_path)[0]
            new_file_path = f"{base}.json"  # 新的文件路径

            # 重命名文件
            try:
                os.rename(file_path, new_file_path)
            except FileExistsError as e:
                pass
            # print(f"已重命名文件: {file_path} 为 {new_file_path}")
# 递归重命名目录下所有文件后缀
def renamedigui_files_to_json():
    # 定义目标目录
    target_directory = os.path.join(os.getcwd(), 'score', 'score')

    # 遍历目录及其子目录
    for dirpath, dirnames, filenames in os.walk(target_directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # 获取文件名和扩展名
            base = os.path.splitext(file_path)[0]
            new_file_path = f"{base}.json"  # 新的文件路径

            # 重命名文件
            os.rename(file_path, new_file_path)
            # print(f"已重命名文件: {file_path} 为 {new_file_path}")

def add_files_to_json(directory):
    # 获取目录下所有文件
    for file_path in glob.glob(os.path.join(directory, '*')):
        # 检查是否为文件
        if os.path.isfile(file_path):
            # 获取文件名和扩展名
            base = os.path.splitext(file_path)[0]
            new_file_path = f"{base}.json"  # 新的文件路径

            # 重命名文件
            os.rename(file_path, new_file_path)
            # print(f"已重命名文件: {file_path} 为 {new_file_path}")


def extract_zip_and_copy_files(zip_path, target_directory, status_label):

    # 更新状态信息
    status_label.config(text="正在解压...")

    # 解压缩ZIP文件
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_directory)  # 解压到目标目录
        # print(f"已解压文件: {zip_path}")


    # 调用重命名方法
    renamedigui_files_to_json()

    # 更新状态信息
    status_label.config(text="解压完成。")
    messagebox.showinfo('成功','导入完毕')
    enable_drag_and_drop()  # 解压完成后启用拖拽


def threaded_extraction(zip_path, target_directory, status_label):
    disable_drag_and_drop()  # 开始解压前禁用拖拽
    extract_zip_and_copy_files(zip_path, target_directory, status_label)


def disable_drag_and_drop():
    global drag_enabled
    drag_enabled = False


def enable_drag_and_drop():
    global drag_enabled
    drag_enabled = True


def create_zip_drag_and_drop_window():
    global root, drag_enabled  # 使用全局变量以便在其他函数中访问
    root = TkinterDnD.Tk()
    root.title("拖拽 ZIP 文件并解压")
    root.geometry("300x200")

    # 设置窗口在最前面
    root.attributes('-topmost', True)

    # 标签显示提示
    label = tk.Label(root, text="将 ZIP 文件拖拽到这里", pady=20)
    label.pack(expand=True)

    # 状态标签
    status_label = tk.Label(root, text="", pady=10)
    status_label.pack()

    # 定义目标目录
    target_directory = os.path.join(os.getcwd(), 'score', 'score')
    os.makedirs(target_directory, exist_ok=True)

    # 默认启用拖拽
    drag_enabled = True

    # 文件拖拽回调
    def drop(event):
        if not drag_enabled:
            return  # 如果拖拽被禁用，直接返回

        file_paths = event.data.split()  # 拆分为列表
        for file_path in file_paths:
            if file_path.lower().endswith('.zip'):  # 将文件路径转换为小写再检查是否为 ZIP 文件
                # print(f"拖拽的 ZIP 文件: {file_path}")
                # 在新线程中解压缩
                threading.Thread(target=threaded_extraction, args=(file_path, target_directory, status_label)).start()
            else:
                messagebox.showwarning('注意','仅支持 .zip 格式')

    # 绑定拖拽事件
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', drop)

    # 启动主循环
    root.mainloop()

# 停止进程
def stop_process():
    global process, is_running
    if process and is_running:
        ps_process = psutil.Process(process.pid)
        for child in ps_process.children(recursive=True):  # 终止所有子进程
            child.terminate()
        ps_process.terminate()  # 终止主进程
        ps_process.wait()  # 等待进程完全结束
        is_running = False
        but1.config(text="启动自动弹琴程序",command=start_process)

# 监控进程状态的线程
def monitor_process():
    global process, is_running
    was_running = False  # 记录之前的状态
    while True:
        if process:
            if is_running and not was_running:
                but1.config(state=tk.NORMAL, text="停止运行", command=stop_process)
                mainmenu.iconify()
                but2.config(state=tk.DISABLED)
                but3.config(state=tk.DISABLED)
                # print("检测到进程启动")  # 检测到进程启动时执行的代码
                was_running = True  # 更新状态

            elif not is_running and was_running:
                # print("检测到进程结束")  # 检测到进程结束时执行的代码
                but1.config(text="启动自动弹琴程序", command=start_process)
                mainmenu.deiconify()
                but2.config(state=tk.NORMAL)
                but3.config(state=tk.NORMAL)
                was_running = False  # 重置状态

            if process.poll() is not None:  # 检查进程是否已结束
                is_running = False

        time.sleep(1)



# ---运行方法库---
# 拖拽文件后执行的代码
def show_main_menu():
    rename_files_to_json()
# 导入曲谱
def addShere():
    create_zip_drag_and_drop_window()

# 进入自动弹琴
def start_process():
    global process, is_running
    if not is_running:
        try:
            process = subprocess.Popen(["光遇自动弹琴软件.exe"])
            is_running = True
            but1.config(state=tk.DISABLED,text="正在执行启动程序")
            def main():
                monitor_process()
            thread1 = threading.Thread(target=main)
            thread1.start()
        except Exception as e:
            but1.config(state=tk.NORMAL, text="启动自动弹琴程序", command=start_process)
            messagebox.showerror("错误", f"无法启动进程:请确认自动弹琴软件名字是否为“光遇自动弹琴软件.exe”并存放在当前目录下")
            webbrowser.open('https://gitee.com/xiao-zhu245/SkyAutoMusic/releases')


create_score_directory()
button_padding = (10, 5)
global mainmenu
mainmenu = tk.Tk()
mainmenu.geometry("305x180")  # 设置窗口大小
mainmenu.minsize(305,180)

mainmenu.title('自动弹琴管理器1.0')

tk.Label(mainmenu, text='————安装————', font=('微软雅黑', 16)).place(relx=0.5, y=40, anchor='center')
but2 = ttk.Button(mainmenu, text='安装曲谱', command=create_drag_and_drop_window, padding=button_padding)
but2.place(relx=0.3, y=90, anchor='center')
but3 = ttk.Button(mainmenu, text='从压缩包中导入曲谱', command=addShere, padding=button_padding)
but3.place(relx=0.7, y=90, anchor='center')
but1 = ttk.Button(mainmenu, text='启动自动弹琴程序', command=start_process, padding=(50, 10))
but1.place(relx=0.5, y=140, anchor='center')


mainmenu.mainloop()