import os
import re
import time
import queue
import asyncio
import threading
import subprocess
import webbrowser
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import scrolledtext

import speech_recognition as sr
import pyautogui
import psutil
from deep_translator import GoogleTranslator
import pygame
import edge_tts
from pydub import AudioSegment
import pygetwindow as gw

# Initializam mixer-ul audio
pygame.mixer.init()

# =========================
# CONFIGURARE & INIȚIALIZARE
# =========================

# Adaugate variatii fonetice frecvente detectate de Google Speech Recognition
WAKE_WORDS = ["colea", "colia", "kolea", "alea", "culea", "jora"]

# Vocea masculina nativa in romana de la Microsoft
VOICE_ROMANIAN_MALE = "ro-RO-EmilNeural"

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

stop_program = False

# -------------------------
# FEREASTRA COLEA (GUI)
# -------------------------

root = tk.Tk()
root.title("Colea - Asistentul Tău Vocal")
root.geometry("850x620")
root.minsize(700, 500)

title = tk.Label(root, text="Asistentul_COLEA", font=("Arial", 24, "bold"))
title.pack(pady=(10, 2))

status_label = tk.Label(root, text="Sistemul este online...", font=("Arial", 11))
status_label.pack(pady=2)

# -------------------------
# PANOU INTERACTIV DE TEXT PENTRU PREZENTARE (1-6)
# -------------------------

input_frame = tk.Frame(root, bg="#f0f0f0", bd=2, relief=tk.GROOVE)
input_frame.pack(fill="x", padx=20, pady=10)

entry_label = tk.Label(input_frame, text="Tastează cifra (1-6) pentru prezentare:", font=("Arial", 10, "bold"), bg="#f0f0f0")
entry_label.pack(side="left", padx=5)

entry_box = tk.Entry(input_frame, font=("Arial", 12))
entry_box.pack(side="left", fill="x", expand=True, padx=5, pady=5)

def process_text_input(event=None):
    user_text = entry_box.get().strip()
    entry_box.delete(0, tk.END)

    if not user_text:
        return

    # Scurtături numerice pentru prezentare fix pe cerințele tale
    if user_text == "1":
        log("TASTATURĂ [1]: Execuție prezentare Colea")
        introduce_self()
        return
    elif user_text == "2":
        log("TASTATURĂ [2]: Execuție mesaj Demo")
        speak("Această funcție nu este disponibilă în versiunea Demo. Vă rugăm achiziționați pachetul Premium sau puneți-vă la treabă.")
        return
    elif user_text == "3":
        log("TASTATURĂ [3]: Execuție glumă director")
        speak("Am găsit 2 milioane de rezultate. Primul sfat: Fă-te că lucrezi când trece directorul.")
        return
    elif user_text == "4":
        log("TASTATURĂ [4]: Execuție baterie Dan")
        speak("Scanare finalizată. Bateria angajatului Dan: 1%. Se recomandă conectarea la priză sau o pauză de masă de 3 ore.")
        return
    elif user_text == "5":
        log("TASTATURĂ [5]: Execuție închidere ședință")
        speak("Am înțeles. Se închide ședința. Vă doresc o zi sporită la zarplată!")
        return
    elif user_text == "6":
        log("TASTATURĂ [6]: Execuție modul Praznik, pauză 2 secunde și muzică")
        def run_praznik_sequence():
            # Rostește textul și așteaptă până se termină audio-ul
            temp_file = "colea_praznik.mp3"
            text_praznik = "ooi Comandă neînțeleasă. Se inițiază modul Praznik. inițiez redarea muzicii."
            log("COLEA: " + text_praznik)
            
            asyncio.run(generate_speech(text_praznik, temp_file))
            apply_jarvis_effect(temp_file)

            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

            pygame.mixer.music.unload()
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # Pauza de 2 secunde cerută
            time.sleep(2.0)

            # Deschide Telegram și pornește muzica
            play_telegram_music_silent()

        threading.Thread(target=run_praznik_sequence, daemon=True).start()
        return

    # Pentru orice alt text introdus sau alte comenzi normale
    cleaned = clean_text(user_text)
    words = cleaned.split()
    if words and words[0] in WAKE_WORDS:
        handle_command(user_text)
    else:
        handle_command("colea " + user_text)

