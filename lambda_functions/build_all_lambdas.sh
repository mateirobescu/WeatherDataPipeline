#!/usr/bin/env bash
set -e

echo "Starting Lambda build process..."

cd "$(cd "$(dirname "$0")" && pwd)"

for dir in */
do
  (
    cd "$dir"
    FUNCTION_NAME=$(basename "$dir")
    ZIP_NAME="../${FUNCTION_NAME%/}.zip"
    BUILD_DIR="../build_${FUNCTION_NAME}"

    rm -rf "../$FUNCTION_NAME.zip"

    echo "=== Building ${FUNCTION_NAME} ==="

    rm -rf "$BUILD_DIR"
    mkdir "$BUILD_DIR"

    cp lambda_function.py "$BUILD_DIR"/lambda_function.py

    if [[ -f requirements.txt ]]; then
      echo "Installing dependencies..."
      pip install -qqr requirements.txt -t "$BUILD_DIR"
    fi

    echo "Creating ZIP package..."
    (cd "$BUILD_DIR" && zip -rq "$ZIP_NAME" .)

    rm -rf "$BUILD_DIR"

    echo -e "Finished building ${FUNCTION_NAME} --- $ZIP_NAME\n"
  )
done

echo "All lambda function built and ready for deployment!"