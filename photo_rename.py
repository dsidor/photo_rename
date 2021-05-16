import datetime
import os
import image_exif
import easygui
import tkinter


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


class Table:
    def __init__(self, tk, data):
        self._data = [[src_name, tkinter.StringVar(value=dst_name)] for src_name, dst_name in data]

        # code for creating table
        for i in range(len(data)):
            self.e = tkinter.Entry(tk, width=40, fg='black', font=('Arial', 12))
            self.e.grid(row=i, column=0)
            self.e.insert(tkinter.END, self._data[i][0])
            self.e.config(state='readonly')

            if data[i][1] is None:
                self.e = tkinter.Entry(tk, width=40, fg='red', font=('Arial', 12, 'italic'))
                self.e.insert(0, 'Not an image')
                self.e.grid(row=i, column=1)
                self.e.config(state='readonly')
            else:
                # data[i][1] = tkinter.StringVar()
                # self._data[i][1].set(data[i][1])
                self.e = tkinter.Entry(tk, width=40, fg='black', font=('Arial', 12), textvariable=self._data[i][1])
                self.e.grid(row=i, column=1)


def _test():
    # files = easygui.fileopenbox("Select files to rename","photo_rename", multiple=True)
    # if files is None:
    #     exit(0)
    path = './fotos/'
    def get_new_name(file):
        start_name = 'Imie_Nazwisko'
        date = image_exif.get_date(file)
        if date is None:
            return None
        date = datetime.datetime.strftime(date, '%Y-%m-%d_%H.%M.%S')
        return start_name + '_' + date + '.jpg'
    files = [os.path.join(path, file) for file in os.listdir(path)]
    renames = [[os.path.basename(file), get_new_name(file)] for file in files]
    renames = sorted(renames, key=lambda x: x[0].lower())
    print('\n'.join(f'{k}' for k in renames))

    root = tkinter.Tk()
    root.resizable(False, False)
    root.title('Photo rename')
    frame = tkinter.Frame(root)
    frame.pack(padx=5, pady=5, fill='x', expand=True)
    t = Table(frame, renames)

    def rename_button_handle():
        root.destroy()
        print(renames[-2][1].get())

    rename_button = tkinter.Button(root, text="Rename", command=rename_button_handle)
    rename_button.pack(fill='x', expand=True, padx=5, pady=5)
    root.mainloop()

    # renames = {os.path.basename(file): image_exif.get_date(file) for file in files}
    # print('\n'.join([f'{k}: {v}' for k, v in renames.items()]))


if __name__ == '__main__':
    _test()
