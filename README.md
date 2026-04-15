# APK Modding Toolkit

Набор Python-скриптов для распаковки, модификации, обратной сборки APK и установки на устройство через WiFi.

## Структура

```
apk-small/
├── apk_original/      # Исходный APK (base.apk)
├── 7zip_apk/          # Распакованный APK
├── dex_original/      # Оригинальные .dex файлы
├── small/             # Smali-код
├── java/              # Java-код (через JADX)
├── python/            # Скрипты
│   ├── extract_apk.py     # Распаковка + декомпиляция
│   ├── assemble_dex.py    # Сборка .dex из smali
│   ├── build_apk.py       # Упаковка + подпись
│   └── install_wifi.py    # ADB WiFi: сопряжение и установка APK
└── tools/             # Инструменты (adb, apktool, 7zip, jadx, build-tools)
```

## Быстрый старт

### 1. Распаковка
```
1_extract.bat
```
- Распаковывает APK с помощью 7-Zip
- Копирует `.dex` файлы в `dex_original/`
- Декомпилирует в smali-код (baksmali)
- Декомпилирует в Java-код (JADX)

### 2. Сборка .dex
```
2_assemble.bat
```
- Интерактивный выбор: какие `.dex` собрать (или все)
- Собирает из smali-кода с помощью smali.jar

### 3. Упаковка и подпись
```
3_build.bat
```
- Упаковывает в ZIP без сжатия
- Выравнивает (zipalign)
- Подписывает (apksigner) с использованием keystore

### 4. Установка через WiFi
```
4_install_wifi.bat
```
- Сопряжение с устройством по коду (Android 11+ Wireless Debugging)
- Подключение через ADB over WiFi
- Установка подписанного APK на устройство
- Управление подключёнными устройствами

## Требования

- Python 3
- Java
- 7-Zip (установлен в `C:\Program Files\7-Zip`)
- Включённый Wireless Debugging на Android-устройстве (для шага 4)

## Инструменты

| Инструмент | Назначение |
|---|---|
| 7-Zip | Распаковка/упаковка APK |
| baksmali | Декомпиляция .dex в smali |
| smali | Сборка .dex из smali |
| JADX | Декомпиляция .dex в Java |
| zipalign | Выравнивание APK |
| apksigner | Подпись APK |
| ADB | Установка APK через WiFi |

## Настройка подписи

В `python/build_apk.py` измени пароль keystore:
```python
--ks-pass pass:testtest
```

Также можно заменить keystore в `tools/my-release-key.keystore` на свой.
