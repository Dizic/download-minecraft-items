import requests
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
import logging
from urllib.parse import unquote
from concurrent.futures import as_completed

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('minecraft_items_download.log'),
        logging.StreamHandler()
    ]
)

# Конфигурация
SAVE_DIR = 'scripts/minecraft_items'
API_BASE_URL = 'https://minecraft.fandom.com/api.php'
ITEMS_PER_REQUEST = 50
MAX_WORKERS = 10
DELAY_BETWEEN_REQUESTS = 1  # секунды
DOWNLOAD_FILES = False  # Флаг для контроля скачивания файлов

def ensure_dir(directory):
    """Создает директорию, если она не существует"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]

def get_item_list():
    """Получает список предметов из Minecraft Wiki API"""
    items = []
    continue_token = None
    
    while True:
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': 'Category:Items',
            'cmlimit': ITEMS_PER_REQUEST,
            'cmtype': 'page'
        }
        
        if continue_token:
            params['cmcontinue'] = continue_token
            
        try:
            response = requests.get(API_BASE_URL, params=params)
            data = response.json()
 
            if 'query' in data and 'categorymembers' in data['query']:
                items.extend(data['query']['categorymembers'])
                
            if 'continue' in data and 'cmcontinue' in data['continue']:
                continue_token = data['continue']['cmcontinue']
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                break
                
        except Exception as e:
            logging.error(f"Ошибка при получении списка предметов: {e}")
            break
            
    return items

def get_item_image(item):
    """Получает URL изображения предмета"""
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'images',
        'titles': item['title']
    }
    
    try:
        response = requests.get(API_BASE_URL, params=params)
        data = response.json()
        
        pages = data['query']['pages']
        for page_id in pages:
            page = pages[page_id]
            if 'images' in page:
                for image in page['images']:
                    if 'png' in image['title'].lower() or 'gif' in image['title'].lower():
                        return image['title']
    except Exception as e:
        logging.error(f"Ошибка при получении изображения для {item['title']}: {e}")
        
    return None

def get_image_url(image_title):
    """Получает прямую ссылку на изображение"""
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'imageinfo',
        'iiprop': 'url',
        'titles': image_title
    }
    
    try:
        response = requests.get(API_BASE_URL, params=params)
        data = response.json()
        
        pages = data['query']['pages']
        for page_id in pages:
            page = pages[page_id]
            if 'imageinfo' in page:
                return page['imageinfo'][0]['url']
    except Exception as e:
        logging.error(f"Ошибка при получении URL изображения для {image_title}: {e}")
        
    return None

def download_image(url, filename):
    """Скачивает изображение по URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        logging.info(f"Скачано: {filename}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при скачивании {url}: {e}")
        return False

def process_item(item, download_files=True):
    """Обрабатывает один предмет и возвращает информацию о нем"""
    image_title = get_item_image(item)
    item_info = {
        'name': item['title'],
        'imageUrl': None,
        'localPath': None
    }
    
    if image_title:
        image_url = get_image_url(image_title)
        if image_url:
            item_info['imageUrl'] = image_url
            
            if download_files:
                filename = sanitize_filename(f"{item['title']}_{os.path.basename(unquote(image_url))}")
                filepath = os.path.join(SAVE_DIR, filename)
                item_info['localPath'] = filepath
                
                if download_image(image_url, filepath):
                    return True, item_info
            else:
                # Если скачивание отключено, localPath остается None
                return True, item_info
    
    return False, item_info

def save_items_json(items_info):
    """Сохраняет информацию о предметах в JSON файл"""
    json_path = os.path.join(os.path.dirname(SAVE_DIR), 'minecraft_items.json')
    
    # Фильтруем только успешно скачанные предметы
    successful_items = [item for item in items_info if item['imageUrl'] is not None]
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(successful_items, f, indent=2, ensure_ascii=False)
        logging.info(f"Информация о предметах сохранена в {json_path}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении JSON: {e}")

def main(download_files=DOWNLOAD_FILES):
    """Основная функция"""
    if download_files:
        ensure_dir(SAVE_DIR)
    
    logging.info("Получение списка предметов...")
    items = get_item_list()
    total_items = len(items)
    logging.info(f"Найдено предметов: {total_items}")
    
    successful_downloads = 0
    failed_downloads = 0
    items_info = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Запускаем задачи и получаем результаты
        future_to_item = {
            executor.submit(process_item, item, download_files): item 
            for item in items
        }
        
        for future in as_completed(future_to_item):
            success, item_info = future.result()
            items_info.append(item_info)
            
            if success:
                successful_downloads += 1
                if download_files:
                    logging.info(f"Обработан предмет: {item_info['name']}")
                else:
                    logging.info(f"Получена информация о предмете: {item_info['name']}")
            else:
                failed_downloads += 1
                logging.warning(f"Не удалось обработать предмет: {future_to_item[future]['title']}")
    
    # Сохраняем информацию в JSON
    save_items_json(items_info)
    
    logging.info(f"\nИтоги:")
    logging.info(f"Всего предметов: {total_items}")
    if download_files:
        logging.info(f"Успешно скачано: {successful_downloads}")
    else:
        logging.info(f"Успешно обработано: {successful_downloads}")
    logging.info(f"Не удалось обработать: {failed_downloads}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Скачивание изображений предметов Minecraft')
    parser.add_argument('--download', action='store_true', 
                       help='Скачивать файлы (по умолчанию только собирает информацию)')
    
    args = parser.parse_args()
    main(download_files=args.download) 
