import datetime
import os
import image_exif
import easygui
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog
from tkinter import messagebox


class OsMock(object):
    @staticmethod
    def rename(source, destination):
        print(f'{source} -> {destination}')

    class path(object):
        @staticmethod
        def exists(path):
            return False


# _os = OsMock()
_os = os


class Renaming(object):
    IMAGES_EXT = ('.jpg', )

    @classmethod
    def matching(cls, path):
        pass

    @classmethod
    def _rename(cls, source, destination):
        ext = os.path.splitext(source)[1]
        destination = os.path.join(os.path.dirname(source), destination)
        addition = ''
        index = 0
        while _os.path.exists(destination + addition + ext):
            index += 1
            addition = f' ({index})'

        destination = destination + addition + ext
        _os.rename(source, destination)

    @classmethod
    def rename_name_shot_time(cls, path, name):
        images = cls._files_in_dir(path)
        # to_rename = [image for image in images if not image.startswith(name)]
        for image in images:
            date_str = image_exif.get_date(image)
            if date_str is None:
                print(f'No date information in {image}')
                continue
            cls._rename(image, name + date_str.strftime('%Y.%m.%d_%H.%M.%S'))


class FileEntry(object):
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(self.path)
        self.date = get_date(self.path)
        self.after_prefix = '_' + self.date

    def get_new_name(self, prefix):
        return prefix + self.after_prefix + '.jpg'


class Gui(object):
    def __init__(self):
        self._root = tk.Tk()
        self._root.resizable(True, True)
        self._root.title('Photo rename')
        self._files = []
        self._entries = []  # type: [FileEntry]

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
        self._recalculate_button = tk.Button(top_frame, text="Reset names",
                                             command=self._reset_button_handle)
        self._recalculate_button.pack(side=tk.LEFT, anchor=tk.W, padx=5, pady=5)
        top_frame.pack(anchor=tk.W, fill='x')

        frame = tk.Frame(self._root)
        frame.pack(padx=5, pady=5, fill='x', expand=True)
        self._table = ttk.Treeview(frame)
        self._table['columns'] = ('date', 'after')
        self._table.heading("#0", text='Original')
        self._table.column("#0", anchor="w", width=300)
        self._table.heading('date', text='Date')
        self._table.column('date', anchor='w', width=150)
        self._table.heading('after', text='Renamed')
        self._table.column('after', anchor='w', width=300)
        self._table.grid(sticky=(tk.N, tk.S, tk.W, tk.E))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self._table.bind('<Double-1>', self._table_double_click)

        rename_button = tk.Button(self._root, text="Rename", command=self._rename_button_handle)
        rename_button.pack(fill='x', expand=True, padx=5, pady=5)

    def _table_double_click(self, event):
        selection = self._table.selection()
        if len(selection) == 0:
            return
        elif len(selection) != 1:
            raise Exception('Incorrect handling of table selection')
        row = self._table.identify_row(event.y)
        orig_name = self._table.item(selection, "text")
        row = [i for i, entry in enumerate(self._entries) if entry.name == orig_name]
        if len(row) != 1:
            raise Exception('Incorrect handling of table selection')
        else:
            row = row[0]

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
        path = './fotos/'
        files = [os.path.join(path, file) for file in os.listdir(path)]
        # files = easygui.fileopenbox("Select files to rename","photo_rename", multiple=True)
        if files is None:
            return
        self._files = files
        self._recalculate_entries()

    def _reset_button_handle(self):
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
        errors = []
        for entry in self._entries:  # type: FileEntry
            try:
                self._safe_rename(entry.path, entry.get_new_name(self._prefix_entry.get()))
            except Exception as ex:
                errors.append(str(ex))
        if errors:
            tk.messagebox.showerror('Errors occurred', '\n'.join(errors))
        else:
            tk.messagebox.showinfo('Success', f'{len(self._entries)} files renamed')

            self._files = []
            self._entries = []
            self._recalculate_entries()

    @staticmethod
    def _safe_rename(path, new_name):
        dir_name = os.path.dirname(path)
        new_path = os.path.join(dir_name, new_name)
        if path == new_path:
            return
        if os.path.exists(new_path):
            raise Exception(f'File {new_name} already exists')
        print(f'{path} -> {new_path}')
        os.rename(path, new_path)

    def quit(self):
        self._root.destroy()

    def run(self):
        self._root.mainloop()


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
