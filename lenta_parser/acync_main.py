# import csv
import datetime
import random
import time
import aiofiles as aiofiles
import requests
from aiocsv import AsyncWriter
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import aiohttp
import asyncio
from aiohttp import ClientConnectorError


if __name__ == '__main__':
    async def parse_card(card) -> list:
        title = card.find('div', {'class': 'sku-card-small-header__title'}).get_text(strip=True).replace(u'\xa0', ' ')

        old_price_item = card.find('div', {'class': 'sku-card-small-prices__item sku-card-small-prices__item--regular'})
        old_price_integer = old_price_item \
            .find('span', {'class': 'price-label__integer'}) \
            .get_text(strip=True) \
            .replace(u'\xa0', ' ')
        old_price_decimal = old_price_item.find('small', {'class': 'price-label__fraction'}).get_text(strip=True)
        old_price = f'{old_price_integer}.{old_price_decimal}'

        new_price_item = card.find('div', {'class': 'sku-card-small-prices__item sku-card-small-prices__item--primary'})
        new_price_integer = new_price_item \
            .find('span', {'class': 'price-label__integer'}) \
            .get_text(strip=True) \
            .replace(u'\xa0', ' ')
        new_price_decimal = new_price_item.find('small', {'class': 'price-label__fraction'}).get_text(strip=True)
        new_price = f'{new_price_integer}.{new_price_decimal}'

        try:
            discount = card.find('div', {'class': 'discount-label-small '
                                                  'discount-label-small--sku-card '
                                                  'sku-card-small__discount-label'}).get_text(strip=True)
        except AttributeError:
            discount = f'{round((1 - int(new_price_integer.replace(" ", "")) / int(old_price_integer.replace(" ", ""))) * 100)}%'

        image_ref_pattern = re.compile(r'src=".+"')
        picture = str(card.find('div', {'class': 'square__inner'}).getText)
        image_ref = image_ref_pattern.search(picture)[0].replace('"', '')[4:]

        return [title,
                old_price,
                new_price,
                discount,
                image_ref]


    def parse_page(soup):
        cards = soup.findAll('div', {'class': 'sku-card-small-container js-sku-card-small'})
        _loop = asyncio.get_event_loop()
        coroutines = [parse_card(card) for card in cards]
        items = _loop.run_until_complete(asyncio.gather(*coroutines, return_exceptions=False))
        # items = []
        # for card in cards:
        #     items.append(parse_card(card))
        return items


    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': UserAgent().random
    }
    cookies = {
        'CityCookie': 'spb',
        'Store': '0012'
    }


    async def get(url):
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(url=url, headers=headers, cookies=cookies)
                return [await response.text(), response]
            except ClientConnectorError:
                response = 'ClientConnectorError'
                return [None, response]


    url_page = f'?page='
    results_responses = requests.get("https://lenta.com/promo/" + url_page + '1', headers=headers, cookies=cookies)

    result_t = results_responses
    soup = BeautifulSoup(result_t.text, 'lxml')
    li_next = str(soup.find('li', {'class': 'next'}).getText)
    end_page = int(re.search(r'rel="1 == \d+', li_next)[0].split('==')[1].strip())

    loop = asyncio.get_event_loop()
    coroutines_responses = [get("https://lenta.com/promo/" + url_page + str(page)) for page in range(1, end_page + 1)]
    results_responses = loop.run_until_complete(asyncio.gather(*coroutines_responses, return_exceptions=True))
    no_results = set(range(1, end_page + 1))

    pattern = re.compile(r'page=(\d+)')
    pages_parsed = set()
    coroutines_soups = []

    data = []

    while True:
        coroutines_responses = []
        print(no_results)

        for result_text, result in results_responses:
            searched = pattern.search(str(result))
            if searched:
                current_page = int(searched.group(1))
                pages_parsed.add(current_page)
                soup = BeautifulSoup(result_text, 'lxml')
                data.extend(parse_page(soup))

        no_results -= pages_parsed
        coroutines_responses = [get("https://lenta.com/promo/" + url_page + str(page)) for page in no_results]
        if len(no_results) == 0:
            break
        else:
            time.sleep(random.random())
            results_responses = loop.run_until_complete(asyncio.gather(*coroutines_responses, return_exceptions=True))


    # def write_data_to_file():
    #     _cur_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
    #     with open(
    #             f'ЛЕНТА__{_cur_time}.csv',
    #             'w',
    #             encoding='utf-8',
    #             newline=''
    #     ) as file:
    #         writer = csv.writer(file)
    #
    #         writer.writerow(
    #             [
    #                 'Продукт',
    #                 'Старая цена',
    #                 'Новая цена',
    #                 'Процент скидки',
    #                 'Ссылка на изображение',
    #             ]
    #         )
    #         writer.writerows(data)
    #
    #     return f'Файл ЛЕНТА_{_cur_time}.csv успешно записан!'


    async def write_data_to_file():
        _cur_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
        async with aiofiles.open(f'ЛЕНТА__{_cur_time}.csv', 'w', encoding='utf-8', newline='') as file:
            writer = AsyncWriter(file)

            await writer.writerow(
                [
                    'Продукт',
                    'Старая цена',
                    'Новая цена',
                    'Процент скидки',
                    'Время акции',
                ]
            )
            await writer.writerows(data)

        return f'Файл ЛЕНТА__{_cur_time}.csv успешно записан!'

    asyncio.get_event_loop().run_until_complete(write_data_to_file())
