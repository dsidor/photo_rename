import datetime
import os
import sys
import image_exif
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog
import tkinter.scrolledtext
import tkinter.filedialog
import PIL
import PIL.ImageTk


class ReportWindow(tk.simpledialog.Dialog):
    def __init__(self, root, title, infos, errors):
        self.infos = infos
        self.errors = errors
        super().__init__(root, title)

    def body(self, frame):
        if self.infos:
            label_info = tk.Label(frame, text='Names changed:', font=('calibre', 12, 'bold'))
            label_info.pack()

            info_widget = tk.scrolledtext.ScrolledText(frame, height=5)
            info_widget.insert('end', self.infos)
            info_widget.config(state='disabled')
            info_widget.pack(fill='both', expand=True)

        if self.errors:
            label_info = tk.Label(frame, text='Errors:', fg='red', font=('calibre', 12, 'bold'))
            label_info.pack()

            error_widget = tk.scrolledtext.ScrolledText(frame, height=5)
            error_widget.insert('end', self.errors)
            error_widget.config(state='disabled')
            error_widget.pack(fill='both', expand=True)

        frame.pack(expand=1, fill='both')


class ImagePreview(tk.simpledialog.Dialog):
    def __init__(self, root, path):
        self.path = path
        self.img = None
        super().__init__(root, os.path.basename(path))

    def body(self, frame):
        img = PIL.Image.open(self.path)
        width, height = self._scaled_size(*img.size)
        img = img.resize((width, height))
        canvas = tk.Canvas(frame, width=width, height=height)
        self.img = PIL.ImageTk.PhotoImage(img)
        canvas.create_image(width/2, height/2, anchor=tk.CENTER, image=self.img)
        canvas.pack()
        frame.pack()

    @staticmethod
    def _scaled_size(width, height):
        scale = min(480.0 / width, 320.0 / height)
        return int(width * scale), int(height * scale)


class FileEntry(object):
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(self.path)
        self.date = get_date(self.path)
        self.after_prefix = ' ' + self.date

    def get_new_name(self, prefix):
        return prefix + self.after_prefix + '.jpg'


