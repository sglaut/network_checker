import requests
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple

# Настройка логирования
def setup_logging():
    # Создаем директорию для логов если её нет
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/internet_check.log'),
            logging.StreamHandler()
        ]
    )

class InternetChecker:
    def __init__(self, telegram_bot_token: str = None, check_interval: int = 60):
        """
        Инициализация проверяльщика интернета
        
        :param telegram_bot_token: Токен Telegram бота (опционально)
        :param check_interval: Интервал проверки в секундах
        """
        self.check_interval = check_interval
        self.telegram_bot_token = telegram_bot_token
        self.timeout = 10  # Таймаут для запросов в секундах
        
        # URL для проверки
        self.urls = {
            'google': 'https://www.google.com',
            'yandex': 'https://ya.ru',
            'telegram': f'https://api.telegram.org/bot{telegram_bot_token}/getMe' if telegram_bot_token else None
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_url(self, url: str, name: str) -> Tuple[bool, str]:
        """
        Проверяет доступность URL
        
        :param url: URL для проверки
        :param name: Название сервиса
        :return: Кортеж (успешность, сообщение об ошибке)
        """
        if not url:
            return False, "URL не настроен"
            
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return True, "Успешно"
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Таймаут"
        except requests.exceptions.ConnectionError:
            return False, "Ошибка соединения"
        except requests.exceptions.RequestException as e:
            return False, f"Ошибка запроса: {str(e)}"
        except Exception as e:
            return False, f"Неожиданная ошибка: {str(e)}"

    def check_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """
        Проверяет все сервисы
        
        :return: Словарь с результатами проверки
        """
        results = {}
        
        # Проверяем Google
        results['google'] = self.check_url(self.urls['google'], 'Google')
        
        # Проверяем Yandex
        results['yandex'] = self.check_url(self.urls['yandex'], 'Yandex')
        
        # Проверяем Telegram API, если токен указан
        if self.urls['telegram']:
            results['telegram'] = self.check_url(self.urls['telegram'], 'Telegram API')
        
        return results

    def analyze_results(self, results: Dict[str, Tuple[bool, str]]) -> Tuple[bool, str]:
        """
        Анализирует результаты проверки
        
        :param results: Результаты проверки сервисов
        :return: Кортеж (статус интернета, диагностическое сообщение)
        """
        successful_checks = sum(1 for success, _ in results.values() if success)
        total_checks = len(results)
        
        # Если проверяем только 2 сервиса (без Telegram)
        if total_checks == 2:
            threshold = 2  # Оба должны быть успешными
        else:
            threshold = 2  # 2 из 3 успешных
        
        if successful_checks >= threshold:
            return True, "Интернет доступен"
        else:
            # Анализируем, что именно не работает
            failed_services = []
            for service, (success, error) in results.items():
                if not success:
                    failed_services.append(f"{service}: {error}")
            
            if 'telegram' in results and not results['telegram'][0] and all(results[s][0] for s in results if s != 'telegram'):
                return True, "Интернет доступен, но проблемы с Telegram API"
            else:
                return False, f"Проблемы с интернетом. Ошибки: {', '.join(failed_services)}"

    def run_continuous_check(self):
        """
        Запускает непрерывную проверку
        """
        logging.info("Запуск мониторинга интернета...")
        logging.info(f"Интервал проверки: {self.check_interval} секунд")
        
        if not self.urls['telegram']:
            logging.warning("Токен Telegram бота не указан. Проверка только Google и Yandex")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.info(f"\n--- Проверка в {timestamp} ---")
                
                # Проверяем все сервисы
                results = self.check_all_services()
                
                # Логируем результаты
                for service, (success, message) in results.items():
                    status = "✓" if success else "✗"
                    logging.info(f"{service}: {status} {message}")
                
                # Анализируем результаты
                internet_ok, diagnosis = self.analyze_results(results)
                
                if internet_ok:
                    logging.info(f"РЕЗУЛЬТАТ: {diagnosis}")
                else:
                    logging.error(f"РЕЗУЛЬТАТ: {diagnosis}")
                
                # Ждем перед следующей проверкой
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logging.info("Мониторинг остановлен пользователем")
        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")

def main():
    # Настройка логирования
    setup_logging()
    
    # Конфигурация из переменных окружения
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    
    # Создаем экземпляр проверяльщика
    checker = InternetChecker(
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        check_interval=CHECK_INTERVAL
    )
    
    # Запускаем проверку
    checker.run_continuous_check()

if __name__ == "__main__":
    main()