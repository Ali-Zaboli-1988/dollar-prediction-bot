import requests
from newspaper import Article
from typing import List, Dict
import time
from bs4 import BeautifulSoup

def fetch_news_from_urls(urls: List[str]) -> List[Dict[str, str]]:
    results = []
    for url in urls:
        try:
            article = Article(url, language='fa')
            article.download()
            time.sleep(1)
            article.parse()
            results.append({
                'url': url,
                'title': article.title or 'بدون عنوان',
                'text': article.text or ''
            })
        except Exception:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=' ', strip=True)
                title = soup.title.string if soup.title else 'عنوان یافت نشد'
                results.append({
                    'url': url,
                    'title': title,
                    'text': text[:8000]
                })
            except Exception as e:
                results.append({
                    'url': url,
                    'title': 'خطا',
                    'text': f'قادر به دریافت خبر: {str(e)}'
                })
    return results

def combine_news_texts(news_list: List[Dict[str, str]]) -> str:
    return ' '.join([item['text'] for item in news_list if item['text']])
