from bs4 import BeautifulSoup

import requests


def get_html(url):
    r = requests.get(url)
    html = r.text
    return BeautifulSoup(html, 'html.parser')


url = 'http://ontomathpro.org/ontology/'
html = get_html(url)
list = html.find('ul')
terms = list()
list_elements = list.find_all('li')
print(len(list_elements))

for x in list_elements:
    page = x.find('a')
    inner_url = url + page.get('href')
    inner_html = get_html(inner_url)
    inner_list = inner_html.find('ul')
    if inner_list is None:
        continue
    for elem in inner_list.find_all('li'):
        label = elem.find('a').getText()
        if label == 'label':
            term = elem.find('span').getText()
            if '(ru)' in term:
                ru_term = term.replace('(ru)', '')
                print(ru_term)
                print(len(terms))
                terms.append(ru_term)

print(terms)
