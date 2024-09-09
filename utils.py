import csv
from lxml import etree
from datetime import datetime
import pytz
from pyzotero import zotero
from METADATA import ZOTERO_API_KEY, LIBRARY_ID, LIBRARY_TYPE, COLLECTION_KEY, ZHIPU_KEY
import requests
from zhipuai import ZhipuAI
import os
import sqlite3


def save_papers_info_csv(csv_file_path, works):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Publication Date', 'Cited By Count', 'Cited By Percentile','journal', 'doi'])
        for work in works.get():
            print(work)
            title = work['title']
            publication_date = work['publication_date']
            cited_by_count = work['cited_by_count']
            cited_by_percentile_year = work['cited_by_percentile_year']['min']
            temp = work['locations'][0]
            print(temp)
            if temp['source'] is not None:
                journal = temp['source']['display_name']
            else:
                journal = "None"
            doi = work['doi']
            writer.writerow([title, publication_date, cited_by_count, cited_by_percentile_year, journal, doi])
    

def save_papers_info_rssfeed(xml_file, works):
    rss = etree.Element('rss', version='2.0')
    channel = etree.SubElement(rss, 'channel')
    title = etree.SubElement(channel, 'title')
    title.text = 'OpenAlex Works Feed'
    link = etree.SubElement(channel, 'link')
    link.text = 'https://openalex.org'
    description = etree.SubElement(channel, 'description')
    description.text = 'RSS feed for works from OpenAlex API'
    for work in works.get(per_page=200):
        item = etree.SubElement(channel, 'item')
        title = etree.SubElement(item, 'title')
        title.text = work['title']
        id = etree.SubElement(item, 'id')
        id.text = work['id'][21:]
        description = etree.SubElement(item, 'description')
        description.text = work["abstract"]
        pubDate = etree.SubElement(item, 'pubDate')

        date_obj = datetime.strptime(work.get('publication_date', '1970-01-01'), '%Y-%m-%d')
        date_obj = date_obj.replace(tzinfo=pytz.utc)  # 将时间设为UTC时区
        pubDate.text = date_obj.strftime('%Y-%m-%d')

        link = etree.SubElement(item, 'link')
        link.text = work['doi']
        temp = work['locations']
        if temp != []:
            if temp[0]['source'] is not None:
                journal_name = temp[0]['source']['display_name']
            else:
                journal_name = "Journal-None"
        else:
            journal_name = "Journal-None"
        journal = etree.SubElement(item, 'journal')
        journal.text = journal_name
        first_author = etree.SubElement(item, 'first_author')
        temp = work['authorships']
        if temp != []:
            first_author.text = work['authorships'][0]['author']['display_name']
        else: 
            first_author.text = "No Author"
        citation_count = etree.SubElement(item, 'citation_count')
        citation_count.text = str(work['cited_by_count'])
    with open(xml_file, 'wb') as file:
        file.write(etree.tostring(rss, pretty_print=True, xml_declaration=True, encoding='UTF-8'))



def save_to_zotero(item):

    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, ZOTERO_API_KEY)
    title = item.find('title').text
    authors = item.find('first_author').text
    publication_date = item.find('pubDate').text
    doi = item.find('link').text[16:]

    zotero_item = {
        'itemType': 'journalArticle',
        'title': title,
        'creators': [{'creatorType': 'author', 'firstName': author.split(' ')[0], 'lastName': ' '.join(author.split(' ')[1:])} for author in authors.split(', ')],
        'date': publication_date,
        'DOI': doi,
    }
    response = zot.create_items([zotero_item])
    item_key = response['success']['0']
    item_details = zot.item(item_key)
    payload = {
        "key": item_details['data']['key'],
        "version": item_details['data']['version'],
        "data": item_details['data']
    }
    zot.addto_collection(COLLECTION_KEY, payload)
    # find_and_attach_pdf(item_key, doi, zot)


def find_and_attach_pdf(item_key, doi,zot):
    pdf_url = f"https://api.unpaywall.org/v2/{doi}?email=your_email@example.com"
    response = requests.get(pdf_url)

    if response.status_code == 200:
        data = response.json()
        pdf_link = data.get('best_oa_location', {}).get('url_for_pdf')

        if pdf_link:
            # 下载并附加 PDF
            zot.attachment_add_link(pdf_link, item_key)


def translate(text):
    client = ZhipuAI(api_key=ZHIPU_KEY)

    response = client.chat.completions.create(
        model="glm-4-plus",
        messages=[
            {
                "role": "system",
                "content": "你是一个翻译专家，需要专注于英文书籍的翻译，确保准确性和专业性，同时符合中文表达习惯。你的任务是准确、专业地将英文语句翻译成中文，保持原意，符合中文表达习惯。" 
            },
            {
                "role": "user",
                "content": text
            }
        ],
        top_p= 0.7,
        temperature= 0.95,
        max_tokens=1024,
        tools = [{"type":"web_search","web_search":{"search_result":True}}],
        stream=False
    )
    translation = response.choices[0].message.content if response.choices else "翻译失败"
    return translation

def check_id_exist(cursor, id):
    cursor.execute('''
SELECT COUNT(*) FROM papers WHERE id = ?
''', (id,))
    return cursor.fetchone()[0]

def delete_id(id):
    conn = sqlite3.connect('papers.db')
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM papers WHERE id = ?
    ''', (id,))
    conn.commit()
    conn.close()


def check_database():
    if os.path.exists('papers.db')!=True:
        # 创建一个数据库连接（文件数据库）
        conn = sqlite3.connect('papers.db')
        cursor = conn.cursor()

        # 执行 SQL 语句

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT,
            translation TEXT,
            link TEXT,
            journal TEXT,
            author TEXT,
            pubDate TEXT,
            citation_count INTEGER,
            rate INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # 提交更改并关闭连接
        conn.commit()
        conn.close()

def check_METADATA():
    file_path = 'METADATA.py'
    if os.path.exists(file_path)!=True:
        with open(file_path, 'w') as file:
            # 写入内容
            file.write("""ZOTERO_API_KEY = 'xxx'
LIBRARY_ID = 'xxx'
LIBRARY_TYPE = 'user'
COLLECTION_KEY = 'xxx'
ZHIPU_KEY = 'xxx.xxx'""")
