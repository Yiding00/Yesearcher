# Yesearcher
Academic Paper finder, basic information reader, paper saver. All In One!

## Based on

- pyalex: find paper using openalex

- tkinter: visualize

- pyzotero: output to zotero


## Usage

Use Y-Searcher to find, filter papers

```python
keywords = '"residual learning" OR "image recognition"'

w = Works().filter(from_publication_date="2015-07-01", to_publication_date="2017-07-31")
w.filter(title={"search":keywords})
```


Use Y-Reader to read the basic info (max 200 papers):
![alt text](image.png)

Use "保存" can save this paper to any folder of your zotero

## TODO

- 解决 某些会议不显示 的问题
- 英译中
- 尝试扩容，200篇对于长时间区间检索有些不够用


有任何关于本应用的想法欢迎与我讨论