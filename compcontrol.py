import os
import time
import getpass
import subprocess
import psutil
import webbrowser
import shutil

import telebot
from telebot import types, util

import pyautogui
from io import BytesIO
from win10toast import ToastNotifier
import wmi
import pythoncom

from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import pyaudio
import wave

import cv2
import numpy as np
import threading


try:
    with open("token.txt", "r") as f:
        TOKEN = f.readline()

except:
    raise Exception("""
    You do not have a token.txt file.
    If you don't have it, create a file token.txt.
    Create your bot in Telegram's BotFather bot.
    And paste a bot token you got into token.txt file.""")


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    items = ["Screenshot", "Click", "Write", "More functions", "Settings"]

    for item in items:
        markup.add(types.KeyboardButton(item))

    bot.send_message(message.chat.id, "Remote controller. Click /help if need help. Select action:", reply_markup=markup)


@bot.message_handler(commands=["help"])
def help(message):

    commands = [
        "start", "help", "screenshot", "click", "write",
        "create_folder", "create_file", "get_profile", "file_manager",
        "open_file_in_pc", "get_file_from_pc", "pc_battery", "get_disk_info",
        "open_link", "show_notification",
        "disk_wmi", "set_brightness_wmi", "set_volume_wmi", "open_app",
        "stop_bot", "Coming soon..."
    ]

    descriptions = [
        "start the bot", "get help", "create a screenshot and send by bot to chat", "click at x y coordinates", "write a text written by user",
        "create a folder with path and name at the end of path", "path and file with extension", "get name of the user uses pc", "hardest function, path and it will show what is in this folder",
        "open any flle with these exts: .mp3, .mp4, .mov, .avi", "download any file by path got from chat", "battery on user PC", "(deprecated, not working in exe) gets some info about disks",
        "send link and it will be open by webbrowser", "Notify user with title and description", 
        "Get disk info with wmi", "Send % \brightness", "Send % volume", "Send path/to/app.exe, send_welcome() not working",
        "stop the bot", "soon..."
    ]

    out_str = "It's message with all commands: \n"
    for i in range(len(commands)):
        out_str += "/" + commands[i] + " - " + descriptions[i] + ".\n"

    out_str += "If you send a photo/video/audio at any time it will be opened on PC. For example: you send an audio file, it opens and plays in default program.\n"

    for message1 in util.smart_split(out_str, 3000):
        bot.send_message(message.chat.id, message1)

    send_welcome(message)


@bot.message_handler(commands=["stop_bot"])
def stop_bot(message):
    bot.send_message(message.chat.id, "Now bot will be SHUTTED DOWN")
    bot.stop_bot()

def error(m, e):
    bot.send_message(m.chat.id, f"Произошла ошибка: {e}")
    send_welcome(m)


@bot.message_handler(commands=['screenshot'])
def send_screenshot(message):
    try:
        screenshot = pyautogui.screenshot()

        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        buffer.seek(0)

        bot.send_photo(message.chat.id, buffer)

    except Exception as e:
        error(message, e)


@bot.message_handler(commands=['click'])
def click_at_coordinates(message):
    bot.send_message(message.chat.id, "Введите координаты x и y через пробел:")
    bot.register_next_step_handler(message, handle_coordinates)

def handle_coordinates(message):
    try:
        x, y = map(int, message.text.split())
        pyautogui.click(x, y)
        bot.send_message(message.chat.id, f"Клик выполнен в координатах ({x}, {y})")
    except Exception as e:
        error(message, e)


@bot.message_handler(commands=["write"])
def write_text(message):
    bot.send_message(message.chat.id, "Введите текст")
    bot.register_next_step_handler(message, handle_text)

def handle_text(message):
    try:
        pyautogui.typewrite(message.text)
        bot.send_message(message.chat.id, "Текст введен: " + message.text)
    except Exception as e:
        error(message, e)


