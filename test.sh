#!/bin/bash

echo "Loading environment variables..."
export $(< .env)

echo "Generating test receipts..."
python3 scripts/generate_test_receipts.py

echo ""
echo "Running OCR classification tests..."
python3 scripts/run_tests.py

echo ""
echo "Done! Tests completed."
echo ""
echo "Notes:"
echo "- Gemini 2.5 Flash is the default model"
echo "- OpenAI can be used with --model openai:gpt-4o (requires valid API key)"
echo "- Test images are in test-images/ directory"
