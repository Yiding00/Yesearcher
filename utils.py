import csv
from lxml import etree
from datetime import datetime
import pytz
from pyzotero import zotero
from METADATA import API_KEY, LIBRARY_ID, LIBRARY_TYPE, COLLECTION_KEY
import requests


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

    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
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