def on_key_release(event):
    val = entry_box.get().strip()
    # Execută instantaneu la tastarea cifrelor 1-6 fără a mai fi nevoie de Enter
    if val in ["1", "2", "3", "4", "5", "6"]:
        process_text_input()

entry_box.bind("<KeyRelease>", on_key_release)
entry_box.bind("<Return>", process_text_input)

send_btn = tk.Button(input_frame, text="Trimite", font=("Arial", 10, "bold"), bg="#d0d0d0", command=process_text_input)
send_btn.pack(side="right", padx=5, pady=5)

output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 11))
output.pack(fill="both", expand=True, padx=20, pady=(0, 15))
output.configure(state="disabled")

def log(text):
    def add():
        output.configure(state="normal")
        output.insert(tk.END, text + "\n")
        output.see(tk.END)
        output.configure(state="disabled")
    root.after(0, add)

def set_status(text):
    root.after(0, lambda: status_label.config(text=text))

# -------------------------
# SISTEM VOCAL MASCULIN
# -------------------------

async def generate_speech(text, output_file):
    """Genereaza fisierul audio cu voce masculina folosind Edge TTS."""
    communicate = edge_tts.Communicate(text, VOICE_ROMANIAN_MALE, pitch="-5Hz", rate="+0%")
    await communicate.save(output_file)

def apply_jarvis_effect(file_path):
    """Aplica un ton mai gros si un ecou subtil (daca pydub/ffmpeg sunt disponibile)."""
    try:
        sound = AudioSegment.from_file(file_path)
        
        # Coboram tonalitatea usor pentru un efect mai sobru
        octaves = -0.15
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        sound_low = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        sound_low = sound_low.set_frame_rate(sound.frame_rate)
        
        # Adaugam un ecou sintetic foarte scurt
        echo = sound_low - 14  # volum redus pentru ecou
        sound_jarvis = sound_low.overlay(echo, position=35)
        
        sound_jarvis.export(file_path, format="mp3")
    except Exception:
        # Daca FFmpeg nu este instalat, va ramane vocea masculina curata
        pass

def speak_direct(text):
    def run_speech():
        try:
            # Curățăm riguros textul de orice reziduu accidental "săr" sau "sir"
            cleaned_spoken_text = re.sub(r'\b(săr|sir)\b\.?', '', text, flags=re.IGNORECASE).strip()
            
            log("COLEA: " + cleaned_spoken_text)
            temp_file = "colea_voice.mp3"

            # Rulam apelul asincron pentru generarea vocii curate
            asyncio.run(generate_speech(cleaned_spoken_text, temp_file))
            
            # Aplicam procesarea audio
            apply_jarvis_effect(temp_file)

            # Redam sunetul
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

            pygame.mixer.music.unload()

            if os.path.exists(temp_file):
                os.remove(temp_file)

        except Exception as e:
            print(f"Eroare vorbire COLEA: {e}")

    threading.Thread(target=run_speech, daemon=True).start()

def speak(text):
    speak_direct(text)

# -------------------------
# HELPER CURĂȚARE TEXT & DIACRITICE
# -------------------------

