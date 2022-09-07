import datetime

import requests
from bs4 import BeautifulSoup
import csv


def write_to_csv(data):
    cur_time = datetime.datetime.now().strftime('%d_%m_%Y')
    with open(f'{cur_time}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='excel')
        writer.writerow(
            [
                'Название',
                'Безопасная сделка',
                'Цена',
                'Дата и время размещения',
                'Описание',
                'Ссылка'
            ]
        )
        for item in data:
            writer.writerow(
                [
                    item['title'],
                    item['safe_deal'],
                    item['price'],
                    item['date_and_time'],
                    item['description'],
                    item['link']
                ]
            )
        print(f'[INFO] File {cur_time}.csv successfully written!')
        return f'{cur_time}.csv'


def collect_data(hours, days):
    data = []
    if hours < 1 or hours > 24 or days < 1 or days > 5:
        print(f'[ERROR] Invalid input data')
    now = datetime.datetime.now()
    for page_num in range(1, 100):
        cookies = {
            '__ddg1_': 'lIO0PA6BVZY7f0PeAmnk',
            'PHPSESSID': 'd30f161d56409587e2d558bfc1ed33a0',
            'new_pf0': '1',
            'new_pf10': '1',
            'hidetopprjlenta': '0',
            '_tm_lt_sid': '1658988047858.296898',
            '_ym_uid': '1658988049965280990',
            '_ym_d': '1658988049',
            '_ga': 'GA1.2.1671831563.1658988049',
            '_gid': 'GA1.2.775792834.1658988049',
            '_ga_cid': '1671831563.1658988049',
            'mindboxDeviceUUID': 'a1769ead-5847-4cd6-9088-c94037f78647',
            'directCrm-session': '%7B%22deviceGuid%22%3A%22a1769ead-5847-4cd6-9088-c94037f78647%22%7D',
            '_ym_isad': '2',
            '_ym_visorc': 'w',
            'uechat_3_first_time': '1658988049689',
            'uechat_3_disabled': 'true',
            'new_pf0': '1',
            'cookies_accepted': '1',
            'uechat_3_mode': '0',
            'uechat_3_pages_count': '2',
        }

        headers = {
            'authority': 'www.fl.ru',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'ru-RU,ru;q=0.9',
            'cache-control': 'max-age=0',
            # Requests sorts cookies= alphabetically
            # 'cookie': '__ddg1_=lIO0PA6BVZY7f0PeAmnk; PHPSESSID=d30f161d56409587e2d558bfc1ed33a0; new_pf0=1; new_pf10=1; hidetopprjlenta=0; _tm_lt_sid=1658988047858.296898; _ym_uid=1658988049965280990; _ym_d=1658988049; _ga=GA1.2.1671831563.1658988049; _gid=GA1.2.775792834.1658988049; _ga_cid=1671831563.1658988049; mindboxDeviceUUID=a1769ead-5847-4cd6-9088-c94037f78647; directCrm-session=%7B%22deviceGuid%22%3A%22a1769ead-5847-4cd6-9088-c94037f78647%22%7D; _ym_isad=2; _ym_visorc=w; uechat_3_first_time=1658988049689; uechat_3_disabled=true; new_pf0=1; cookies_accepted=1; uechat_3_mode=0; uechat_3_pages_count=2',
            'referer': 'https://www.fl.ru/projects/?kind=1',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }

        params = {
            'kind': '1',
        }

        response = requests.get('https://www.fl.ru/projects/?page=' + str(page_num) + '&kind=1', params=params,
                                cookies=cookies, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            soup.find('h1', class_='b-layout__txt b-layout__txt_fontsize_90 b-layout__txt_color_646464 '
                                   'b-layout__txt_bold b-layout__txt_lineheight_1').text.strip()
            break
        except AttributeError:
            cards = soup.findAll('div', class_='b-post__grid')
        for card in cards:
            title_card = card.find(class_='b-post__link').text.strip()
            card_link = card.find('a').get('href')
            response_card = requests.get('https://www.fl.ru/' + card_link, headers=headers)
            soup_card = BeautifulSoup(response_card.text, 'lxml')
            try:
                soup_card.find(class_='b-layout__txt_fontsize_12 b-layout__txt_bold '
                                      'b-layout__txt_color_1da409 b-layout__txt_padright_5 '
                                      'b-layout__txt_text_decor_none').text.strip()
                safety_deal_status = 'Присутствует'
            except AttributeError:
                safety_deal_status = 'Отсутсвует'
            price = soup_card.find('span', class_='b-layout__bold').text.strip()
            description = soup_card.find('div', class_='b-layout__txt b-layout__txt_padbot_20').text.strip()
            date_and_time = soup_card.find('div', class_='b-layout__txt b-layout__txt_padbot_30') \
                .find('div', class_='b-layout__txt b-layout__txt_fontsize_11').text.strip().replace(' ', '')
            date_and_time = date_and_time[:16]
            time = date_and_time
            link = 'https://www.fl.ru/' + card_link
            if abs(int(time[11:13]) - int(str(now.hour))) > hours or abs(int(time[0:2]) - int(str(now.day))) > days:
                return data
            data.append({
                'title': title_card,
                'safe_deal': safety_deal_status,
                'price': price,
                'date_and_time': date_and_time,
                'description': description,
                'link': link
            })
    return data


def main():
    result_data = collect_data(24, 1)
    write_to_csv(result_data)


if __name__ == '__main__':
    main()
