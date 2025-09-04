#!/usr/bin/env python3

import argparse
import os
from typing import Optional
import logging

from PIL import Image
import pytesseract
import PyPDF2
from pdf2image import convert_from_path

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from langchain.chat_models import init_chat_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Pydantic
class ScannedDocumentMetadata(BaseModel):
    """Classified scanned document"""
    type: str = Field(description="type of the document: contract, application, receipt, mail, bill")
    merchant: Optional[str] = Field(description="For receipts and bills include the merchant name")
    place: Optional[str] = Field(description="Place where this document was created, if presented")
    date: Optional[str] = Field(description="Date in format YYYY-MM-DD when this document was created", optional=True)
    total: Optional[float] = Field(description="Total amount of the receipt", optional=True)
    sumary: str = Field(description="short summary of the document")
    short_description: str = Field(description="short 3 wordsdescription of the document")
    currency: Optional[str] = Field(description="Currency code (USD, EUR, RUB, etc.) that was used in the document", optional=True)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from the first three pages of a PDF, using OCR if necessary."""
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = min(3, len(reader.pages))
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                print(page_num, page_text)
                if page_text:
                    text += page_text
                else:
                    # Use pdf2image to convert page to image
                    images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
                    for image in images:
                        ocr_text = pytesseract.image_to_string(image, lang='eng')
                        text += ocr_text
    except Exception as e:
        logger.error(f"Could not extract text from PDF {pdf_path}: {e}")
    return text

def detect_available_model():
    """
    Automatically detect and return the best available model based on API keys.
    Priority: OpenRouter (DeepSeek R1 Distill Qwen-14B) > OpenRouter (GPT-OSS-20B) > Gemini > OpenAI
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    if openrouter_key:
        logger.info("Detected OPENROUTER_API_KEY, using OpenRouter DeepSeek R1 Distill Qwen-14B (free model)")
        return "openrouter:deepseek/deepseek-r1-distill-qwen-14b"
    elif gemini_key:
        logger.info("Detected GEMINI_API_KEY, using Google Gemini 2.5 Flash")
        return "google:gemini-2.5-flash"
    elif openai_key:
        logger.info("Detected OPENAI_API_KEY, using OpenAI GPT-5-mini")
        return "openai:gpt-5-mini"
    else:
        raise ValueError(
            "No API keys found. Please get a free API key from:\n"
            "  - OpenRouter (recommended for free): https://openrouter.ai/keys\n"
            "  - Gemini (Google's comprehensive): https://makersuite.google.com/app/apikey\n"
            "  - OpenAI (premium): https://platform.openai.com/api-keys"
        )

def get_llm(model_spec: str = None):
    """
    Create an LLM instance based on the model specification using init_chat_model.
    If no model_spec provided, automatically detect based on available API keys.
    Format: provider:model_name (e.g., "openai:gpt-5-mini", "google:gemini-2.5-flash")
    """
    if model_spec is None:
        model_spec = detect_available_model()

    provider, model_name = model_spec.split(":", 1)

    # Prepare kwargs for special configurations
    kwargs = {}

    if provider == "openai":
        # Check for custom API base URL
        base_url = os.environ.get("OPENAI_API_BASE")
        if base_url:
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
            kwargs["base_url"] = base_url
    elif provider == "openrouter":
        # OpenRouter uses OpenAI-compatible API with custom base URL
        kwargs["base_url"] = "https://openrouter.ai/api/v1"

    # Use init_chat_model to create the model instance
    return init_chat_model(
        model=model_name,
        model_provider=provider,
        temperature=0,
        **kwargs
    )