def remove_diacritics(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def clean_text(text):
    text = remove_diacritics(text.lower())
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

# -------------------------
# DICȚIONAR APLICAȚII & PROCESE
# -------------------------

APPS = {
    "word": ["winword", "WINWORD.EXE"],
    "microsoft word": ["winword", "WINWORD.EXE"],
    "powerpoint": ["powerpnt", "POWERPNT.EXE"],
    "power point": ["powerpnt", "POWERPNT.EXE"],
    "viber": ["viber", "Viber.exe"],
    "steam": ["steam://open/main", "steam.exe"],
    "discord": ["discord", "Discord.exe"],
    "counter strike": ["steam://rungameid/730", "cs2.exe"],
    "cs": ["steam://rungameid/730", "cs2.exe"],
    "csgo": ["steam://rungameid/730", "cs2.exe"],
    "fxsound": ["fxsound", "FxSound.exe"],
    "fx sound": ["fxsound", "FxSound.exe"],
    "spotify": ["spotify", "Spotify.exe"],
    "spoti": ["spotify", "Spotify.exe"],
    "notepad": ["notepad.exe", "notepad.exe"],
    "blocnotes": ["notepad.exe", "notepad.exe"],
    "calculator": ["calc.exe", "CalculatorApp.exe"],
    "calc": ["calc.exe", "CalculatorApp.exe"],
    "paint": ["mspaint.exe", "mspaint.exe"],
    "explorer": ["explorer.exe", "explorer.exe"],
    "browser": ["start chrome", "chrome.exe"],
    "chrome": ["start chrome", "chrome.exe"],
    "edge": ["msedge.exe", "msedge.exe"],
    "telegram": ["tg://", "Telegram.exe"]
}

# -------------------------
# DICȚIONAR FOLDERE FRECVENTE
# -------------------------

FOLDERS = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "descarcari": os.path.join(os.path.expanduser("~"), "Downloads"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "ecran": os.path.join(os.path.expanduser("~"), "Desktop"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "documente": os.path.join(os.path.expanduser("~"), "Documents"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "poze": os.path.join(os.path.expanduser("~"), "Pictures"),
    "imagini": os.path.join(os.path.expanduser("~"), "Pictures"),
    "music": os.path.join(os.path.expanduser("~"), "Music"),
    "muzica": os.path.join(os.path.expanduser("~"), "Music"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    "videoclipuri": os.path.join(os.path.expanduser("~"), "Videos")
}

# -------------------------
# FUNCȚII REDARE & CONTROL MUZICĂ
# -------------------------

def kill_telegram():
    """Inchide complet procesul Telegram daca este blocat sau ascuns."""
    subprocess.run("taskkill /f /im Telegram.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_telegram_music():
    speak("Inițiez redarea muzicii.")
    
    screen_w, screen_h = pyautogui.size()
    
    # Cautam ferestrele Telegram existente
    tg_windows = [w for w in gw.getWindowsWithTitle('Telegram') if w.title == 'Telegram']
    
    need_restart = False

    if not tg_windows:
        need_restart = True
    else:
        win = tg_windows[0]
        if win.isMinimized or win.left < 0 or win.top < 0 or win.left >= screen_w or win.top >= screen_h:
            need_restart = True
        else:
            try:
                win.restore()
                win.activate()
                win.maximize()
            except Exception:
                need_restart = True

    if need_restart:
        kill_telegram()
        time.sleep(0.5)
        webbrowser.open("tg://")
        
        time.sleep(3.0)
        
        new_windows = [w for w in gw.getWindowsWithTitle('Telegram') if w.title == 'Telegram']
        if new_windows:
            try:
                new_windows[0].activate()
                new_windows[0].maximize()
            except Exception:
                pass
    
    time.sleep(1.0)
    
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.8)
    pyautogui.write('Sbornik trekov', interval=0.08)
    time.sleep(1.2)
    pyautogui.press('enter')
    time.sleep(1.2)
    
    pyautogui.hotkey('ctrl', 'end')
    time.sleep(0.8)
    
    click_x = int(screen_w * 0.10)
    click_y = int(screen_h * 0.81)
    
    pyautogui.click(click_x, click_y)

def play_telegram_music_silent():
    """Ruleaza muzica pe Telegram fara ca funcția speak să mai zică 'Inițiez redarea muzicii'."""
    screen_w, screen_h = pyautogui.size()
    tg_windows = [w for w in gw.getWindowsWithTitle('Telegram') if w.title == 'Telegram']
    
    need_restart = False

    if not tg_windows:
        need_restart = True
    else:
        win = tg_windows[0]
        if win.isMinimized or win.left < 0 or win.top < 0 or win.left >= screen_w or win.top >= screen_h:
            need_restart = True
        else:
            try:
                win.restore()
                win.activate()
                win.maximize()
            except Exception:
                need_restart = True

    if need_restart:
        kill_telegram()
        time.sleep(0.5)
        webbrowser.open("tg://")
        
        time.sleep(3.0)
        
        new_windows = [w for w in gw.getWindowsWithTitle('Telegram') if w.title == 'Telegram']
        if new_windows:
            try:
                new_windows[0].activate()
                new_windows[0].maximize()
            except Exception:
                pass
    
    time.sleep(1.0)
    
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.8)
    pyautogui.write('Sbornik trekov', interval=0.08)
    time.sleep(1.2)
    pyautogui.press('enter')
    time.sleep(1.2)
    
    pyautogui.hotkey('ctrl', 'end')
    time.sleep(0.8)
    
    click_x = int(screen_w * 0.10)
    click_y = int(screen_h * 0.81)
    
    pyautogui.click(click_x, click_y)

def next_track():
    speak("Trec la următoarea piesă.")
    pyautogui.press('nexttrack')

def prev_track():
    speak("Revin la piesa anterioară.")
    pyautogui.press('prevtrack')

def toggle_play_pause():
    speak("Schimb starea redării.")
    pyautogui.press('playpause')

# -------------------------
# FUNCȚII GLUME CU PAUZE SPECIFICE
# -------------------------

def tell_joke():
    def run_joke():
        try:
            # Partea 1 a glumei
            part1 = "Cum își salută programatorii iubita? Hello, World!"
            log("COLEA: " + part1)
            temp_file1 = "colea_joke1.mp3"
            
            asyncio.run(generate_speech(part1, temp_file1))
            apply_jarvis_effect(temp_file1)
            
            pygame.mixer.music.load(temp_file1)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            if os.path.exists(temp_file1):
                os.remove(temp_file1)

            # Pauza de 2 secunde
            time.sleep(2.0)

            # Partea 2 a glumei
            part2 = "Știu, gluma asta e mai veche decât cablurile USB cu care își încarcă lumea telefoanele, dar promit pe viitor să glumesc mai bine decît Steopa sau Uzun."
            log("COLEA: " + part2)
            temp_file2 = "colea_joke2.mp3"
            
            asyncio.run(generate_speech(part2, temp_file2))
            apply_jarvis_effect(temp_file2)
            
            pygame.mixer.music.load(temp_file2)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            if os.path.exists(temp_file2):
                os.remove(temp_file2)

        except Exception as e:
            print(f"Eroare glumă COLEA: {e}")

    threading.Thread(target=run_joke, daemon=True).start()

def tell_another_joke():
    def run_another_joke():
        try:
            # Partea 1
            part1 = "Gluma despre Dima Andrei."
            log("COLEA: " + part1)
            temp_file1 = "colea_ajoke1.mp3"
            
            asyncio.run(generate_speech(part1, temp_file1))
            apply_jarvis_effect(temp_file1)
            
            pygame.mixer.music.load(temp_file1)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            if os.path.exists(temp_file1):
                os.remove(temp_file1)

            # Pauza de 1 secunda
            time.sleep(1.0)

            # Partea 2
            part2 = "Dima Andrei e atât de rapid, încât și procesorul de la calculatorul meu cere pauză de masă când îl vede pe Andrei cum lucrează."
            log("COLEA: " + part2)
            temp_file2 = "colea_ajoke2.mp3"
            
            asyncio.run(generate_speech(part2, temp_file2))
            apply_jarvis_effect(temp_file2)
            
            pygame.mixer.music.load(temp_file2)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            if os.path.exists(temp_file2):
                os.remove(temp_file2)

        except Exception as e:
            print(f"Eroare altă glumă COLEA: {e}")

    threading.Thread(target=run_another_joke, daemon=True).start()

def introduce_self():
    intro_text = (
        "Salutare! Eu sunt Colea, asistentul tău personal virtual. "
        "Sunt programat în Python și rulez direct pe sistemul tău Windows. "
        "Rolul meu este să-ți fac viața mai ușoară și să te ajut să controlezi calculatorul doar prin comenzi vocale. "
        "Printre altele, pot să deschid sau să închid aplicații, să redau muzică direct din Telegram, "
        "să caut rapid informații pe Google și YouTube, să verific starea procesorului și a memoriei RAM, "
        "să fac capturi de ecran, să aflu prețurile la carburanți la benzinăriile Bemol, "
        "să reglez volumul sau chiar să blochez stația de lucru atunci când ai nevoie de securitate. "
        "Cu ce te pot ajuta astăzi?"
    )
    speak(intro_text)

# -------------------------
# FUNCȚIE PREȚURI BEMOL (CURĂȚARE ZERO-URI INUTILE)
# -------------------------

def check_bemol_prices():
    """Deschide pagina de prețuri Bemol și le citește fără .00 / ,00."""
    url = "https://www.bemol.md/ro/prices"
    log("DESCHIDERE BEMOL: " + url)
    webbrowser.open(url)
    
    def fetch_prices():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                prices_list = []

                # Căutăm rândurile sau blocurile cu date despre carburanți
                rows = soup.select('table tr, .price-row, .prices-item, .fuel-price, div')

                for row in rows:
                    text = row.get_text(separator=' ', strip=True)
                    # Filtrăm liniile relevante care conțin denumiri de combustibil și cifre
                    if any(fuel in text.lower() for fuel in ['euro', 'diesel', 'benzina', 'gpl', '95', '98']) and re.search(r'\d+[\.,]\d+', text):
                        clean_line = re.sub(r'\s+', ' ', text)
                        if clean_line not in prices_list and len(clean_line) < 80:
                            prices_list.append(clean_line)

                # Dacă selectorii generici nu găsesc structura, extragem prin Regex
                if not prices_list:
                    all_text = soup.get_text()
                    matches = re.findall(r'((?:Benzină|Diesel|GPL|Euro\s*95|Euro\s*Diesel)[^0-9\n]+\d+[\.,]\d+)', all_text, re.IGNORECASE)
                    prices_list = [m.strip() for m in matches]

                if prices_list:
                    spoken_text = ". ".join(prices_list[:4])

                    # Elimină .00 și ,00 din text pentru a nu mai pronunța "zero zero"
                    spoken_text = re.sub(r'[\.,]00\b', '', spoken_text)

                    log(f"PRETURI EXTRASE: {spoken_text}")
                    speak(f"Prețurile curente la benzinăria Bemol sunt următoarele: {spoken_text}")
                else:
                    speak("Am deschis pagina Bemol, dar nu am putut citi automat tabelul de prețuri.")
            else:
                speak("Am deschis pagina de prețuri Bemol în browser.")

        except Exception as e:
            log("Eroare la preluare prețuri Bemol: " + str(e))
            speak("Am deschis pagina de prețuri Bemol în browser.")

    threading.Thread(target=fetch_prices, daemon=True).start()

# -------------------------
# FUNCȚII SISTEM
# -------------------------

def take_screenshot():
    speak("Efectuez o captură de ecran.")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    log(f"SCREENSHOT SALVAT: {filename}")

def lock_computer():
    speak("Securizez sistemul și blochez stația de lucru.")
    os.system("rundll32.exe user32.dll,LockWorkStation")

def empty_recycle_bin():
    speak("Golesc coșul de gunoi.")
    ps_cmd = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
    subprocess.run(["powershell", "-c", ps_cmd], shell=True)

def check_system_status():
    cpu_usage = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    ram_free_gb = round(ram.available / (1024 ** 3), 1)

    battery_info = ""
    battery = psutil.sensors_battery()
    if battery:
        plugged = "conectat la sursa de alimentare" if battery.power_plugged else "pe baterie"
        battery_info = f"Nivelul bateriei este la {battery.percent} la sută, {plugged}."
    else:
        battery_info = "Sistemul rulează pe o configurație desktop."

    response = f"Procesorul operează la {cpu_usage} la sută din capacitate. Memoria RAM este utilizată în proporție de {ram_usage} la sută, având {ram_free_gb} gigabaiți disponibili. {battery_info}"
    speak(response)

# -------------------------
# TRADUCĂTOR
# -------------------------

def translate_text(text_to_translate):
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text_to_translate)
        log(f"TRADUCERE ('{text_to_translate}'): {translated}")
        speak(f"Traducerea solicitată este: {translated}")
    except Exception as e:
        log("Eroare traducere: " + str(e))
        speak("A apărut o eroare la traducerea textului.")

# -------------------------
# CONTROL VOLUM DINAMIC & SISTEM
# -------------------------

def adjust_volume(direction, amount=10):
    steps = max(1, int(amount / 2))
    key_code = 175 if direction == "up" else 174
    
    if direction == "up":
        speak(f"Cresc volumul cu {amount} la sută.")
    else:
        speak(f"Reduc volumul cu {amount} la sută.")

    ps_command = f"$w = New-Object -ComObject WScript.Shell; for ($i=0; $i -lt {steps}; $i++) {{ $w.SendKeys([char]{key_code}) }}"
    subprocess.run(["powershell", "-c", ps_command], shell=True)

def volume_mute():
    speak("Dezactivez sunetul.")
    subprocess.run("powershell -c \"(New-Object -ComObject WScript.Shell).SendKeys([char]173)\"", shell=True)

def shutdown_pc():
    speak("Inițiez secvența de oprire a sistemului în 30 de secunde.")
    os.system("shutdown /s /t 30")

def restart_pc():
    speak("Repornesc calculatorul în 30 de secunde.")
    os.system("shutdown /r /t 30")

def cancel_shutdown():
    speak("Secvența de oprire a fost anulată.")
    os.system("shutdown /a")

# -------------------------
# EXECUTARE & ÎNCHIDERE APLICAȚII / FOLDERE
# -------------------------

def open_folder(folder_name):
    folder_name = clean_text(folder_name)
    
    if folder_name in FOLDERS:
        path = FOLDERS[folder_name]
        speak(f"Deschid directorul {folder_name}.")
        os.startfile(path)
        return True
    
    speak(f"Nu am identificat directorul {folder_name}.")
    return False

def open_application(name):
    name = clean_text(name)
    
    if name in FOLDERS:
        return open_folder(name)

    if name in APPS:
        launch_cmd = APPS[name][0]
        speak(f"Lansez aplicația {name}.")
        try:
            if launch_cmd.startswith(("tg://", "steam://")):
                webbrowser.open(launch_cmd)
            else:
                os.system(f"start {launch_cmd}")
            return True
        except Exception:
            speak(f"Nu am putut rula aplicația {name}.")
            return False

    try:
        speak(f"Deschid {name}.")
        os.system(f"start {name}")
        return True
    except Exception:
        speak(f"Aplicația {name} nu a putut fi deschisă.")
        return False

def close_application(name):
    name = clean_text(name)
    process_name = APPS[name][1] if name in APPS else f"{name}.exe"

    try:
        speak(f"Închid procesul {name}.")
        subprocess.run(f"taskkill /f /im {process_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        speak(f"Nu am putut opri procesul {name}.")
        return False

def tell_time():
    current = datetime.now().strftime("%H:%M")
    speak(f"Ora curentă este {current}.")

def weather(city=None):
    if not city:
        city = "Chisinau"
    query = f"vremea in {city}"
    url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    speak(f"Afișez datele meteorologice pentru {city}.")
    webbrowser.open(url)

def google_search(query):
    if not query:
        speak("Ce informații doriți să caut pe Google?")
        return
    url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    log("CĂUTARE GOOGLE: " + query)
    speak(f"Am căutat pe Google: {query}.")
    webbrowser.open(url)

def youtube_search(query):
    if not query:
        speak("Ce doriți să caut pe YouTube?")
        return
    url = "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
    log("CĂUTARE YOUTUBE: " + query)
    speak(f"Caut pe YouTube: {query}.")
    webbrowser.open(url)

# -------------------------
# EXECUTARE CORP COMANDĂ
# -------------------------

def execute_command_body(cmd_body):
    set_status("Procesez comanda...")

    if any(k in cmd_body for k in ["cine esti", "ce poti sa faci", "cu ce ma ajuti", "prezinta te", "prezinta", "ce stii sa faci", "mai multe despre tine", "despre tine"]):
        introduce_self()
        return True

    if any(k in cmd_body for k in ["alta gluma", "zi alta gluma", "spune alta gluma", "alta anecdota", "zi alta anecdota", "gluma despre dima"]):
        tell_another_joke()
        return True

    if any(k in cmd_body for k in ["spune o gluma", "zi o gluma", "spune o anecdota", "zi o anecdota", "razi ceva", "pune o gluma"]):
        tell_joke()
        return True

    if any(k in cmd_body for k in ["preturi bemol", "pret bemol", "benzinaria bemol", "carburant bemol", "combustibil bemol", "cat e benzina la bemol", "preturi carburant"]):
        check_bemol_prices()
        return True

    if any(k in cmd_body for k in ["cum sta sistemul", "stare sistem", "status sistem", "cata memorie avem", "memorie libera", "baterie"]):
        check_system_status()
        return True

    tr_starts = ["tradu ", "traduce ", "tradu in engleza "]
    for start in tr_starts:
        if cmd_body.startswith(start):
            text_to_tr = cmd_body[len(start):].strip()
            text_to_tr = re.sub(r'\s+in\s+engleza$', '', text_to_tr)
            translate_text(text_to_tr)
            return True

    if any(k in cmd_body for k in ["goleste cosul", "goleste gunoiul", "curata cosul", "empty recycle bin"]):
        empty_recycle_bin()
        return True

    yt_starts = ["cauta pe youtube ", "cauta in youtube ", "play pe youtube ", "pune pe youtube "]
    for start in yt_starts:
        if cmd_body.startswith(start):
            query = cmd_body[len(start):].strip()
            youtube_search(query)
            return True

    if any(k in cmd_body for k in ["pune muzica", "play music", "da drumul la muzica", "pune niste muzica"]):
        play_telegram_music()
        return True

    if any(k in cmd_body for k in ["pauza", "pause", "continua", "play", "opreste muzica", "porneste muzica"]):
        toggle_play_pause()
        return True

    if any(k in cmd_body for k in ["urmatoarea", "urmatoarea piesa", "urmatoarea melodie", "schimba muzica", "next"]):
        next_track()
        return True

    if any(k in cmd_body for k in ["precedenta", "inapoi", "piesa anterioara", "melodia anterioara", "previous"]):
        prev_track()
        return True

    if any(k in cmd_body for k in ["screenshot", "fa screenshot", "poaza la ecran", "captura ecran"]):
        take_screenshot()
        return True

    if any(k in cmd_body for k in ["blocheaza pcul", "blocheaza pc", "blocheaza calculatorul", "lock"]):
        lock_computer()
        return True

    if cmd_body in ["esti aici", "esti acolo", "ma auzi"]:
        speak("La ordinul dumneavoastră. Cu ce vă pot ajuta?")
        return True

    if any(k in cmd_body for k in ["cat e ora", "ora", "spune ora"]):
        tell_time()
        return True

    if any(k in cmd_body for k in ["mai tare", "volum sus", "sunet mai tare", "creste volumul"]):
        numbers = re.findall(r'\d+', cmd_body)
        amount = int(numbers[0]) if numbers else 10
        adjust_volume("up", amount)
        return True

    if any(k in cmd_body for k in ["mai incet", "volum jos", "sunet mai incet", "scade volumul"]):
        numbers = re.findall(r'\d+', cmd_body)
        amount = int(numbers[0]) if numbers else 10
        adjust_volume("down", amount)
        return True

    if any(k in cmd_body for k in ["tacere", "fara sunet", "mute"]):
        volume_mute()
        return True

    if any(k in cmd_body for k in ["inchide pcul", "opreste calculatorul", "inchide calculatorul", "opreste pcul", "inchide pc", "opreste pc", "reporneste pc", "reporneste pcul", "restart"]):
        if any(r in cmd_body for r in ["reporneste", "restart"]):
            restart_pc()
        else:
            shutdown_pc()
        return True

    if any(k in cmd_body for k in ["anuleaza inchiderea", "anuleaza restartul", "stop restart", "anularea inchiderea", "anularea", "anulare"]):
        cancel_shutdown()
        return True

    search_starts = ["cauta pe google ", "cauta pe browser ", "cauta pe internet ", "cauta in google ", "cauta "]
    for start in search_starts:
        if cmd_body.startswith(start):
            query = cmd_body[len(start):].strip()
            google_search(query)
            return True

    if "vremea" in cmd_body or "meteo" in cmd_body:
        city = None
        match = re.search(r"(?:in|pentru)\s+(.+)", cmd_body)
        if match:
            city = match.group(1).strip()
        weather(city)
        return True

    folder_triggers = ["deschide folderul ", "deschide folder ", "deschide foderul ", "deschide foder "]
    for trigger in folder_triggers:
        if cmd_body.startswith(trigger):
            folder_name = cmd_body[len(trigger):].strip()
            open_folder(folder_name)
            return True

    close_triggers = ["inchide ", "inchide aplicatia ", "opreste ", "stinge "]
    for trigger in close_triggers:
        if cmd_body.startswith(trigger):
            app_name = cmd_body[len(trigger):].strip()
            close_application(app_name)
            return True

    open_triggers = ["deschide ", "deschide aplicatia ", "porneeste ", "porneste "]
    for trigger in open_triggers:
        if cmd_body.startswith(trigger):
            app_name = cmd_body[len(trigger):].strip()
            open_application(app_name)
            return True

    return False

# -------------------------
# GESTIONARE COMENZI VOCALE
# -------------------------

def handle_command(command, source=None):
    cleaned = clean_text(command)
    
    if not cleaned:
        return

    log("TU: " + command)
    words = cleaned.split()

    if not words:
        set_status("Aștept cuvântul de activare...")
        return

    found_wake = False
    cmd_body = ""

    for idx, word in enumerate(words):
        if word in WAKE_WORDS:
            found_wake = True
            cmd_body = " ".join(words[idx+1:]).strip()
            break

    if not found_wake:
        if "alea" in cleaned or "colea" in cleaned:
            found_wake = True
            parts = re.split(r'\b(colea|alea)\b', cleaned)
            if len(parts) > 2:
                cmd_body = parts[2].strip()

    if not found_wake:
        set_status("Aștept cuvântul «Colea»...")
        return

    if not cmd_body:
        speak("Da")
        set_status("Ascult comanda (5 secunde)...")
        
        if source is not None:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                set_status("Procesez vocea...")
                followup_text = recognizer.recognize_google(audio, language="ro-RO")
                
                cleaned_followup = clean_text(followup_text)
                log("TU (Comandă): " + followup_text)
                
                if cleaned_followup:
                    executed = execute_command_body(cleaned_followup)
                    if not executed:
                        speak("Comanda nu a fost recunoscută în baza de date.")
            except sr.WaitTimeoutError:
                set_status("Timpul a expirat.")
            except sr.UnknownValueError:
                speak("Nu am putut decoda semnalul vocal.")
            except Exception as e:
                log("Eroare la ascultare: " + str(e))
        return

    executed = execute_command_body(cmd_body)
    if not executed:
        if any(w in cmd_body for w in ["prezinta", "esti", "ajuti", "faci"]):
            introduce_self()
        elif any(w in cmd_body for w in ["alta gluma", "dima"]):
            tell_another_joke()
        else:
            speak("Comanda nu este recunoscută.")

# -------------------------
# BUCLĂ ASCULTARE
# -------------------------

def listen_loop():
    global stop_program

    try:
        with sr.Microphone() as source:
            log("SISTEM: Calibrare senzori audio...")
            set_status("Calibrare microfon...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            speak("Sistemele sunt pregătite")
            set_status("Ascult... Spuneți «Colea» sau tastați.")

            while not stop_program:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    set_status("Procesare semnal vocal...")
                    
                    text = recognizer.recognize_google(audio, language="ro-RO")
                    handle_command(text, source=source)
                    
                    set_status("Ascult... Spuneți «Colea» sau tastați.")

                except sr.UnknownValueError:
                    set_status("Aștept comandă...")
                except sr.RequestError:
                    speak("Conexiunea la serviciul de recunoaștere vocală a eșuat.")
                    set_status("Eroare conexiune.")
                    time.sleep(3)
                except Exception as e:
                    log("Eroare microfon: " + str(e))
                    set_status("Eroare microfon.")
                    time.sleep(2)

    except Exception as e:
        log("Microfon indisponibil: " + str(e))
        set_status("Microfon indisponibil.")

def close_program():
    global stop_program
    stop_program = True
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_program)
threading.Thread(target=listen_loop, daemon=True).start()

root.mainloop()