@bot.message_handler(commands=['create_folder'])
def create_folder(message):
    bot.send_message(message.chat.id, "Введите путь для создания папки:")
    bot.register_next_step_handler(message, handle_path)

def handle_path(message):
    path = message.text.strip()
    try:
        os.makedirs(path)
        bot.send_message(message.chat.id, f"Папка по пути {path} успешно создана!")
    except FileExistsError:
        bot.send_message(message.chat.id, f"Папка по пути {path} уже существует.")
    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=['create_file'])
def create_file(message):
    bot.send_message(message.chat.id, "Введите путь и содержимое файла с разделителем ';':")
    bot.register_next_step_handler(message, handle_path_file)

def handle_path_file(message):
    path, content = message.text.split(";", 1)
    try:
        with open(path, "w") as f:
            f.write(content)
        bot.send_message(message.chat.id, f"Файл по пути {path} с своим содержимим успешно создан")
    except FileExistsError:
        bot.send_message(message.chat.id, f"Файл по пути {path} уже существует.")
    except Exception as e:
        error(message, e)

    send_welcome(message)

@bot.message_handler(commands=['get_profile'])
def get_cur_user(message):
    try:
        current_user = getpass.getuser()
        bot.send_message(message.chat.id, f"Текущий пользователь компьютера: {current_user}")
    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=['file_manager'])
def list_file_step_1(message):
    bot.send_message(message.chat.id, "Пришлите путь")
    bot.register_next_step_handler(message, list_file_step_2)

def list_file_step_2(message):
    path = message.text
    try:
        contents = os.listdir(path)
        files_and_folders = [
            item for item in contents if
            os.path.isfile(os.path.join(path, item)) or os.path.isdir(os.path.join(path, item))
        ]

        out_str = f"Файлы в папке {path}:\n"
        for i in files_and_folders:
            out_str += i + "\n"

        bot.send_message(message.chat.id, out_str)

    except Exception as e:
        error(message, e)

    send_welcome(message)



def create_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)

    up = types.InlineKeyboardButton("⬆️", callback_data="up")
    down = types.InlineKeyboardButton("⬇️", callback_data="down")

    delete = types.InlineKeyboardButton("Delete", callback_data="delete")
    rename = types.InlineKeyboardButton("Rename", callback_data="rename")

    open_btn = types.InlineKeyboardButton("Open", callback_data="open")
    back = types.InlineKeyboardButton("Back", callback_data="back")

    new_folder = types.InlineKeyboardButton("New Folder", callback_data="new_folder")
    new_file = types.InlineKeyboardButton("New File", callback_data="new_file")

    get_file = types.InlineKeyboardButton("Get File from PC", callback_data="get_file")

    return markup.add(up, rename, down, delete, open_btn, back, new_folder, new_file, get_file)


def get_files_lisdir(path):
    contents = os.listdir(path)

    if contents == []:
        return "Папка пуста"

    files_and_folders = [
        item for item in contents if
        os.path.isfile(os.path.join(path, item)) or os.path.isdir(os.path.join(path, item))
    ]

    return files_and_folders

def create_manager_str(path, cursor, cursor_mark):
    out_str = f"Файлы в папке {path}:\n\n"
    files_and_folders = "Пусто"
    try:
        files_and_folders = get_files_lisdir(path)

        i = 0
        for file in files_and_folders:
            if cursor == i:
                out_str += cursor_mark + file + "\n"
            else:
                out_str += file + "\n"
            i += 1

    except Exception as e:
        error_str = f"Ошибка: {e}"
        out_str += error_str

    return [out_str, files_and_folders[cursor]]


def delete_file_or_dir(path):
    # chatGPT!
    if os.path.isdir(path):
        try:
            shutil.rmtree(path)
            return f"{path} удален"
        except Exception as e:
            return f"Неудалось удалить {path}: {e}"
    elif os.path.isfile(path):
        try:
            os.remove(path)
            return f"{path} удален"
        except Exception as e:
            return f"Неудалось удалить {path}: {e}"
    else:
        return f"{path} не папка или файл"

