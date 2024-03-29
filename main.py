from requests_html import HTMLSession
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import os

#Как я понял, лучше проверить, является ли url действительным URL
def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_images(url):
    session = HTMLSession()
    response = session.get(url)
    response.html.render(timeout=20) # это вдруг сайт на Javascript и таймаут поставил 20 секунд
    soup = bs(response.html.html, "html.parser")
    urls = []
    for img in tqdm(soup.find_all("img"), "Извлечено изображение"):
        img_url = img.attrs.get("src") or img.attrs.get("data-src") or img.attrs.get("data-original")
        print(img_url)
        if not img_url: # если img не содержит атрибута src, просто пропустим
            continue
        img_url = urljoin(url, img_url)
        # далее, как я прочел надо сделать блок, который удаляет
        # URL‑адреса типа в название которого заканчивается что-то вроде ?c=253.2.255'
        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass
        if is_valid(img_url):
            urls.append(img_url)
    session.close()
    return urls


def download(url, pathname):
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get("Content-Length", 0))
    filename = os.path.join(pathname, url.split("/")[-1])
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True,
                    unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress.iterable:
            f.write(data)
            progress.update(len(data))


def main(url, path):
    imgs = get_all_images(url)
    for img in imgs:
        download(img, path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Этот скрипт загружает все изображения с веб‑страницы.")
    parser.add_argument("url", help="URL‑адрес веб‑страницы, с которой вы хотите загрузить изображения.")
    parser.add_argument("-p", "--path",
                        help="Каталог, в котором вы хотите хранить изображения, по умолчанию - это домен переданного URL")

    args = parser.parse_args()
    url = args.url
    path = args.path
    if not path:
        path = urlparse(url).netloc

    main(url, path)
