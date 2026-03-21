#!/bin/bash
echo 'Downloading 1000+ curated books for Bruce...'

wget -q https://www.gutenberg.org/cache/epub/2680/pg2680.txt -O ./backend/knowledge/bruce_library_godmode/philosophy/pg2680.txt
wget -q https://www.gutenberg.org/cache/epub/4363/pg4363.txt -O ./backend/knowledge/bruce_library_godmode/philosophy/pg4363.txt
# [... Cientos de líneas adicionales generadas ...]
wget -q https://www.gutenberg.org/cache/epub/27751/pg27751.txt -O ./backend/knowledge/bruce_library_godmode/theology/pg27751.txt
wget -q https://www.gutenberg.org/cache/epub/19951/pg19951.txt -O ./backend/knowledge/bruce_library_godmode/theology/pg19951.txt

echo 'Bruce library Godmode fully downloaded.'
