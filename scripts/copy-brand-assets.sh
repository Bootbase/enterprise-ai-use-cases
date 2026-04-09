#!/usr/bin/env bash
# Copy Bootbase brand assets into the Jekyll site
# Run from repo root:  bash scripts/copy-brand-assets.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRAND_SRC="$HOME/Documents/01 Bootbase/Portfolio/Bootbase/Projects/bootbase.be/assets"

DEST_FAVICON="$REPO_ROOT/docs/assets/favicon"
DEST_IMG="$REPO_ROOT/docs/assets/img"

echo "Copying brand assets..."

# Create directories
mkdir -p "$DEST_FAVICON" "$DEST_IMG"

# Copy favicons
cp "$BRAND_SRC/favicon/favicon.ico"          "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/favicon-16x16.png"    "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/favicon-32x32.png"    "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/favicon-96x96.png"    "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/apple-icon.png"       "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/apple-icon-180x180.png" "$DEST_FAVICON/"
cp "$BRAND_SRC/favicon/android-icon-192x192.png" "$DEST_FAVICON/"

# Copy logos
cp "$BRAND_SRC/logo-64.png"        "$DEST_IMG/"
cp "$BRAND_SRC/logo-white-200.png" "$DEST_IMG/"
cp "$BRAND_SRC/logo-blue-250.png"  "$DEST_IMG/"

echo "Done! Assets copied to docs/assets/"
echo ""
echo "Now commit and push:"
echo "  cd $REPO_ROOT"
echo "  git add -A"
echo "  git commit -m 'feat: apply Bootbase branding and update site messaging'"
echo "  git push origin main"
