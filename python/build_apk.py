import subprocess
import os
import sys
import shutil

# Пути к директориям
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "7zip_apk")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
BUILD_TOOLS = os.path.join(TOOLS_DIR, "build-tools")
KEYSTORE = os.path.join(TOOLS_DIR, "my-release-key.keystore")

# Инструменты
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
ZIPALIGN = os.path.join(BUILD_TOOLS, "zipalign.exe")
APKSIGNER = os.path.join(BUILD_TOOLS, "apksigner.bat")
APKSIGNER_DIR = BUILD_TOOLS

# Временные файлы
TEMP_ZIP = os.path.join(BASE_DIR, "temp_unsigned.apk")
FINAL_APK = os.path.join(BASE_DIR, "app_signed.apk")


def pack_to_zip():
    """Упаковывает содержимое 7zip_apk в ZIP без сжатия."""

    if not os.path.exists(INPUT_DIR) or not os.listdir(INPUT_DIR):
        print("Ошибка: папка 7zip_apk пуста или не существует!")
        sys.exit(1)

    if not os.path.exists(SEVEN_ZIP):
        print(f"Ошибка: 7zip не найден - {SEVEN_ZIP}")
        sys.exit(1)

    # Удаляем старый файл если есть
    if os.path.exists(TEMP_ZIP):
        os.remove(TEMP_ZIP)

    print(f"[1/3] Упаковка в ZIP (без сжатия):")
    print(f"      Из: {INPUT_DIR}")
    print(f"      В:  {TEMP_ZIP}")

    # -mx0 = без сжатия
    cmd = [SEVEN_ZIP, "a", "-tzip", "-mx=0", TEMP_ZIP, os.path.join(INPUT_DIR, "*")]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("      Упаковка завершена!")
    except subprocess.CalledProcessError as e:
        print(f"      Ошибка при упаковке:\n{e.stderr}")
        sys.exit(1)


def align_apk():
    """Выравнивает APK через zipalign."""

    temp_aligned = os.path.join(BASE_DIR, "temp_aligned.apk")

    if not os.path.exists(ZIPALIGN):
        print(f"Ошибка: zipalign.exe не найден - {ZIPALIGN}")
        sys.exit(1)

    # Переименовываем .zip в .apk
    if os.path.exists(temp_aligned):
        os.remove(temp_aligned)

    shutil.move(TEMP_ZIP, temp_aligned)

    print(f"\n[2/3] Выравнивание (zipalign):")
    print(f"      Вход:  {temp_aligned}")
    print(f"      Выход: {TEMP_ZIP}")

    cmd = [ZIPALIGN, "-p", "-v", "4", temp_aligned, TEMP_ZIP]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Выводим результат zipalign
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line:
                print(f"        {line}")
        # Удаляем неотфайловый файл
        if os.path.exists(temp_aligned):
            os.remove(temp_aligned)
        print("      Выравнивание завершено!")
    except subprocess.CalledProcessError as e:
        print(f"      Ошибка при выравнивании:\n{e.stderr}")
        if os.path.exists(temp_aligned):
            os.remove(temp_aligned)
        sys.exit(1)


def sign_apk():
    """Подписывает APK через apksigner."""

    if not os.path.exists(APKSIGNER):
        print(f"Ошибка: apksigner.bat не найден - {APKSIGNER}")
        sys.exit(1)

    if not os.path.exists(KEYSTORE):
        print(f"Ошибка: keystore не найден - {KEYSTORE}")
        sys.exit(1)

    print(f"\n[3/3] Подписание (apksigner):")
    print(f"      Вход:  {TEMP_ZIP}")
    print(f"      Выход: {FINAL_APK}")

    # Пароль keystore по умолчанию
    cmd = (
        f'cmd /c "cd /d "{BUILD_TOOLS}" && apksigner.bat sign '
        f'--ks "{KEYSTORE}" '
        f'--ks-pass pass:testtest '
        f'--out "{FINAL_APK}" '
        f'"{TEMP_ZIP}"'
        f'"'
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        # Выводим логи
        output = result.stdout + result.stderr
        for line in output.strip().split('\n'):
            line = line.strip()
            if line:
                print(f"        {line}")

        # Проверяем что файл создан
        if os.path.exists(FINAL_APK):
            size = os.path.getsize(FINAL_APK)
            print(f"\n      Подписано! Размер: {size:,} байт")
            print(f"      Файл: {FINAL_APK}")
        else:
            print("      Ошибка: подписанный файл не создан!")
            sys.exit(1)

    except Exception as e:
        print(f"      Ошибка при подписании: {e}")
        sys.exit(1)


def cleanup():
    """Удаляет временные файлы."""
    for f in [TEMP_ZIP]:
        if os.path.exists(f):
            os.remove(f)
            print(f"\n      Удалён временный файл: {os.path.basename(f)}")

    # Удаляем .idsig если есть
    idsig = FINAL_APK + ".idsig"
    if os.path.exists(idsig):
        os.remove(idsig)
        print(f"      Удалён: {os.path.basename(idsig)}")


def main():
    print("=" * 60)
    print("Сборка APK: упаковка → выравнивание → подпись")
    print("=" * 60)

    pack_to_zip()
    align_apk()
    sign_apk()
    cleanup()

    print("\n" + "=" * 60)
    print("Готово! Подписанный APK:")
    print(f"  {FINAL_APK}")
    print("=" * 60)


if __name__ == "__main__":
    main()
