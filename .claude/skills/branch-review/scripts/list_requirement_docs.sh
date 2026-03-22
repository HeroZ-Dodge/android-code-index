#!/bin/bash
# 列出文件夹中的所有需求文档（PDF、DOCX 和图片）
# 用法: ./list_requirement_docs.sh <folder_path>

FOLDER_PATH=$1

if [ -z "$FOLDER_PATH" ]; then
    echo "Error: Folder path is required"
    echo "Usage: $0 <folder_path>"
    exit 1
fi

if [ ! -d "$FOLDER_PATH" ]; then
    echo "Error: '$FOLDER_PATH' is not a valid directory"
    exit 1
fi

echo "=== Requirements Documents in Folder ==="
echo "Folder: $FOLDER_PATH"
echo ""

echo "=== PDF Files ==="
PDF_COUNT=$(find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.pdf" \) | wc -l | xargs)
echo "Total PDF files: $PDF_COUNT"
find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.pdf" \) | sort
echo ""

echo "=== DOCX Files ==="
DOCX_COUNT=$(find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.docx" \) | wc -l | xargs)
echo "Total DOCX files: $DOCX_COUNT"
find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.docx" \) | sort
echo ""

echo "=== Image Files ==="
IMG_COUNT=$(find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | wc -l | xargs)
echo "Total image files: $IMG_COUNT"
find "$FOLDER_PATH" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | sort
echo ""

TOTAL_COUNT=$((PDF_COUNT + DOCX_COUNT + IMG_COUNT))
echo "=== Summary ==="
echo "Total documents: $TOTAL_COUNT (PDF: $PDF_COUNT, DOCX: $DOCX_COUNT, Images: $IMG_COUNT)"
