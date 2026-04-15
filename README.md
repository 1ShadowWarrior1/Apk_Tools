# APK Modding Toolkit

Набор Python-скриптов для распаковки, модификации и обратной сборки APK.

## Структура

```
apk-small/
├── apk_original/      # Исходный APK (base.apk)
├── 7zip_apk/          # Распакованный APK
├── dex_original/      # Оригинальные .dex файлы
├── small/             # Smali-код
├── java/              # Java-код (через JADX)
├── python/            # Скрипты
│   ├── extract_apk.py    # Распаковка + декомпиляция
│   ├── assemble_dex.py   # Сборка .dex из smali
│   └── build_apk.py      # Упаковка + подпись
└── tools/             # Инструменты (apktool, 7zip, jadx, build-tools)
```

## Быстрый старт

### 1. Распаковка
```
1_extract.bat
```
- Распаковывает APK
- Копирует `.dex` файлы
- Декомпилирует в smali и Java

### 2. Сборка .dex
```
2_assemble.bat
```
- Выбираешь какие `.dex` собрать (или все)
- Собирает из smali-кода

### 3. Упаковка и подпись
```
3_build.bat
```
- Упаковывает в ZIP без сжатия
- Выравнивает (zipalign)
- Подписывает (apksigner)

## Требования

- Python 3
- Java
- 7-Zip (установлен в `C:\Program Files\7-Zip`)

## Инструменты

| Инструмент | Назначение |
|---|---|
| 7-Zip | Распаковка/упаковка APK |
| baksmali | Декомпиляция .dex в smali |
| smali | Сборка .dex из smali |
| JADX | Декомпиляция .dex в Java |
| zipalign | Выравнивание APK |
| apksigner | Подпись APK |

## Настройка подписи

В `python/build_apk.py` измени пароль keystore:
```python
--ks-pass pass:123456
```