def delete_messages(message, messages: list):
    for m in messages:
        bot.delete_message(message.chat.id, m.message_id)


@bot.message_handler(commands=['file_manager_my_start'])
def file_manager_my_start(message):
    global cursor, path
    cursor = 0
    path = message.text.split(" ")[-1]
    cursor_mark = "➡️"

    try:
        out_str = create_manager_str(path, cursor, cursor_mark)
        manager_message = bot.send_message(message.chat.id, out_str, reply_markup=create_markup())

        def update_manager(callback=False, message=False, exception_if_exists = "", info = ""):
            if callback:
                bot.edit_message_text(create_manager_str(path, cursor, cursor_mark)[0] + exception_if_exists + info, callback.message.chat.id, manager_message.message_id, reply_markup=create_markup())
            else:
                bot.edit_message_text(create_manager_str(path, cursor, cursor_mark)[0] + exception_if_exists + info, message.chat.id, manager_message.message_id, reply_markup=create_markup())


        def change_direction(callback):
            global cursor
            if cursor < 0:
                cursor += 1
            elif cursor >= len(get_files_lisdir(path)):
                cursor -= 1

            update_manager(callback)

        @bot.callback_query_handler(func=lambda m: m.data == "down")
        def manager_down(callback):
            global cursor
            cursor = cursor + 1
            change_direction(callback)

        @bot.callback_query_handler(func=lambda m: m.data == "up")
        def manager_up(callback):
            global cursor
            cursor = cursor - 1
            change_direction(callback)

        @bot.callback_query_handler(func=lambda m: m.data == "open")
        def open_dir(callback):
            global path, cursor
            out = create_manager_str(path, cursor, cursor_mark)

            cursor = 0
            path = path + "\\" + out[-1]
            update_manager(callback)

        @bot.callback_query_handler(func=lambda m: m.data == "back")
        def back(callback):
            global path
            path = os.path.dirname(os.path.normpath(path))
            update_manager(callback)

        @bot.callback_query_handler(func=lambda m: m.data == "delete")
        def delete(callback):
            try:
                result_msg = delete_file_or_dir(os.path.normpath(path + "\\" + get_files_lisdir(path)[cursor]))
                update_manager(callback=callback, info="INFO: " + result_msg)
            except Exception as e:
                update_manager(callback=callback, exception_if_exists=f"Ошибка: {e}")

        @bot.callback_query_handler(func=lambda m: m.data == "new_folder")
        def new_folder(callback):
            m1 = bot.send_message(callback.message.chat.id, "Отправьте название папки")
            bot.register_next_step_handler(callback.message, new_folder_step, m1)

        def new_folder_step(message, m1):
            try:
                os.makedirs(path + str(message.text))
                update_manager(message=message, info=f"INFO: Папка по пути {path} успешно создана.")
                delete_messages(message, [m1, message])
            except Exception as e:
                update_manager(message=message, exception_if_exists=f"Ошибка: {e}")
                delete_messages(message, [m1, message])

        @bot.callback_query_handler(func=lambda m: m.data == "new_file")
        def new_file(callback):
            m1 = bot.send_message(callback.message.chat.id, "Отправьте название файла и, если это текст, то его содержимое с разделителем ;. Или готовый файл(photo/video/audio)")
            bot.register_next_step_handler(callback.message, new_file_step, m1)

        def new_file_step(message, m1):
            if message.content_type == "text":
                file_name, file_text = message.text.split(";")
                try:
                    with open(os.path.normpath(path + "\\" + str(file_name)), "w") as f:
                        f.write(file_text)
                    update_manager(message=message, info=f"INFO: Файл по пути {path} успешно создан.")
                except Exception as e:
                    update_manager(message=message, exception_if_exists=f"Ошибка: {e}")

            else:
                try:
                    open_file_media_sent_from_bot(message, path)
                    update_manager(message=message, info=f"INFO: Файл по пути {path} успешно создан(as sent).")
                except Exception as e:
                    update_manager(message=message, exception_if_exists=f"Ошибка: {e}")

            delete_messages(message, [m1, message])


        def rename_file_or_folder(message, inner_path, m1):
            new_name = message.text
            try:
                os.rename(inner_path, os.path.join(os.path.dirname(inner_path), new_name))
                update_manager(message=message, info=f"INFO: {inner_path} успешно переименован в {new_name}")
            except Exception as e:
                update_manager(message=message, exception_if_exists=f"Не удалось переименовать {inner_path}: {e}")

            delete_messages(message, [m1, message])

        @bot.callback_query_handler(func=lambda m: m.data == "rename")
        def rename(callback):
            m1 = bot.send_message(callback.message.chat.id, "На что переминовываем? (название файла или папки)")
            bot.register_next_step_handler(callback.message, rename_file_or_folder, 
                os.path.normpath(path + "\\" + create_manager_str(path, cursor, cursor_mark)[-1]), m1)

        @bot.callback_query_handler(func=lambda m: m.data == "get_file")
        def get_file(callback):
            callback.message.text = os.path.normpath(path + "\\" + create_manager_str(path, cursor, cursor_mark)[-1])
            get_file_from_pc_step(callback.message)

        @bot.message_handler(commands=["file_manager_my_end"])
        def end_manager(message):
            send_welcome(message)

    except Exception as e:
        error(message, e)


