#!/bin/bash

echo "Bruce VANTABLACK: Inicializando Biblioteca Cognitiva Suprema..."

LIB_DIR="./backend/knowledge/bruce_library"

declare -A BOOKS

# Filosofía
BOOKS["philosophy/meditations"]="https://www.gutenberg.org/cache/epub/2680/pg2680.txt"
BOOKS["philosophy/beyond_good_and_evil"]="https://www.gutenberg.org/cache/epub/4363/pg4363.txt"
BOOKS["philosophy/tao_te_ching"]="https://www.gutenberg.org/cache/epub/216/pg216.txt"
BOOKS["philosophy/apology_socrates"]="https://www.gutenberg.org/cache/epub/1656/pg1656.txt"

# Historia
BOOKS["history/peloponnesian_war"]="https://www.gutenberg.org/cache/epub/7142/pg7142.txt"
BOOKS["history/decline_of_rome"]="https://www.gutenberg.org/cache/epub/25717/pg25717.txt"

# Estrategia
BOOKS["strategy/art_of_war"]="https://www.gutenberg.org/cache/epub/132/pg132.txt"
BOOKS["strategy/the_prince"]="https://www.gutenberg.org/cache/epub/1232/pg1232.txt"

# Economía
BOOKS["economy/wealth_of_nations"]="https://www.gutenberg.org/cache/epub/3300/pg3300.txt"
BOOKS["economy/as_man_thinketh"]="https://www.gutenberg.org/cache/epub/4507/pg4507.txt"

# Ciencia
BOOKS["science/principia"]="https://www.gutenberg.org/cache/epub/28233/pg28233.txt"
BOOKS["science/relativity"]="https://www.gutenberg.org/cache/epub/5001/pg5001.txt"

# Desarrollo Personal
BOOKS["personal/the_science_of_getting_rich"]="https://www.gutenberg.org/cache/epub/28134/pg28134.txt"

# Crear carpetas y descargar libros
for path in "${!BOOKS[@]}"; do
  DIR="$LIB_DIR/$(dirname "$path")"
  FILE="$LIB_DIR/$path.txt"
  URL="${BOOKS[$path]}"
  mkdir -p "$DIR"
  echo "Descargando $(basename "$path") a $DIR..."
  wget -q "$URL" -O "$FILE"
done

echo "✅ Biblioteca instalada en: $LIB_DIR"