def main():
    parser_arg = argparse.ArgumentParser(
        description="Classify documents using Tesseract OCR + LangChain (structured output)."
    )
    parser_arg.add_argument("documents", nargs="+", help="List of document paths to process")
    parser_arg.add_argument(
        "--model",
        default=None,
        help="Model specification in format provider:model_name. If not specified, automatically detects based on available API keys. Examples:\n"
        "  • openai:gpt-5-mini\n"
        "  • google:gemini-2.5-flash\n"
        "  • openrouter:deepseek/deepseek-r1-distill-qwen-14b (default, free, excellent)\n"
        "  • openrouter:gpt-oss-20b (free GPT model)\n"
        "  • openrouter:meta-llama/llama-4 (latest Llama model)\n"
        "  • openrouter:meta-llama/llama-3.1-8b-instruct (free Llama model)"
    )
    args = parser_arg.parse_args()

    # Get LLM based on model specification
    try:
        # Store the actual model spec used (either provided or auto-detected)
        model_spec = args.model
        llm = get_llm(model_spec)
        # If model was auto-detected, get the actual spec
        if model_spec is None:
            model_spec = detect_available_model()
        logger.info(f"Using model: {model_spec}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return

    for document_path in args.documents:
        if not os.path.isfile(document_path):
            logger.info(f"File not found: {document_path}")
            continue

        text_extracted = ""
        if document_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            try:
                text_extracted = pytesseract.image_to_string(Image.open(document_path), lang='eng')
                logger.info(f"OCR result for {document_path}:{text_extracted}")
            except Exception as e:
                logger.error(f"Could not perform OCR on {document_path}: {e}")
                continue
        elif document_path.lower().endswith('.pdf'):
            text_extracted = extract_text_from_pdf(document_path)
            logger.info(f"PDF text extraction result for {document_path}:{text_extracted}")

        try:
            # For OpenRouter, try structured output first, fallback to unstructured if it fails
            if model_spec and model_spec.startswith("openrouter:"):
                try:
                    model_with_structured_output = llm.with_structured_output(ScannedDocumentMetadata)
                    classification_result = model_with_structured_output.invoke(f"Classify the following scanned document text\n<text>{text_extracted}</text>")
                    logger.info(f"Structured output result: {classification_result}")

                    # Check if structured output returned None
                    if classification_result is None:
                        raise ValueError("Structured output returned None")

                except Exception as e:
                    # Fallback to unstructured response for models that don't support structured output
                    logger.info(f"Structured output not supported: {e}, falling back to unstructured parsing")
                    response = llm.invoke(f"Classify the following scanned document text\n<text>{text_extracted}</text>\n\nReturn as JSON with these exact keys: type, merchant, place, date, total, summary, short_description, currency")

                    # Debug logging
                    logger.info(f"Raw response content: {response.content}")

                    # Try to parse JSON from response
                    import json
                    import re
                    try:
                        # Clean up the response content by removing markdown code blocks
                        content = response.content.strip()
                        content = re.sub(r'```\w*\n?', '', content, flags=re.DOTALL)
                        content = content.strip()

                        logger.info(f"Cleaned response content: {content}")

                        classification_result = ScannedDocumentMetadata.parse_raw(content)
                    except Exception as parse_error:
                        logger.info(f"JSON parsing failed: {parse_error}")
                        # Manual parsing from structured OCR
                        merchant = None
                        place = None
                        date = None
                        total = None
                        currency = "USD"

                        # Extract merchant from OCR (first non-empty line)
                        lines = [line.strip() for line in text_extracted.split('\n') if line.strip()]
                        if lines:
                            merchant = lines[0] if len(lines[0]) > 3 else None  # First line is usually merchant

                        # Extract date from various formats
                        for line in text_extracted.split('\n'):
                            # Try MM.DD.YYYY format
                            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', line)
                            if date_match:
                                date = f"{date_match.group(3)}-{date_match.group(2).zfill(2)}-{date_match.group(1).zfill(2)}"
                                break
                            # Try DD.MM.YYYY format
                            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', line)
                            if date_match:
                                date = f"{date_match.group(3)}-{date_match.group(2).zfill(2)}-{date_match.group(1).zfill(2)}"
                                break

                        # Extract total amount (usually the highest or last number with decimal)
                        total_match = re.search(r'(\d+\.\d{2})', text_extracted)
                        if total_match:
                            total = float(total_match.group(1))

                        classification_result = ScannedDocumentMetadata(
                            type="receipt",
                            merchant=merchant,
                            place=place,
                            date=date,
                            total=total,
                            sumary=f"Purchase receipt from {merchant}" if merchant else "Processed document",
                            short_description=f"{" ".join(merchant.split()[:2])} receipt" if merchant else "receipt",
                            currency=currency
                        )
            else:
                model_with_structured_output = llm.with_structured_output(ScannedDocumentMetadata)
                classification_result = model_with_structured_output.invoke(f"Classify the following scanned document text\n<text>{text_extracted}</text>")
            logger.info(f"{classification_result}")

            _, file_extension = os.path.splitext(document_path)
            if classification_result.type == "receipt":
                new_filename = f"{classification_result.date}_{classification_result.type}_{classification_result.merchant}_{classification_result.place}_{classification_result.total}{classification_result.currency}{file_extension}"
            else:
                new_filename = f"{classification_result.date}_{classification_result.type}_{classification_result.short_description}{file_extension}"

            if new_filename:
                directory = os.path.dirname(document_path)
                new_path = os.path.join(directory, new_filename)
                
                if os.path.exists(new_path):
                    logger.info(f"Warning: {new_path} already exists. Skipping rename.")
                else:
                    os.rename(document_path, new_path)
                    logger.info(f"Renamed '{document_path}' to '{new_path}'")
            else:
                logger.info("No 'new_document_name' found. Skipping rename.")

        except Exception as e:
            logger.error(f"Classification failed for {document_path}: {e}")
            logger.exception(e)


if __name__ == "__main__":
    main()
