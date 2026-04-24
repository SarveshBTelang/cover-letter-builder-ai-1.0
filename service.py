"""
Service module for generating cover letters based on user input and a template. This module handles the main logic of extracting job context, generating the letter body using an LLM, decrypting the template, styling the document, and converting it to PDF format. It also includes a progress bar to provide real-time feedback during the generation process.

Author: Sarvesh Telang
"""


import os
from docx import Document
from pathlib import Path
import subprocess
from tqdm import tqdm
from fastapi import HTTPException
import msoffcrypto
import io
import asyncio
import boto3

from generate_response import generate_cover_letter_body, extract_job_context

# ---------- R2 CONFIG ----------
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET = os.getenv("R2_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

def normalize_value(value):
    if isinstance(value, (tuple, list)):
        return value[0]
    return value

def upload_to_r2(file_path: Path, key: str):
    try:
        s3.upload_file(
            Filename=str(file_path),
            Bucket=R2_BUCKET,
            Key=key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"R2 upload failed: {str(e)}")

async def progress_bar(send, total_steps):
    current = 0

    async def update(step_msg=""):
        nonlocal current
        current += 1
        percent = int((current / total_steps) * 100)
        bar = "█" * (percent // 10) + "-" * (10 - percent // 10)
        await send(f"[{bar}] {percent}% {step_msg}")

    return update


async def generate_letter(config, log=None):
    async def send(msg):
        if log:
            await log(msg)
        else:
            print(msg)

    total_steps = 6
    update = await progress_bar(send, total_steps)

    # Step 1
    await update("Extracting job context and instructions...")
    extract_job_context(config)
    await asyncio.sleep(1)

    # Step 2
    await update("Generating LLM response...")
    body = generate_cover_letter_body(config)
    body = body.replace("*", "")

    try:
        # Step 3
        await update("Decrypting template...")
        decrypted = io.BytesIO()

        with open(config["TEMPLATE_PATH"], "rb") as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=config["ACCESS_KEY"])
            office_file.decrypt(decrypted)

    except msoffcrypto.exceptions.InvalidKeyError:
        await send("❌ Incorrect access key!!! ")
        await send(f"(Entered key: {config['ACCESS_KEY']})")

    decrypted.seek(0)
    doc = Document(decrypted)

    # Step 4
    await update("Styling document...")
    replacements = {
        "FIRM": normalize_value(config["FIRM"]),
        "LOCATION": normalize_value(config["LOCATION"]),
        "DATE": normalize_value(config["DATE"]),
        "POSITION": normalize_value(config["POSITION"]),
        "GREETING": normalize_value(config["GREETING"]),
        "BODY": body
    }

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            for key, value in replacements.items():
                if key in run.text:
                    run.text = run.text.replace(key, value)
    
    await asyncio.sleep(1)

    # Step 5
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    docx_path = output_dir / f"{config['OUTPUT_FILE_NAME']}.docx"
    doc.save(docx_path)

    r2_docx_key = f"docx/{docx_path.name}"
    upload_to_r2(docx_path, r2_docx_key)

    # Step 6
    await update("Converting to PDF...")
    subprocess.run([
        config["LIBREOFFICE_PATH"],
        "--headless",
        "--convert-to", "pdf",
        str(docx_path),
        "--outdir", str(output_dir)
    ], check=True)

    return docx_path.with_suffix(".pdf"), docx_path