@bot.message_handler(commands=["open_file_in_pc"])
def open_file_media(message):
    path = message.text
    if not os.path.exists(path):
        bot.send_message(message.chat.id, f"Файл {path} не найден.")
        return

    file_ext = os.path.splitext(path)[-1]

    if file_ext == ".mp3":
        command = "start wmplayer \"" + path + "\""
    elif file_ext == ".mp4" or file_ext == ".avi" or file_ext == ".mov":
        command = "start \"" + path + "\""
    else:
        bot.send_message(message.chat.id, f"Невозможно открыть файл {path}.")
        return

    bot.send_message(message.chat.id, "command to subprocess.call(): " + command)
    subprocess.call(command, shell=True)
    send_welcome(message)


@bot.message_handler(content_types=['photo', 'video', 'audio', 'document'])
def open_file_media_sent_from_bot(message, path=os.getcwd(), open_now=False, send_welcome_now=False):
    mct = message.content_type

    if mct == "video": file_info = bot.get_file(message.video.file_id)
    elif mct == "audio": file_info = bot.get_file(message.audio.file_id)
    elif mct == "document": file_info = bot.get_file(message.document.file_id)
    elif mct == "photo": file_info = bot.get_file(message.photo[-1].file_id)

    file_path = os.path.join(path, os.path.normpath(file_info.file_path).split("\\")[-1])
    downloaded_file = bot.download_file(file_info.file_path)

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    if open_now:
        open_file(file_path)
    if send_welcome_now:
        send_welcome(message)

def open_file(path):
    if os.name == 'nt':
        # Windows
        os.startfile(path)
    elif os.name == 'posix':
        # Linux
        os.system(f'xdg-open "{path}"')


@bot.message_handler(commands=['get_file_from_pc'])
def get_file_from_pc(message):
    bot.send_message(message.chat.id, "Введите путь к файлу:")
    bot.register_next_step_handler(message, get_file_from_pc_step, True)

def get_file_from_pc_step(message, send_welcome_now=False):
    file_path = message.text

    if not os.path.exists(file_path):
        bot.send_message(message.chat.id, "Файл не найден")
        return

    with open(file_path, 'rb') as f:
        bot.send_document(message.chat.id, f)

    if send_welcome_now: send_welcome(message)


@bot.message_handler(commands=["pc_battery"])
def pc_battery(message):
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            percent = battery.percent
            bot.send_message(message.chat.id, f"Заряд батареи: {percent}%")
        else:
            bot.send_message(message.chat.id, "Батарея не обнаружена")
    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=["get_disk_info"])
