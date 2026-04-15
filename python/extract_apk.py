import subprocess
import os
import sys
import shutil

def find_apk_file(directory):
    """Находит первый .apk файл в указанной директории."""
    if os.path.exists(directory):
        for f in os.listdir(directory):
            if f.lower().endswith(".apk"):
                return os.path.join(directory, f)
    return None


# Пути к директориям
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK_DIR = os.path.join(BASE_DIR, "apk_original")
APK_INPUT = find_apk_file(APK_DIR)
if APK_INPUT is None:
    print(f"Ошибка: в папке apk_original не найден ни один .apk файл")
    sys.exit(1)
OUTPUT_7Z = os.path.join(BASE_DIR, "7zip_apk")
DEX_OUTPUT = os.path.join(BASE_DIR, "dex_original")
SMALI_OUTPUT = os.path.join(BASE_DIR, "small")
JAVA_OUTPUT = os.path.join(BASE_DIR, "java")

# Путь к 7zip
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"

# Пути к инструментам
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
BAKSMALI_JAR = os.path.join(TOOLS_DIR, "baksmali.jar")
JADX_DIR = os.path.join(TOOLS_DIR, "jadx-1.5.5", "bin")
JADX_BAT = os.path.join(JADX_DIR, "jadx.bat")


def extract_apk():
    """Распаковывает APK файл в директорию 7zip_apk с помощью 7zip."""
    
    # Проверяем есть ли файлы в папке
    if os.path.exists(OUTPUT_7Z) and os.listdir(OUTPUT_7Z):
        print(f"\n[1/4] Пропуск: 7zip_apk уже содержит файлы")
        return True
    
    # Проверяем наличие 7zip
    if not os.path.exists(SEVEN_ZIP):
        print(f"Ошибка: 7zip не найден по пути - {SEVEN_ZIP}")
        sys.exit(1)
    
    # Проверяем существование входного файла
    if not os.path.exists(APK_INPUT):
        print(f"Ошибка: файл не найден - {APK_INPUT}")
        sys.exit(1)
    
    # Создаём выходную директорию если нет
    os.makedirs(OUTPUT_7Z, exist_ok=True)
    
    print(f"\n[1/4] Распаковка: {APK_INPUT}")
    print(f"      В директорию: {OUTPUT_7Z}")
    
    # Команда 7zip для распаковки
    cmd = [SEVEN_ZIP, "x", APK_INPUT, f"-o{OUTPUT_7Z}", "-y"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("      Распаковка завершена успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"      Ошибка при распаковке:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Ошибка: не удалось запустить 7zip - {SEVEN_ZIP}")
        sys.exit(1)


def copy_dex_files():
    """Копирует все .dex файлы из 7zip_apk в dex_original."""
    
    # Проверяем есть ли файлы в папке
    if os.path.exists(DEX_OUTPUT) and os.listdir(DEX_OUTPUT):
        print(f"\n[2/4] Пропуск: dex_original уже содержит файлы")
        return
    
    print(f"\n[2/4] Копирование .dex файлов:")
    print(f"      Из: {OUTPUT_7Z}")
    print(f"      В:  {DEX_OUTPUT}")
    
    os.makedirs(DEX_OUTPUT, exist_ok=True)
    
    dex_files = [f for f in os.listdir(OUTPUT_7Z) if f.endswith(".dex")]
    
    if not dex_files:
        print("      Ошибка: .dex файлы не найдены!")
        sys.exit(1)
    
    for dex_file in dex_files:
        src = os.path.join(OUTPUT_7Z, dex_file)
        dst = os.path.join(DEX_OUTPUT, dex_file)
        shutil.copy2(src, dst)
        print(f"      Скопирован: {dex_file}")
    
    print(f"      Скопировано файлов: {len(dex_files)}")


def disassemble_to_smali():
    """Декомпиляция .dex в smali-код с помощью baksmali.jar."""
    
    # Проверяем есть ли файлы в папке
    if os.path.exists(SMALI_OUTPUT) and os.listdir(SMALI_OUTPUT):
        print(f"\n[3/4] Пропуск: small уже содержит файлы")
        return
    
    print(f"\n[3/4] Декомпиляция в smali-код:")
    print(f"      Инструмент: {BAKSMALI_JAR}")
    print(f"      Вывод в:    {SMALI_OUTPUT}")
    
    # Проверяем наличие baksmali.jar
    if not os.path.exists(BAKSMALI_JAR):
        print(f"      Ошибка: baksmali.jar не найден - {BAKSMALI_JAR}")
        sys.exit(1)
    
    # Создаём папки для каждого .dex файла
    dex_files = [f for f in os.listdir(DEX_OUTPUT) if f.endswith(".dex")]
    
    for dex_file in dex_files:
        dex_path = os.path.join(DEX_OUTPUT, dex_file)
        # Имя папки без расширения (classes -> classes)
        folder_name = os.path.splitext(dex_file)[0]
        output_path = os.path.join(SMALI_OUTPUT, folder_name)
        os.makedirs(output_path, exist_ok=True)
        
        print(f"      Обработка: {dex_file}")
        
        cmd = ["java", "-jar", BAKSMALI_JAR, "d", dex_path, "-o", output_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"      Готово: {folder_name}/")
        except subprocess.CalledProcessError as e:
            print(f"      Ошибка при декомпиляции {dex_file}:\n{e.stderr}")
            sys.exit(1)


def disassemble_to_java():
    """Декомпиляция .dex в Java-код с помощью jadx."""
    
    # Проверяем есть ли файлы в папке
    if os.path.exists(JAVA_OUTPUT) and os.listdir(JAVA_OUTPUT):
        print(f"\n[4/4] Пропуск: java уже содержит файлы")
        return
    
    print(f"\n[4/4] Декомпиляция в Java-код:")
    print(f"      Инструмент: {JADX_BAT}")
    print(f"      Вывод в:    {JAVA_OUTPUT}")
    
    # Проверяем наличие jadx.bat
    if not os.path.exists(JADX_BAT):
        print(f"      Ошибка: jadx.bat не найден - {JADX_BAT}")
        sys.exit(1)
    
    # Создаём папки для каждого .dex файла
    dex_files = [f for f in os.listdir(DEX_OUTPUT) if f.endswith(".dex")]
    
    for dex_file in dex_files:
        dex_path = os.path.join(DEX_OUTPUT, dex_file)
        # Имя папки без расширения (classes -> classes)
        folder_name = os.path.splitext(dex_file)[0]
        output_path = os.path.join(JAVA_OUTPUT, folder_name)
        os.makedirs(output_path, exist_ok=True)
        
        print(f"      Обработка: {dex_file}")
        
        cmd = f'jadx.bat -d "{output_path}" "{dex_path}"'
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=JADX_DIR)
            # Выводим логи
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    print(f"        {line}")
            print(f"      Готово: {folder_name}/")
        except Exception as e:
            print(f"      Ошибка при декомпиляции {dex_file}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    extract_apk()
    copy_dex_files()
    disassemble_to_smali()
    disassemble_to_java()
    print("\nВсе этапы завершены!")
