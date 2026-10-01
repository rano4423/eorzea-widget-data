#!/bin/sh
# Downloads the source data for build.js into ./cache.
set -e
cd "$(dirname "$0")"
mkdir -p cache
FT=https://raw.githubusercontent.com/icykoneko/ff14-fish-tracker-app/master
TC=https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging
curl -fsSL -o cache/data.js "$FT/js/app/data.js"
curl -fsSL -o cache/ft_license.txt "$FT/LICENSE"
curl -fsSL -o cache/tc_license.txt "$TC/LICENSE"
for f in legendary-fish nodes items places maps; do
  curl -fsSL -o "cache/tc_$f.json" "$TC/libs/data/src/lib/json/$f.json"
done
# kanji readings for search (Unicode Unihan database, Unicode License v3)
curl -fsSL -o cache/Unihan.zip https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip
unzip -o -q cache/Unihan.zip Unihan_Readings.txt -d cache
curl -fsSL -o cache/unicode_license.txt https://www.unicode.org/license.txt
echo done