def get_disk_info(message):
    out_disk_info = ""
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            disk = psutil.disk_usage(partition.mountpoint)
            out_disk_info += f"Диск {partition.mountpoint}:\n"
            out_disk_info += f"  Общий объем: {disk.total / 1024 / 1024 / 1024:.2f} ГБ\n"
            out_disk_info += f"  Свободное место: {disk.free / 1024 / 1024 / 1024:.2f} ГБ\n\n"

        bot.send_message(message.chat.id, out_disk_info)

    except Exception as e:
        error(message, e)
        bot.send_message(message.chat.id, out_disk_info)

    send_welcome(message)


@bot.message_handler(commands=['open_link'])
def open_link(message):
    bot.send_message(message.chat.id, "Введите ссылку для открытия webbrowser'ом")
    bot.register_next_step_handler(message, open_link_step)

def open_link_step(message):
    try:
        webbrowser.open(message.text)
    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=["show_notification"])
def show_notification(message):
    bot.send_message(message.chat.id, "Введите заголовок и сообщение с разделителем ;")
    bot.register_next_step_handler(message, show_notification_step)

def show_notification_step(message):
    try:
        title = message.text.split(";")[0]
        message_text = message.text.split(";")[-1]
        toaster = ToastNotifier()
        toaster.show_toast(title, message_text)
    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=["disk_wmi"])
def disk_wmi(message):
    out = "Disk wmi:\n"
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()

        for disk in c.Win32_LogicalDisk():
            out += f"""
            DeviceID: {disk.DeviceID}
            VolumeName: {disk.VolumeName}
            FileSystem: {disk.FileSystem}
            Description: {disk.Description}

            In Bytes:
            Size: {disk.Size} B
            FreeSpace: {disk.FreeSpace} B

            More accurate:
            Size_GB = {int(disk.Size) / (1024**3)} GB
            FreeSpace_GB = {int(disk.FreeSpace) / (1024**3)} GB

            More readable:
            Size_GB_round = {round(int(disk.Size) / 1_000_000_000, 2)} GB
            FreeSpace_GB_round = {round(int(disk.FreeSpace) / 1_000_000_000, 2)} GB"""

    except Exception as e:
        error(message, e)

    bot.send_message(message.chat.id, out)
    send_welcome(message)

@bot.message_handler(commands=["set_brightness_wmi"])
def set_brightness_wmi(message):
    bot.send_message(message.chat.id, "Сколько процентов якркости установить через wmi?")
    bot.register_next_step_handler(message, set_brightness_wmi_step)

def set_brightness_wmi_step(message):
    try:
        brightness = int(message.text)
        if brightness < 0:
            bot.send_message(message.chat.id, "Проценты меньше нуля? Интересно...")
            send_welcome(message)
            return

        brightness = int(brightness * 255 / 100)  # преобразуем проценты в значение от 0 до 255
        pythoncom.CoInitialize()
        c = wmi.WMI(namespace='wmi')

        methods = c.WmiMonitorBrightnessMethods()[0]  # получаем доступ к методам изменения яркости экрана
        methods.WmiSetBrightness(brightness, 0)  # изменяем яркость экрана
        bot.send_message(message.chat.id, f"Яркость в {brightness}% установлена")

    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=["set_volume_wmi"])
def set_volume_wmi(message):
    bot.send_message(message.chat.id, "Введите % громкости")
    bot.register_next_step_handler(message, set_volume_pycaw)

def set_volume_pycaw(message):
    volume_level = message.text
    try:
        pythoncom.CoInitialize()
        sessions = AudioUtilities.GetAllSessions()

        out_str = "Изменен звук для: \n"
        for session in sessions:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            volume.SetMasterVolume(float(volume_level) / 100, None)
            out_str += str(volume) + "\n"
        bot.send_message(message.chat.id, out_str)

    except Exception as e:
        error(message, e)

    send_welcome(message)