class Gui(object):
    def __init__(self):
        self._root = tk.Tk()
        self._root.resizable(True, True)
        self._root.title('Photo rename')
        self._files = []
        self._entries = []  # type: [FileEntry]
        self._default_dir = None
        if len(sys.argv) > 1:
            d = sys.argv[1]
            if os.path.isdir(d) and os.path.exists:
                self._default_dir = d

        top_frame = tk.Frame(self._root)
        self._select_files_button = tk.Button(top_frame, text="Select files",
                                              command=self._select_files_button_handle)
        self._select_files_button.pack(side=tk.LEFT, anchor=tk.W, padx=5, pady=5)
        name_label = tk.Label(top_frame, text='Enter name prefix:', font=('calibre', 10, 'bold'))
        name_label.pack(side=tk.LEFT, fill='x', padx=5, pady=5)
        self._prefix_entry = tk.Entry(top_frame)
        self._prefix_entry.insert(0, 'Name_prefix')
        self._prefix_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5, pady=5)
        self._prefix_entry.bind('<KeyRelease>', lambda _: self._redraw_table())
        self._prefix_entry.bind('<FocusOut>', lambda _: self._redraw_table())
        rename_button = tk.Button(top_frame, text="Rename", command=self._rename_button_handle)
        rename_button.pack(side=tk.LEFT, anchor=tk.W, padx=5, pady=5)
        top_frame.pack(anchor=tk.W, fill='x')

        frame = tk.Frame(self._root)
        self._table = ttk.Treeview(frame, selectmode='browse')
        self._root.minsize(width=400, height=300)
        self._table['columns'] = ('date', 'after')
        self._table.heading("#0", text='Original')
        self._table.column("#0", anchor="w", width=300)
        self._table.heading('date', text='Date')
        self._table.column('date', anchor='w', width=150)
        self._table.heading('after', text='Renamed')
        self._table.column('after', anchor='w', width=300)
        # self._table.grid(sticky=(tk.N, tk.S, tk.W, tk.E))
        self._table.pack(padx=5, pady=5, fill='both', expand=True)
        frame.pack(padx=5, pady=5, fill='both', expand=True)
        scroll = ttk.Scrollbar(self._table, orient="vertical", command=self._table.yview)
        scroll.pack(side='right', fill='y')
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self._table.bind('<Double-1>', self._table_double_click)

    def _table_double_click(self, event):
        row, column = self._get_selection_row_col(event)

        if 0 == column:
            self.preview_image(self._entries[row].path)
            return
        else:
            answer = tk.simpledialog.askstring("Change name to",
                                               f"original name: {self._entries[row].name}\n"
                                               f"date of shot:    {self._entries[row].date}",
                                               initialvalue=self._entries[row].after_prefix,
                                               parent=self._root)
            if answer is None:
                return

            self._entries[row].after_prefix = answer
            self._redraw_table()

    def insert_table(self, orig, date, renamed):
        self._table.insert('', 'end', text=orig, values=(date, renamed))

    def _select_files_button_handle(self):
        # path = './fotos/'
        # files = [os.path.join(path, file) for file in os.listdir(path)]
        files = [file.name for file in tk.filedialog.askopenfiles(initialdir=self._default_dir)]
        if not files:
            return
        self._default_dir = os.path.dirname(files[0])
        self._files = files
        self._recalculate_entries()

    def _recalculate_entries(self):
        names_set = {}
        self._entries = []
        for file in self._files:
            try:
                entry = FileEntry(file)
            except ValueError:
                continue
            if entry is None:
                continue

            count = names_set.get(entry.after_prefix)
            if count is None:
                names_set[entry.after_prefix] = 1
            else:
                names_set[entry.after_prefix] = count + 1
                entry.after_prefix += f'({count})'

            self._entries.append(entry)

        self._redraw_table()

    def _redraw_table(self):
        self._table.delete(*self._table.get_children())
        for file in self._entries:
            self.insert_table(file.name, file.date, file.get_new_name(self._prefix_entry.get()))

    def _rename_button_handle(self):
        changed = []
        errors = []
        for entry in self._entries:  # type: FileEntry
            try:
                changed.append(self._safe_rename(entry.path, entry.get_new_name(self._prefix_entry.get())))
            except Exception as ex:
                errors.append(str(ex))
        self._show_report('\n'.join(changed), '\n'.join(errors))

        self._files = []
        self._entries = []
        self._recalculate_entries()

    @staticmethod
    def _safe_rename(path, new_name):
        dir_name = os.path.dirname(path)
        new_path = os.path.join(dir_name, new_name)
        if path == new_path:
            return f'The same name: {new_name}'
        if os.path.exists(new_path):
            raise Exception(f'File {new_name} already exists')
        else:
            os.rename(path, new_path)
            return f'{os.path.basename(path)} -> {new_name}'

    def preview_image(self, path):
        ImagePreview(self._root, path)

    def quit(self):
        self._root.destroy()

    def run(self):
        self._root.mainloop()

    def _show_report(self, info_text, error_text):
        title = 'Success' if not error_text else 'Errors occurred'
        ReportWindow(self._root, title, info_text, error_text)

    def _get_selection_row_col(self, event):
        selection = self._table.selection()
        if len(selection) == 0:
            return
        elif len(selection) != 1:
            raise Exception('Incorrect handling of table selection')
        orig_name = self._table.item(selection, "text")
        row = [i for i, entry in enumerate(self._entries) if entry.name == orig_name]
        if len(row) != 1:
            raise Exception('Incorrect handling of table selection')
        else:
            row = row[0]

        column = int(self._table.identify_column(event.x).replace('#', ''))
        return row, column


def get_date(file):
    date = image_exif.get_date(file)
    if date is None:
        raise ValueError
    return datetime.datetime.strftime(date, '%Y-%m-%d_%H.%M.%S')


def main():
    gui = Gui()

    gui.run()


if __name__ == '__main__':
    main()
