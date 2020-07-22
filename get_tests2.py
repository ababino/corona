import re
import glob
import time
import os
from datetime import datetime, timedelta

import requests
import pdftotext
# import textract
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer

# trae links
links = []
for mes in ['mayo', 'junio', 'julio']:
    url = "https://www.argentina.gob.ar/coronavirus/informe-diario/{}2020".format(mes)
    #https://www.argentina.gob.ar/sites/default/files/20-05-20_reporte-matutino-covid-19.pdf
    page = requests.get(url)
    data = page.text
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.findAll('a', attrs={'href': re.compile("^https://www.argentina.gob.ar/sites/default/files/(.+)matutino(.+)pdf")}):
        links.append(link.get('href'))


    confirmed_re = re.compile(r'El total de casos confirmados en Argentina es de (?P<confirmed>\d+(\.?)\d+)')
    new_tests_re = re.compile(r'Ayer fueron realizadas (?P<new_tests>\d+(\.?)\d+) nuevas muestras')
    date_re = re.compile(r'(?P<date>([0-3]?\d)(\/[0-1]\d+\/| de \w+ de )2020)')

    month_translation = {'mayo': 'may', 'junio': 'jun', 'julio': 'jul'}
    data = []

    # copia pdf
    for url in links:
        # print(url)
        fn = os.path.join('data', 'argentina', url.split('/')[-1])
        if fn not in glob.glob(os.path.join('data', 'argentina', '*.pdf')):
            print('Downloading: {}'.format(fn))
            myfile = requests.get(url, allow_redirects=True)
            open(fn, 'wb').write(myfile.content)
            time.sleep(0.3)
        else:
            # print('{} already downloaded'.format(fn))
            pass

        # extrae txt
        # print('extract text')
        # text = textract.process(fn, encoding='UTF-8',method='pdftotext')
        with open(fn, "rb") as f:
            pdf = pdftotext.PDF(f)
            text = "\n\n".join(pdf)

        open('parte.txt', 'w').write(text)

        # extrae tests
        # print('extract info')

        with open('parte.txt') as infile, open('provs.txt', 'w') as outfile:
            new_data = {}
            for line in infile:
                line = line.strip()
                date_search = date_re.search(line)
                if date_search:
                    new_data['date'] = date_search.group('date')
                    for key in month_translation:
                        if key in new_data['date']:
                            val = month_translation[key]
                            new_data['date'] = new_data['date'].replace(key, val)
                            new_data['date'] = datetime.strptime(new_data['date'], '%d de %b de %Y')
                            break
                    if not isinstance(new_data['date'], datetime):
                        new_data['date'] = datetime.strptime(new_data['date'], '%d/%m/%Y')
                    new_data['date'] -= timedelta(days=1)
                    # print('date', new_data['date'])
                confirmed_search = confirmed_re.search(line)
                new_tests_search = new_tests_re.search(line)
                if confirmed_search:
                    new_data['confirmed'] = int(confirmed_search.group('confirmed').replace('.', ''))
                    # print('confirmed', new_data['confirmed'])
                if new_tests_search:
                    new_data['new_tests'] = int(new_tests_search.group('new_tests').replace('.', ''))
                    # print('new tests', new_data['new_tests'])
                if len(new_data)==3:
                    break
        data.append(new_data)


df = pd.DataFrame(data)
df = df[['date', 'confirmed', 'new_tests']]
df = df.sort_values('date')
df.to_csv('data/argentina/argentina_tests2.csv', index=False)
