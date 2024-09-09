import tkinter as tk
from tkinter import messagebox
import xml.etree.ElementTree as ET
import webbrowser
from utils import save_to_zotero, translate, check_id_exist
import sqlite3



class Y_Reader(tk.Tk):
    def __init__(self):
        super().__init__()
        # 设置目前论文index
        self.current_index = 0
        self.items = []
        # 设置程序名称以及窗口大小
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.title("Y-Reader")
        # self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.state('zoomed')

        # 创建画布（canvas）和用于按钮的容器（frame）
        self.canvas = tk.Canvas(self, bg="white")
        self.scroll_y = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas, bg="white")

        self.frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw", width=0.88*screen_width, height=0.92*screen_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        # 创建一个新的Frame用于垂直排列Label和Button
        self.controls_frame = tk.Frame(self, bg="white")
        self.controls_frame.pack(side=tk.LEFT, padx=10, pady=5)

        # 创建剩余数量的Label并添加到controls_frame中
        self.remaining_label = tk.Label(self.controls_frame, text="Remaining: 0", font=("Arial", 20))
        self.remaining_label.pack(padx=10, pady=5)

        # 创建按钮并添加到controls_frame中
        self.previous_button = tk.Button(self.controls_frame, text="上一篇", command=self.show_previous_item, font=("KaiTi", 20))
        self.previous_button.pack(padx=10, pady=5)
        self.next_button = tk.Button(self.controls_frame, text="下一篇", command=self.show_next_item, font=("KaiTi", 20))
        self.next_button.pack(padx=10, pady=5)
        self.save = tk.Button(self.controls_frame, text="保存", command=self.saveitem, font=("KaiTi", 20))
        self.save.pack(padx=10, pady=5)
        self.readmore = tk.Button(self.controls_frame, text="阅读原文", command=self.readmore, font=("KaiTi", 20))
        self.readmore.pack(padx=10, pady=5)

        # 创建用于显示文本内容的 Text 组件
        self.text_widget = tk.Text(self.frame, wrap="word", bg="white", state=tk.DISABLED)
        # 设置字体大小
        self.text_widget.tag_configure("title", font=("Helvetica", 40, "bold"), justify='center')
        self.text_widget.tag_configure("info", font=("Helvetica", 20, "italic"), justify='center')
        self.text_widget.tag_configure("body_en", font=("Helvetica", 24), lmargin1=240, lmargin2=200, rmargin=200)
        self.text_widget.tag_configure("body_cn", font=("KaiTi", 24), lmargin1=240, lmargin2=200, rmargin=200)
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_widget.bind("<KeyPress>", self.handle_key_press)
        # 创建一个数据库连接和一个游标对象
        self.conn = sqlite3.connect('papers.db')
        self.cursor = self.conn.cursor()
        
        # 加载 XML 数据
        self.load_xml_data()
        self.show_current_item()



    def on_frame_configure(self, event):
        # 更新 Canvas 的滚动区域以包括整个 Frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_xml_data(self):
        try:
            # 解析 XML 文件
            tree = ET.parse('openalex_works.xml')
            root = tree.getroot()
            self.items = root.find('channel').findall('item')
        except Exception as e:
            # 处理 XML 文件读取错误
            messagebox.showerror("Error", f"Unable to read XML file: {e}")

    def show_current_item(self):
        if self.current_index == 0:
            item = self.items[self.current_index]
            self.id = item.find('id').text
            self.title = item.find('title').text
            self.link = item.find('link').text
            info = item.find('first_author').text +'  '+item.find('journal').text +'  '+item.find('pubDate').text +'  Citation: '+ item.find('citation_count').text
            abs = item.find('description').text
            if check_id_exist(self.cursor, self.id)==0:
                if abs is None:
                    abs = "未找到摘要，请查看原文"
                    translation = "未找到摘要，请查看原文"
                else:
                    translation = translate(abs)
                    # translation = "未找到摘要，请查看原文"
                self.cursor.execute('''
INSERT INTO papers (title, author, pubDate, id, abstract, translation)
VALUES (?, ?, ?, ?, ?, ?)
''', (item.find('title').text, item.find('first_author').text, item.find('pubDate').text, self.id, abs, translation))
            # 显示内容
            self.display_text(self.title, info, self.id)
            # 更新剩余项目标签
            remaining_count = len(self.items) - (self.current_index + 1)
            self.remaining_label.config(text=f"剩余: {remaining_count}", font=("KaiTi", 20))
            self.canvas.update()
            next_item = self.items[self.current_index+1]
            self.next_abs = next_item.find('description').text
            if check_id_exist(self.cursor, next_item.find('id').text)==0:
                if self.next_abs is None:
                    self.next_abs = "未找到摘要，请查看原文"
                    self.next_translation = "未找到摘要，请查看原文"
                else:
                    self.next_translation = translate(self.next_abs)
                    # self.next_translation = "未找到摘要，请查看原文"
                self.cursor.execute('''
INSERT INTO papers (title, author, pubDate, id, abstract, translation)
VALUES (?, ?, ?, ?, ?, ?)
''', (next_item.find('title').text, next_item.find('first_author').text, next_item.find('pubDate').text, next_item.find('id').text, self.next_abs, self.next_translation))

        elif 0 < self.current_index < len(self.items):
            item = self.items[self.current_index]
            self.id = item.find('id').text
            self.title = item.find('title').text
            self.link = item.find('link').text
            info = item.find('first_author').text +'  '+item.find('journal').text +'  '+item.find('pubDate').text +'  Citation: '+ item.find('citation_count').text

            # 显示内容
            self.display_text(self.title, info, self.id)

            # 更新剩余项目标签
            remaining_count = len(self.items) - (self.current_index + 1)
            self.remaining_label.config(text=f"剩余: {remaining_count}", font=("KaiTi", 20))
            self.canvas.update()
            next_item = self.items[self.current_index+1]
            self.next_abs = next_item.find('description').text
            if check_id_exist(self.cursor, next_item.find('id').text)==0:
                if self.next_abs is None:
                    self.next_abs = "未找到摘要，请查看原文"
                    self.next_translation = "未找到摘要，请查看原文"
                else:
                    self.next_translation = translate(self.next_abs)
                self.cursor.execute('''
INSERT INTO papers (title, author, pubDate, id, abstract, translation)
VALUES (?, ?, ?, ?, ?, ?)
''', (next_item.find('title').text, next_item.find('first_author').text, next_item.find('pubDate').text, next_item.find('id').text, self.next_abs, self.next_translation))


        else:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, "已完成", font=("KaiTi", 20))
            self.remaining_label.config(text="剩余论文数: 0", font=("KaiTi", 20))

        self.conn.commit()


    def saveitem(self):
        save_to_zotero(self.items[self.current_index])

    def show_previous_item(self):
        # 显示上一篇
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_item()
        else:
            messagebox.showinfo("提示", "这是第一篇")

    def show_next_item(self):
        # 显示下一篇
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.show_current_item()
        else:
            messagebox.showinfo("提示", "已阅读完成")
    
    def readmore(self):
        # 阅读原文
        self.open_url(self.link)


    def display_text(self, title, info, id):
        self.cursor.execute("SELECT translation, abstract FROM papers WHERE id = ?", (id,))
        results = self.cursor.fetchall()
        for values in results:
            translation = values[0]
            abstract = values[1]
        # 清空文本组件
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        # 插入文本到 Text 组件
        self.text_widget.insert('1.0', title, 'title')
        self.text_widget.insert('2.0', '\n' + info, 'info')
        self.text_widget.insert('3.0', '\n\n' + translation, 'body_cn')
        self.text_widget.insert('6.0', '\n\n' + abstract, 'body_en')


        self.text_widget.config(state=tk.DISABLED)



    def handle_key_press(self, event):
        # 处理键盘按键事件，如复制选中的文本
        if event.keysym == "c" and event.state & 0x4:  # Ctrl + C
            self.text_widget.event_generate("<<Copy>>")

    def open_url(self, url):
        if url ==  None:
            messagebox.showinfo("提示", "本文无doi号")
        else:
            # 打开 URL
            webbrowser.open(url)

if __name__ == "__main__":
    app = Y_Reader()
    app.mainloop()