@bot.message_handler(commands=["open_app"])
def open_app(message):
    bot.send_message(message.chat.id, "Send path/to/app.exe")
    bot.register_next_step_handler(message, open_app_step)

def open_app_step(message):
    try:
        subprocess.run(message.text)
    except FileNotFoundError as fnfe:
        bot.send_message(message.chat.id, f"FileNotFoundError: {fnfe}")
    except Exception as e:
        error(message, e)


recording = False
out = None

active_device = "screen"

@bot.message_handler(commands=['rec'])
def handle_rec(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    start_button = types.InlineKeyboardButton(text='Включить запись', callback_data="rec_on")
    stop_button = types.InlineKeyboardButton(text='Остановить запись', callback_data="rec_off")
    select_device_button = types.InlineKeyboardButton(text='Выбор устройства', callback_data="select_device")
    quit_button = types.InlineKeyboardButton(text='Выйти из приложения записи', callback_data="quit_rec")

    keyboard.row(start_button, stop_button)
    keyboard.add(select_device_button, quit_button)


    rec_msg = bot.send_message(message.chat.id, 
                               f"Текущее устройство: {active_device} \nВыберите действие", 
                               reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda m: m.data == "select_device")
    def select_device(callback):
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        screen = types.InlineKeyboardButton(text='Экран', callback_data="screen")
        camera = types.InlineKeyboardButton(text='Камера', callback_data="camera")
        audio = types.InlineKeyboardButton(text='Звук', callback_data="audio")
        keyboard.row(screen, camera, audio)
        bot.edit_message_text('Выберите устройство:', callback.message.chat.id, rec_msg.message_id, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda m: 
                                (m.data == "screen") or
                                (m.data == "camera") or
                                (m.data == "audio"))
    def selected(callback):
        global active_device
        print(callback.data)
        print(active_device)
        if callback.data == "screen": active_device = "screen"
        elif callback.data == "camera": active_device = "camera"
        elif callback.data == "audio": active_device = "audio"

        print(active_device)

        bot.edit_message_text(f"Текущее устройство: {active_device} \nВыберите действие",
                              callback.message.chat.id,
                              rec_msg.message_id,
                              reply_markup=keyboard)


    @bot.callback_query_handler(func=lambda m: m.data == "rec_on")
    def start_recording(callback):
        if active_device == "screen": start_recording_screen(callback)
        elif active_device == "camera": start_recording_video(callback)
        elif active_device == "audio": start_recording_audio(callback)

    @bot.callback_query_handler(func=lambda m: m.data == "rec_off")
    def stop_recording(callback):
        if active_device == "screen": stop_recording_screen(callback)
        elif active_device == "camera": stop_recording_video(callback)
        elif active_device == "audio": stop_recording_audio()

    def start_recording_screen(callback):
        global recording, out
        if recording:
            bot.edit_message_text("Запись уже идет!", callback.message.chat.id,
                                  rec_msg.message_id, reply_markup=keyboard)
            return
        recording = True
        out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'XVID'), 30, (1920, 1080))
        bot.edit_message_text("Запись включена", callback.message.chat.id,
                              rec_msg.message_id, reply_markup=keyboard)
        t = threading.Thread(target=record_screen)
        t.start()

    def stop_recording_screen(callback):
        global recording, out
        if not recording:
            bot.edit_message_text('Запись не запущена!', callback.message.chat.id,
                                  rec_msg.message_id, reply_markup=keyboard)
            return
        recording = False
        out.release()
        bot.edit_message_text('Запись остановлена!', callback.message.chat.id,
                              rec_msg.message_id, reply_markup=keyboard)
        callback.message.text = os.path.normpath(f"{os.getcwd()}\output.mp4")
        get_file_from_pc_step(callback.message)
        os.remove(callback.message.text)


    def record_screen():
        global recording, out
        while recording:
            img = pyautogui.screenshot()
            img_np = np.array(img)
            frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
            out.write(frame)
            time.sleep(0.033)

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    def start_recording_audio(callback):
        global audio_frames
        audio_frames = []
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while True:
            try:
                data = stream.read(CHUNK)
                audio_frames.append(data)
            except KeyboardInterrupt:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(audio_frames))
        wf.close()

        with open("audio.wav", "rb") as f:
            bot.send_audio(callback.message.chat.id, f)
        os.remove("audio.wav")

    def stop_recording_audio():
        global audio_frames
        if audio_frames:
            audio_frames = []

    cap = cv2.VideoCapture(0)

    def start_recording_video(callback):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 30

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter("output.mp4", fourcc, fps, (width, height))

        bot.edit_message_text("Запись видео началась", callback.message.chat.id, rec_msg.message_id, reply_markup=keyboard)

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()
        out.release()
        print("it is start_recording_video")

    def stop_recording_video(callback):
        cap.release()

        with open("output.mp4", "rb") as video:
            bot.send_video(callback.message.chat.id, video)

        bot.edit_message_text("Запись видео остановлена, файл отправляется", callback.message.chat.id, rec_msg, reply_markup=keyboard)

        print("it is stop_recording_video")


    @bot.callback_query_handler(func=lambda m: m.data == "quit_rec")
    def quit_rec(callback):
        global recording, out
        recording = False
        out.release()
        send_welcome(callback.message)




