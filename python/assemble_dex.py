import subprocess
import os
import sys

# Пути к директориям
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMALI_INPUT = os.path.join(BASE_DIR, "small")

# Пути к инструментам
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
SMALI_JAR = os.path.join(TOOLS_DIR, "smali.jar")


def get_available_smali_dirs():
    """Возвращает список папок с smali-кодом."""
    if not os.path.exists(SMALI_INPUT):
        return []
    return [d for d in os.listdir(SMALI_INPUT)
            if os.path.isdir(os.path.join(SMALI_INPUT, d))]


def assemble_dex(target_dirs):
    """Собирает .dex файлы из smali-кода."""

    # Проверяем наличие smali.jar
    if not os.path.exists(SMALI_JAR):
        print(f"Ошибка: smali.jar не найден - {SMALI_JAR}")
        sys.exit(1)

    os.makedirs(BASE_DIR, exist_ok=True)

    for dir_name in target_dirs:
        smali_path = os.path.join(SMALI_INPUT, dir_name)
        output_dex = os.path.join(BASE_DIR, f"{dir_name}.dex")

        if not os.path.exists(smali_path):
            print(f"  Пропуск: папка '{dir_name}' не найдена в small/")
            continue

        print(f"\n  Сборка: {dir_name}/ -> {dir_name}.dex")

        cmd = ["java", "-jar", SMALI_JAR, "assemble", smali_path, "-o", output_dex]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  Готово: {dir_name}.dex")
        except subprocess.CalledProcessError as e:
            print(f"  Ошибка при сборке {dir_name}:\n{e.stderr}")
            continue


def main():
    available = get_available_smali_dirs()

    if not available:
        print(f"Ошибка: в папке 'small/' нет папок с smali-кодом!")
        print(f"Ожидаемая структура: small/classes/, small/classes2/, ...")
        sys.exit(1)

    print(f"Доступные папки с smali-кодом:")
    for i, d in enumerate(available, 1):
        print(f"  {i}. {d}")

    print(f"\nВведите номера или имена папок для сборки:")
    print(f"  - через запятую: 1,3,5 или classes,classes2")
    print(f"  - 'all' для сборки всех\n")

    user_input = input("Выбор > ").strip().lower()

    if not user_input:
        print("Ничего не введено. Выход.")
        sys.exit(1)

    if user_input == "all":
        target_dirs = available
    else:
        items = [x.strip() for x in user_input.split(",")]
        target_dirs = []
        for item in items:
            # Если это число — берём по индексу
            if item.isdigit():
                idx = int(item) - 1
                if 0 <= idx < len(available):
                    target_dirs.append(available[idx])
                else:
                    print(f"  Неверный номер: {item}")
            else:
                # Если это имя папки
                if item in available:
                    target_dirs.append(item)
                else:
                    print(f"  Папка не найдена: {item}")

    if not target_dirs:
        print("Нет папок для сборки. Выход.")
        sys.exit(1)

    print(f"\nБудут собраны: {', '.join(target_dirs)}")
    assemble_dex(target_dirs)
    print(f"\nСборка завершена! .dex файлы в корне проекта: {BASE_DIR}")


if __name__ == "__main__":
    main()
