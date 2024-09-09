from pyalex import Works
from utils import save_papers_info_rssfeed
from datetime import datetime, timedelta


def filter_from_month(keywords, year, month):
    formatted_date = f"{year}-{month:02d}-01"
    # print(formatted_date)
    w = Works().filter(from_publication_date=formatted_date)
    w.filter(title={"search":keywords})
    print("过滤得到的论文数：",w.count())

    xml_file_path = 'openalex_works.xml'
    save_papers_info_rssfeed(xml_file_path, w)

def filter_recent_n_years(keywords, n):
    today = datetime.today()
    last_n_year_today = today.replace(year=today.year - n)
    formatted_date = last_n_year_today.strftime("%Y-%m-%d")
    # print(formatted_date)
    w = Works().filter(from_publication_date=formatted_date)
    w.filter(title={"search":keywords})
    print("过滤得到的论文数：",w.count())

    xml_file_path = 'openalex_works.xml'
    save_papers_info_rssfeed(xml_file_path, w)


# w = Works().filter(from_publication_date="2015-07-01", to_publication_date="2017-07-31")