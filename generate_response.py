"""
Module for generating cover letter body text using a language model. This module reads instructions and context from Cloudflare R2 storage, constructs a prompt, and sends it to the desired LLM API to generate the body of a cover letter. The generated text is then returned as a string.

Configure custom LLM API integration by modifying the `generate_cover_letter_body` function to use the appropriate API client and request format. The current implementation is set up for Mistral, but can be adapted for other LLM providers as needed.

"""

import os
from pathlib import Path
import boto3
from dotenv import load_dotenv

# ---------- LOAD ENV ----------
load_dotenv()

# ---------------- MISTRAL ----------------
from mistralai.client import Mistral

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in .env file")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)
MISTRAL_MODEL = "mistral-large-latest"

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

# ---------- IMPORT CONFIG ----------
import config


# ---------- FILE HELPERS ----------
def read_folder_text(folder_path: str) -> str:
    folder = Path(folder_path)
    combined_text = []

    for file in sorted(folder.glob("*.txt")):
        with open(file, "r", encoding="utf-8") as f:
            combined_text.append(f"\n### {file.name} ###\n")
            combined_text.append(f.read())

    return "\n".join(combined_text)


def read_r2_folder(prefix: str) -> str:
    response = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix)

    if "Contents" not in response:
        return ""

    combined_text = []

    for obj in sorted(response["Contents"], key=lambda x: x["Key"]):
        key = obj["Key"]

        file_obj = s3.get_object(Bucket=R2_BUCKET, Key=key)
        content = file_obj["Body"].read().decode("utf-8")

        filename = key.split("/")[-1]
        combined_text.append(f"\n### {filename} ###\n")
        combined_text.append(content)

    return "\n".join(combined_text)


# ---------- NEW HELPER: UPLOAD TO R2 ----------
def upload_text_to_r2(key: str, content: str):
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain"
    )


# ---------- UPDATED FUNCTION ----------
def extract_job_context(config):
    # Build content as string instead of writing locally
    content = (
        f"Firm: {config['FIRM']}\n"
        f"Location: {config['LOCATION']}\n"
        f"Today's Date: {config['DATE']}\n"
        f"Position: {config['POSITION']}\n"
        f"Job Description: {config['JOB_DESCRIPTION']}\n"
    )

    # Upload directly to R2
    upload_text_to_r2("context/job_context.txt", content)


# ---------- MAIN GENERATION ----------
def generate_cover_letter_body(
    config,
    instructions_folder="instructions",
    context_folder="context",
) -> str:

    # Read from R2 instead of local
    instructions_text = read_r2_folder("instructions/")
    context_text = read_r2_folder("context/")

    prompt = f"""
Write a professional cover letter BODY paragraph.

RULES:
- Only output the BODY text (no subject, no greeting, no signature)
- Assume the greeting as "Dear Hiring Manager"
- Keep it concise ({config['BODY_WORD_COUNT']} words) but ensure it doesn't cut off.
- Strictly use the provided instructions and context
- Avoid generic phrases
- Today's date is {config['DATE']}

--- INSTRUCTIONS ---
{instructions_text}

--- CONTEXT ---
{context_text}

Now generate the response:
"""

    print(prompt)

    response = mistral_client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content.strip()