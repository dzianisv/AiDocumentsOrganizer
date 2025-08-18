# GitHub Actions Setup

## Setting up GEMINI_API_KEY Secret

To enable automated testing in GitHub Actions, you need to add your Gemini API key as a repository secret:

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the following secret:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Your Gemini API key (get it from https://makersuite.google.com/app/apikey)

## GitHub Actions Workflow

The workflow (`.github/workflows/test.yml`) will automatically:

- Run on every push to the `main` branch
- Run on every pull request targeting `main`
- Install Tesseract OCR with English, Russian, and Ukrainian language support
- Install Python dependencies
- Generate test receipt images
- Run OCR classification tests using Gemini 2.5 Flash
- Upload test results as artifacts

## Test Coverage

The tests include receipts from:
- **Safeway** (US grocery store) - English text
- **Silpo** (Ukrainian grocery chain) - Ukrainian/Cyrillic text  
- **ATB** (Ukrainian supermarket) - Ukrainian/Cyrillic text

## Running Tests Locally

```bash
# Load environment variables
export $(< .env)

# Run the test suite
./test.sh
```

## Monitoring Test Results

After each workflow run:
1. Go to the **Actions** tab in your repository
2. Click on the workflow run
3. Check the test output in the logs
4. Download test artifacts if needed (includes test images and results)