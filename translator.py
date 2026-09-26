"""
Перевод EN -> RU через argos-translate. Пакет EN->RU скачивается и
устанавливается одной функцией, без ручной конвертации моделей.
"""
import argostranslate.package
import argostranslate.translate


def ensure_en_ru_installed():
    installed_languages = argostranslate.translate.get_installed_languages()
    installed_codes = {lang.code for lang in installed_languages}

    if "en" in installed_codes and "ru" in installed_codes:
        en_lang = next(l for l in installed_languages if l.code == "en")
        if any(t.to_lang.code == "ru" for t in en_lang.translations_from):
            return  # пакет уже стоит

    print("Скачиваю языковой пакет EN -> RU (один раз, дальше работает офлайн)...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package = next(
        p for p in available_packages if p.from_code == "en" and p.to_code == "ru"
    )
    argostranslate.package.install_from_path(package.download())
    print("Пакет EN -> RU установлен.")


def translate_en_to_ru(text: str) -> str:
    if not text:
        return ""
    return argostranslate.translate.translate(text, "en", "ru")