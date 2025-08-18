#!/usr/bin/env python3

import argparse
import os
from typing import Optional
import logging

from PIL import Image
import pytesseract

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Pydantic
class ScannedDocumentMetadata(BaseModel):
    """Classified scanned document"""
    file_name: str = Field(description="A document file name without extension. Includes the date if preseneted in the document text, type of document, short summary of document and place.")
    type: str = Field(description="type of the document: contract, application, receipt, mail, bill")
    merchant: Optional[str] = Field(description="For receipts and bills include the merchant name")
    place: Optional[str] = Field(description="Place where this document was created, if presented")
    date: Optional[str] = Field(description="Date when this document was created in format YYYY-MM-DD if available")
    total: Optional[float] = Field(description="Total amount of the receipt")
    sumary: str = Field(description="short summary of the document")

def get_llm(model_spec: str = "google:gemini-2.5-flash"):
    """
    Create an LLM instance based on the model specification.
    Format: provider:model_name (e.g., "openai:gpt-4o", "google:gemini-2.5-flash")
    """
    provider, model_name = model_spec.split(":", 1)
    
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        # Check for custom API base URL
        base_url = os.environ.get("OPENAI_API_BASE")
        if base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        return ChatOpenAI(
            temperature=0,
            openai_api_key=api_key,
            model_name=model_name,
            base_url=base_url if base_url else None
        )
    elif provider == "google":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

def main():
    parser_arg = argparse.ArgumentParser(
        description="Classify documents using Tesseract OCR + LangChain (structured output)."
    )
    parser_arg.add_argument("images", nargs="+", help="List of image paths to process")
    parser_arg.add_argument(
        "--model", 
        default="google:gemini-2.5-flash",
        help="Model specification in format provider:model_name (e.g., openai:gpt-4o, google:gemini-2.5-flash)"
    )
    args = parser_arg.parse_args()

    # Get LLM based on model specification
    try:
        llm = get_llm(args.model)
        logger.info(f"Using model: {args.model}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return


    for image_path in args.images:
        if not os.path.isfile(image_path):
            logger.info(f"File not found: {image_path}")
            continue

        try:
            # Example: using Russian (lang='rus'), change to 'eng' or other if needed
            text_extracted = pytesseract.image_to_string(Image.open(image_path), lang='rus')
            logger.info(f"OCR result for {image_path}:{text_extracted}")
        except Exception as e:
            logger.error(f"Could not perform OCR on {image_path}: {e}")
            continue

        try:
            # it doesn't work for some reason https://genai.stackexchange.com/questions/2188/llm-with-structured-output-notimplementederror
            model_with_structured_output = llm.with_structured_output(ScannedDocumentMetadata)
            classification_result = model_with_structured_output.invoke(f"Classify the following scanned document text\n<text>{text_extracted}</text>")
            print(classification_result)

            logger.info(f"{classification_result}")

            # 3) Rename the file based on 'file_name' field
            new_filename = classification_result.file_name
            if new_filename:
                directory = os.path.dirname(image_path)
                # Get the original file extension
                _, ext = os.path.splitext(image_path)
                new_path = os.path.join(directory, new_filename + ext)
                
                if os.path.exists(new_path):
                    logger.info(f"Warning: {new_path} already exists. Skipping rename.")
                else:
                    os.rename(image_path, new_path)
                    logger.info(f"Renamed '{image_path}' to '{new_path}'")
            else:
                logger.info("No 'file_name' found. Skipping rename.")

        except Exception as e:
            logger.error(f"Classification failed for {image_path}: {e}")
            logger.exception(e)


if __name__ == "__main__":
    main()
