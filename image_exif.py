from datetime import datetime

from PIL import Image, ExifTags, UnidentifiedImageError

TAGS = {name: number for number, name in ExifTags.TAGS.items()}


def get_exif(path):
    img = Image.open(path)
    return img._getexif()


def get_date(path):
    try:
        date_str = get_exif(path)[TAGS['DateTimeOriginal']]
    except UnidentifiedImageError or KeyError:
        return None
    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')


def _test(dir_path):
    import os
    images = os.listdir(dir_path)
    for image in images:
        path = os.path.join(dir_path, image)
        print(f'{image}: {get_date(path)}')


if __name__ == '__main__':
    _test('./fotos')
