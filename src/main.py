from urllib.parse import urljoin
from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL, EXPECTED_STATUS
import requests_cache
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
from outputs import control_output
import logging
from configs import configure_argument_parser, configure_logging
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li',
                                              attrs={
                                                  'class': 'toctree-l1'})
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python,
                        desc='Выполнение цикла парсинга'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            return
        soup = BeautifulSoup(response.text,
                             features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append(
            (version_link, h1.text, dl_text)
        )
    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = soup.find('div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]

    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
        break
    else:
        raise Exception('Ничего не нашлось')
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = soup.find('div', {'role': 'main'})
    table_tag = main_tag.find('table', {'class': 'docutils'})
    pdf_a4_tag = table_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    archive_path = downloads_dir / filename

    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_section = soup.find('section', attrs={'id': 'numerical-index'})
    section_tbody = main_section.find('tbody')
    tr = section_tbody.find_all('tr')
    abbreviation_pattern = r'[IPS][ADFPRSW]?'
    pep_info = {}
    for item in tqdm(tr):
        type_status = re.search(abbreviation_pattern, item.text).group()
        if len(type_status) == 2:
            status_general = EXPECTED_STATUS[type_status[1]]
        else:
            status_general = EXPECTED_STATUS['']
        td = item.find('a')
        pep_link = urljoin(PEP_URL, td['href'])
        pep_response = session.get(pep_link)
        pep_response.encoding = 'utf-8'
        pep_soup = BeautifulSoup(pep_response.text, 'lxml')
        pep_section = pep_soup.find('dl',
                                    attrs={'class':
                                           'rfc2822 field-list simple'})
        for i in range(len(pep_section.text.split())):
            if pep_section.text.split()[i] == 'Status:':
                status_card = pep_section.text.split()[i+1]
                break
        if status_card is None:
            logging.info(f'Статус PEP не найден: {pep_link}')
            status_card = "Unknown status"
        pep_info[status_card] = pep_info.get(status_card, 0) + 1
        if status_card not in status_general:
            logging.info(f'Несовпадающие статусы: {pep_link}\n'
                         f'Статус в карточке: {status_card}\n'
                         f'Ожидаемые статусы:{status_general}')
    results = [('Статус', 'Количество')]
    for item in pep_info.items():
        results.append(item)
    results.append(('Total', sum(pep_info.values())))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
