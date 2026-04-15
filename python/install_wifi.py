import subprocess
import os
import sys
import socket
import ipaddress
import threading
import time

# Пути к директориям
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_EXE = os.path.join(BASE_DIR, "tools", "adb", "adb.exe")
APK_DIR = os.path.join(BASE_DIR, "apk_original")


def find_apk_file(directory):
    """Находит первый .apk файл в указанной директории."""
    if os.path.exists(directory):
        for f in os.listdir(directory):
            if f.lower().endswith(".apk"):
                return os.path.join(directory, f)
    return None


def run_cmd(cmd, timeout=15):
    """Выполняет команду и возвращает (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, shell=True
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1


def get_local_subnet():
    """Определяет локальную подсеть (например, 192.168.1.0/24)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Берём /24 подсеть
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return network, local_ip
    except Exception as e:
        print(f"Ошибка определения подсети: {e}")
        return None, None


def scan_port(ip, port=5555, timeout=1):
    """Проверяет открыт ли порт на указанном IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except:
        return False


def scan_network_for_adb():
    """Сканирует локальную сеть на наличие устройств с ADB over WiFi."""
    network, local_ip = get_local_subnet()
    if network is None:
        print("Не удалось определить локальную сеть")
        return []

    print(f"\nСканирование сети: {network}")
    print(f"Ваш IP: {local_ip}")
    print(f"Порты для проверки: 5555, 4000, 5000\n")

    found_devices = []
    ports_to_check = [5555, 4000, 5000]

    def check_host(ip):
        for port in ports_to_check:
            if scan_port(ip, port, timeout=1):
                found_devices.append(f"{ip}:{port}")
                break

    threads = []
    for host in network.hosts():
        ip = str(host)
        if ip == local_ip:
            continue
        t = threading.Thread(target=check_host, args=(ip,))
        t.daemon = True
        threads.append(t)
        t.start()
        # Ограничиваем кол-во одновременных потоков
        if len(threads) >= 50:
            for t in threads:
                t.join(timeout=2)
            threads = []
        # Прогресс
        if int(ip.split('.')[-1]) % 50 == 0:
            print(f"  Проверено ~{int(ip.split('.')[-1])}/254 хостов...", end='\r')

    # Ждём оставшиеся потоки
    for t in threads:
        t.join(timeout=2)

    print(f"\nСканирование завершено!")
    return found_devices


def try_mdns_discovery():
    """Пробует обнаружить устройства через mDNS (новый ADB)."""
    print("\nПоиск устройств через mDNS...")
    stdout, stderr, code = run_cmd(f'"{ADB_EXE}" mdns services')
    if code == 0 and stdout.strip():
        devices = []
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('List of devices'):
                # Формат: host:port   device_type   name
                parts = line.split()
                if parts:
                    devices.append(parts[0])
        if devices:
            print(f"Найдено через mDNS: {', '.join(devices)}")
            return devices
    return []


def list_connected_devices():
    """Возвращает список подключённых устройств."""
    stdout, stderr, code = run_cmd(f'"{ADB_EXE}" devices')
    devices = []
    if code == 0:
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('List of devices'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    devices.append(parts[0])
    return devices


def pair_and_connect(host=None, pair_port=None, pairing_code=None, connect_port=None):
    """Сопряжение через код (Android 11+ Wireless Debugging), затем подключение."""
    if host is None:
        host = input("  IP-адрес устройства: ").strip()
    if pair_port is None:
        pair_port = input("  Порт сопряжения: ").strip()
    if pairing_code is None:
        pairing_code = input("  Код сопряжения: ").strip()
    if connect_port is None:
        connect_port = input("  Порт подключения: ").strip()

    if not (host and pair_port and pairing_code and connect_port):
        print("  Все поля обязательны!")
        return False

    pair_address = f"{host}:{pair_port}"
    connect_address = f"{host}:{connect_port}"

    print(f"\n  Сопряжение с {pair_address}...")
    stdout, stderr, code = run_cmd(
        f'"{ADB_EXE}" pair {pair_address} {pairing_code}', timeout=30
    )
    output = (stdout + stderr).strip()
    for line in output.split('\n'):
        line = line.strip()
        if line:
            print(f"  {line}")

    if code != 0 and "successfully" not in output.lower() and "paired" not in output.lower():
        print("  Ошибка сопряжения!")
        return False

    print("  Сопряжение успешно!")
    print(f"\n  Подключение к {connect_address}...")
    return connect_to_device(connect_address)


def connect_to_device(address):
    """Подключается к устройству по указанному адресу."""
    print(f"\nПодключение к {address}...")
    stdout, stderr, code = run_cmd(f'"{ADB_EXE}" connect {address}')
    output = (stdout + stderr).strip()
    print(f"  {output}")
    return code == 0 or "connected" in output.lower() or "already connected" in output.lower()


def disconnect_all():
    """Отключает все WiFi устройства."""
    print("\nОтключение всех устройств...")
    run_cmd(f'"{ADB_EXE}" disconnect')


def install_apk(device_serial=None):
    """Устанавливает подписанный APK на устройство."""
    # Сначала ищем подписанный APK
    SIGNED_APK = os.path.join(BASE_DIR, "app_signed.apk")
    if os.path.exists(SIGNED_APK):
        apk_path = SIGNED_APK
    else:
        apk_path = find_apk_file(APK_DIR)

    if apk_path is None:
        print(f"Ошибка: не найден APK файл")
        print(f"  Ожидаемый путь: {SIGNED_APK}")
        print(f"  Или поместите APK в: {APK_DIR}")
        return False

    apk_filename = os.path.basename(apk_path)
    print(f"\nУстановка APK: {apk_filename}")

    cmd = f'"{ADB_EXE}"'
    if device_serial:
        cmd += f' -s {device_serial}'
    cmd += f' install -r "{apk_path}"'

    print(f"Устройство: {device_serial or 'по умолчанию'}")
    stdout, stderr, code = run_cmd(cmd, timeout=120)
    output = (stdout + stderr).strip()

    for line in output.split('\n'):
        line = line.strip()
        if line:
            print(f"  {line}")

    return code == 0 and "success" in output.lower()


def interactive_menu():
    """Интерактивное меню."""
    print("=" * 60)
    print("ADB WiFi — Сопряжение и установка APK")
    print("=" * 60)

    while True:
        print("\nМеню:")
        print("  1. Сопряжение через код (Android 11+ Wireless Debugging)")
        print("  2. Показать подключённые устройства")
        print("  3. Установить APK на устройство")
        print("  4. Отключить все устройства")
        print("  5. Выйти")

        choice = input("\nВыбор [1-5]: ").strip()

        if choice == '1':
            print("\n[1] Сопряжение через код...")
            print("  Включите Wireless Debugging на устройстве")
            print("  Выберите 'Сопряжение по коду'")
            pair_and_connect()

        elif choice == '2':
            devices = list_connected_devices()
            if devices:
                print(f"\nПодключённые устройства ({len(devices)}):")
                for dev in devices:
                    print(f"  • {dev}")
            else:
                print("\nНет подключённых устройств.")

        elif choice == '3':
            devices = list_connected_devices()
            if not devices:
                print("\nНет подключённых устройств!")
                continue

            print("\nДоступные устройства:")
            for i, dev in enumerate(devices, 1):
                print(f"  {i}. {dev}")

            dev_choice = input("\nВыберите устройство (номер): ").strip()
            if dev_choice.isdigit():
                idx = int(dev_choice) - 1
                if 0 <= idx < len(devices):
                    install_apk(devices[idx])
                else:
                    print("Неверный номер!")
            else:
                print("Неверный ввод!")

        elif choice == '4':
            disconnect_all()

        elif choice == '5':
            print("\nВыход. До свидания!")
            break

        else:
            print("Неверный выбор!")


def main():
    # Проверяем наличие ADB
    if not os.path.exists(ADB_EXE):
        print(f"Ошибка: adb.exe не найден - {ADB_EXE}")
        sys.exit(1)

    # Проверяем наличие подписанного APK
    signed_apk = os.path.join(BASE_DIR, "app_signed.apk")
    if not os.path.exists(signed_apk):
        print(f"Предупреждение: подписанный APK не найден")
        print(f"  Сначала запустите: 3_build.bat")
        print(f"  Ожидаемый путь: {signed_apk}\n")

    interactive_menu()


if __name__ == "__main__":
    main()
