import telebot #Bot Telegram
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup #Captura de URL
import time #Sleep de requisição do site
import math
import re

bot = telebot.TeleBot("5973224926:AAEOGHIB7yKGAvYvvUEfh2Un6ddzTjIp0Ds")

results = {'found': False}
current_product = None

# Função para fazer uma solicitação HTTP com tratamento de exceções
def make_request(url, headers, max_retries=5):
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Lança uma exceção se a resposta for um erro HTTP
            return response
        except requests.exceptions.RequestException as e:
            print(f"Erro na solicitação HTTP: {e}")
            time.sleep(10)  # Espera por 10 segundos antes de tentar novamente
    return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Olá! Este bot busca preços mais baratos de produtos na internet.')
    bot.send_message(message.chat.id, 'Digite o nome do produto que deseja pesquisar especificando nome, marca, modelo, etc:')

def get_prices():
    # Kabum
    results_kabum = get_prices_kabum(current_product)
    if results_kabum:
        results["Kabum"] = results_kabum

def get_prices_kabum(product):
    # Configurar o driver do navegador (neste caso, ChromeDriver)
    driver = webdriver.Chrome()

    # Use a URL inicial
    url_site_4 = f"https://www.kabum.com.br/busca/{product}"
    headers_site_4 = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
    try:
        # Abrir a URL inicial
        driver.get(url_site_4)

        # Use o WebDriverWait para aguardar a presença de um elemento que indica o redirecionamento
        wait = WebDriverWait(driver, 10)  # Defina um tempo limite (em segundos) para aguardar o redirecionamento

        # Agora que o elemento é visível, você sabe que o redirecionamento ocorreu
        print("Redirecionamento concluído")

        # Se desejar, você pode obter a URL atual após o redirecionamento
        url_redirecionada = driver.current_url
        print(f"URL redirecionada: {url_redirecionada}")

        response_site_4 = requests.get(url_site_4, headers=headers_site_4)
        soup_site_4 = BeautifulSoup(response_site_4.content, "html.parser")
        qtd_itens_element_4 = soup_site_4.find('div', id='listingCount')
        print(f"Status da resposta da Kabum: {response_site_4.status_code}")
        if qtd_itens_element_4:
            qtd_itens = qtd_itens_element_4.get_text().strip()
            index = qtd_itens.find(' ')
            qtd = qtd_itens[:index]
        else:
            # Lida com o caso em que o elemento não foi encontrado
            print("Elemento 'listingCount' não encontrado na página.")
            return None  # Ou você pode lidar com isso de outra forma, como retornar um dicionário vazio.

        ultima_pagina = math.ceil(int(qtd) / 20)

        dic_produtos = {'name': [], 'price': [], 'payment': []}

        # Inicialize o valor mínimo como infinito e a marca correspondente como vazia
        price_min = float('inf')
        name_price_min = ""
        payment_price_min = ""

        product_keywords = current_product.lower().split()

        for i in range(1, ultima_pagina + 1):
            url_pag = f"{url_redirecionada}?page_number={i}&page_size=20&facet_filters=&sort=most_searched"
            site = requests.get(url_pag, headers=headers_site_4)
            soup_site_4 = BeautifulSoup(site.content, "html.parser")
            produtos = soup_site_4.find_all("div", class_=re.compile("productCard"))

            payment_text_4 = "Informação não disponível"  # Valor padrão para payment_text_4

            for produto in produtos:
                name_element_site_4 = produto.find("span", class_=re.compile("nameCard")).get_text().strip()
                price_element_site_4 = produto.find("span", class_=re.compile("priceCard")).get_text().strip()

                # Converta o nome do produto do site em letras minúsculas para facilitar a comparação
                name_element_site_4_lower = name_element_site_4.lower()

                # Verifique se a palavra-chave está no nome do produto
                if any(keyword in name_element_site_4_lower for keyword in product_keywords):
                    # Remova caracteres não numéricos da string de preço
                    price_element_site_4 = price_element_site_4.replace('R$', '').replace('.', '').replace(',', '.')

                    try:
                        price_num = float(price_element_site_4)
                    except ValueError:
                        # Trate o erro se não for possível converter em float (por exemplo, se houver espaços ou caracteres não numéricos)
                        continue

                    # Tente encontrar o elemento de pagamento, mas verifique se ele existe antes de acessar o método get_text()
                    payment_element_site_4 = produto.find("span", class_=re.compile("priceTextCard"))
                    payment_text_4 = payment_element_site_4.get_text().strip() if payment_element_site_4 else "Informação não disponível"

                    if price_num < price_min:
                        price_min = price_num
                        name_price_min = name_element_site_4
                        payment_price_min = payment_text_4

                    print(name_element_site_4, price_element_site_4, payment_text_4)

                dic_produtos['name'].append(name_element_site_4)
                dic_produtos['price'].append(price_element_site_4)
                dic_produtos['payment'].append(payment_text_4)

            print(url_pag)

        # Após percorrer todas as páginas, o menor preço estará em 'preco_minimo' e a marca correspondente em 'marca_preco_minimo'
        print(f"O menor preço encontrado é: R${price_min:.2f} da marca {name_price_min}, forma de pagamento: {payment_price_min}")

        # Preencha o dicionário 'data' com as informações do menor preço
        data = {}
        if name_price_min:
            data["name"] = name_price_min
        if price_min != float('inf'):
            data["price"] = f"R${price_min:.2f}"
        if payment_price_min:
            data["payment"] = payment_price_min

        # Adicione 'data' ao dicionário 'results'
        if data:
            results["Kabum"] = data
            print(data)

        # Se um produto foi encontrado, defina 'results["found"]' como True
        if name_price_min:
            results["found"] = True

        return results

    except Exception as e:
        print(f"Erro ao aguardar o redirecionamento: {e}")

    # Feche o navegador
    driver.quit()

@bot.message_handler(func=lambda message: True)
def search_price(message):
    global current_product  # Use a variável global para armazenar o produto pesquisado
    current_product = message.text
    results.clear()
    results['found'] = False
    # Enviando a mensagem de aguardo
    bot.send_message(message.chat.id, 'Aguarde um momento enquanto pesquisamos os melhores preços para você...')
    get_prices_kabum(current_product)  # Passe o produto como um argumento

    if results['found']:
        response = "Preço Mais Barato Encontrado:\n"
        for site, data in results.items():
            if isinstance(data, dict):  # Verifique se data é um dicionário
                name = data.get("name", "Nome não encontrado")
                price = data.get("price", "Preço não encontrado")
                payment = data.get("payment", "Forma de pagamento não encontrada")
                response += f"{site}:\nNome do Produto: {name}\nPreço: {price}\nForma de Pagamento: {payment}\n\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, f"Não foi possível encontrar preços para o produto '{current_product}'.")

bot.polling()