@bot.message_handler(func=lambda message: True)
def handle_start(message):
    mt = message.text

    if mt == "Screenshot": send_screenshot(message)
    elif mt == "Click": click_at_coordinates(message)
    elif mt == "Write": write_text(message)
    elif mt == "More functions":
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        items = ["Create Folder", "Create File", "Get Cur User", "File Manager", "Open Media on PC", "Send Media and open", "Next >"]

        for item in items:
            markup.add(types.KeyboardButton(item))

        bot.send_message(message.chat.id, "Больше функций: ", reply_markup=markup)

        bot.register_next_step_handler(message, handle_more_functions)

    elif mt == "Settings":
        bot.send_message(message.chat.id, "There is no settings yet...")

    else: not_understand(message)


def handle_more_functions(message):
    mt = message.text

    if mt == "Get Cur User": get_cur_user(message)
    elif mt == "Create Folder": create_folder(message)
    elif mt == "Create File": create_file(message)
    elif mt == "File Manager": file_manager_my_start(message)
    elif mt == "Open Media on PC":
        bot.send_message(message.chat.id, "Введите путь к файлу, чтобы открыть его на компьютере")
        bot.register_next_step_handler(message, open_file_media)
    elif mt == "Send Media and open":
        bot.send_message(message.chat.id, "Отправьте файл чтобы его открыть на компьютере (photo/video/audio)")
        bot.register_next_step_handler(message, open_file_media_sent_from_bot, open_now=True, send_welcome_now=True)
    elif mt == "Next >":
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        items = ["Open Link", "Download file from PC", "Get PC Battery", "Get Disk Info", "Notify", "Disk WMI", "< Previous", "Next >"]

        for item in items:
            markup.add(types.KeyboardButton(item))

        bot.send_message(message.chat.id, "More Functions page 2:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_more_functions_2page)

    else: not_understand(message)


def handle_more_functions_2page(message):
    mt = message.text

    if mt == "Open Link": open_link(message)
    elif mt == "Download file from PC": get_file_from_pc(message)
    elif mt == "Get PC Battery": pc_battery(message)
    elif mt == "Get Disk Info": get_disk_info(message)
    elif mt == "Notify": show_notification(message)
    elif mt == "Disk WMI": disk_wmi(message)
    elif mt == "< Previous":
        message.text = "More functions"
        handle_start(message)
    else: not_understand(message)

@bot.message_handler(content_types=["text"])
def not_understand(message):
    bot.send_message(message.chat.id, "I don't understand you, redirect to main")
    send_welcome(message)

bot.infinity_polling()