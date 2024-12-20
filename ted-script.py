import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def initialize_driver(start_page=1):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless
    chrome_options.add_argument("--disable-gpu")  # Desactivar la aceleración de GPU (recomendado para headless)
    chrome_options.add_argument("--no-sandbox")  # Evitar posibles problemas en entornos sin acceso a interfaz gráfica

    # Inicializar el WebDriver con las opciones configuradas
    driver = webdriver.Chrome(options=chrome_options)

    url = f"https://ted.europa.eu/es/search/result?publication-date-from=20240101&publication-date-to=20241204&search-scope=ACTIVE&page={start_page}"
    driver.get(url)

    wait = WebDriverWait(driver, 15)  # Aumenta el tiempo de espera si es necesario

    xpath_tender_url = '//a[contains(@id, "notice")]'
    xpath_cookie_accept = '//a[contains(@href, "accept")]'
    xpath_next_page = '//button[contains(@aria-label, "siguiente")]'

    # Aceptar cookies
    accept_cookies(wait, xpath_cookie_accept)

    return driver, wait, xpath_tender_url, xpath_next_page


def accept_cookies(wait, xpath_cookie_accept):
    try:
        accept_cookies_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath_cookie_accept))
        )
        accept_cookies_button.click()
        print("Consentimiento de cookies aceptado.")
        time.sleep(2)  # Breve pausa después de aceptar cookies
    except TimeoutException:
        print("No se encontró un consentimiento de cookies para aceptar.")


def extract_tender_urls(driver, xpath_tender_url):
    tender_elements = driver.find_elements(By.XPATH, xpath_tender_url)
    tender_urls = [tender.get_attribute('href') for tender in tender_elements]
    print(f"Extraidos {len(tender_urls)} enlaces de licitaciones del TED")
    return tender_urls


def save_to_txt(tender_urls, file):
    for url in tender_urls:
        file.write(url + '\n')
    print(f"Se han guardado {len(tender_urls)} URLs en el archivo.")


def is_next_page(wait, xpath_next_page):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_next_page)))
        return True
    except TimeoutException:
        return False


def click_next_page(wait, xpath_next_page):
    retry_count = 0
    while retry_count < 3:
        try:
            next_page_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath_next_page))
            )
            next_page_button.click()
            print("Clic en siguiente página.")
            time.sleep(2)  # Breve pausa después de hacer clic
            return True
        except TimeoutException:
            retry_count += 1
            print(f"Intento {retry_count} de 3: No se encontró el botón de siguiente página.")
            time.sleep(5)  # Esperar 5 segundos antes de intentar nuevamente
    return False


def main():
    start_page = 1   # Comenzamos desde la página 1
    page_number = start_page

    # Abrir el archivo para escribir (modo append)
    with open("tender_urls.txt", "a", encoding='utf-8') as file:
        tender_urls = []

        while True:  # Continuar hasta que no haya más páginas
            print(f"Scraping página {page_number}")
            driver, wait, xpath_tender_url, xpath_next_page = initialize_driver(start_page=page_number)

            tender_urls = extract_tender_urls(driver, xpath_tender_url)
            save_to_txt(tender_urls, file)  # Guardar las URLs en el archivo

            # Si hemos llegado al numero de pagina 500, reiniciar el driver
            if page_number == 500 and page_number != start_page:
                print(f"Se ha alcanzado la página {page_number}. Reiniciando el driver...")
                driver.quit()
                start_page = page_number + 1  # Ajustar la página inicial para el siguiente reinicio
                continue  # Saltamos el resto de la lógica y reiniciamos el ciclo

            # Navegar a la siguiente página
            if is_next_page(wait, xpath_next_page):
                if not click_next_page(wait, xpath_next_page):
                    print("No se pudo avanzar a la siguiente página. Terminando el proceso.")
                    break
                page_number += 1
                start_page = page_number  # Actualizar el número de página en la URL
                time.sleep(5)
            else:
                print("No hay más páginas para navegar. Terminando el proceso.")
                break

        print(f"Se han encontrado un total de {len(tender_urls)} licitaciones.")

    print("Proceso completado.")


# Llamar a la función principal
main()
