#!/bin/bash
# Local business LEAD finder via Azure Maps POI search.
# Usage: maps_leads.sh "query" [lat] [lon] [radius_m] [limit]
# Default center = Patna (25.5941, 85.1376). Prints: <name> | <phone or verify> | <address>
source ~/.openclaw/maps.env 2>/dev/null   # provides AZURE_MAPS_KEY
Q="$1"; LAT="${2:-25.5941}"; LON="${3:-85.1376}"; R="${4:-12000}"; L="${5:-12}"
ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$Q")
curl -s -m 20 "https://atlas.microsoft.com/search/poi/json?api-version=1.0&query=${ENC}&lat=${LAT}&lon=${LON}&radius=${R}&limit=${L}&subscription-key=${AZURE_MAPS_KEY}" \
  | python3 ~/.openclaw/maps_parse.py
