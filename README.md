# LZW-archiver
Данное приложение, используя алгоритм LZW, позволяет сжимать файлы в архив и извлекать их из него.

## Usage
```
lzw.py [-h] {compress,decompress,listing} ...
```

#### compress (Архивирование)
- positional arguments:
  * `archive_name` : Имя архива
  * `to_compress` : Файлы и каталоги для архивирования
  
#### decompress (Разархивирование)
- positional arguments:
  * `archive_name` : Архив

- optional arguments:
  * `-d DIR, --dir DIR` : Выходнй каталог
  * `-r, --restore-metadata` : Востановить метаданные файлов
  * `-i, --ignore-damage` : Разархивровать все файлы, игнорируя повреждения
  * `-a, --archive-not-damage` : Разархивровать, если архив не поврежден
  * `-f, --files-not-damage` : Разархивровать только неповрежденные файлы(по умолчанию)
  
#### listing (Просмотр файлов архива)
- positional arguments:
  * `archive_name` : Архив

- optional arguments:
  * `-v, --verbose` : Подробная информация
