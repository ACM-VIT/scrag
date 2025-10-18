from newspaper import Article

class NewspaperExtractor:
    """
    Extracts structured data from an article URL using newspaper3k.
    """
    def extract(self, url: str):
        if not url:
            return None

        try:
            article = Article(url)
            article.download()
            article.parse()

            return {
                "title": article.title,
                "text": article.text,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "url": article.url,
            }
        except Exception as e:
            return {"error": str(e)}