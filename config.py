"""
Setup default configuration values for the cover letter generation process, including job details, template paths, and other parameters. 

This configuration can be overridden by user input when the application is run.

Author: Sarvesh Telang
"""

import os
from datetime import datetime
import pytz

def get_default_config():
    """Returns a dictionary containing default configuration values for the cover letter generation process."""

    config = {
        "ACCESS_KEY": "ml",
        "FIRM": "Robert Bosch GmbH",
        "LOCATION": "Stuttgart, Deutschland",
        "POSITION": "Machine Learning Engineer Position",
        "GREETING": "Hiring Manager",
        "JOB_DESCRIPTION" : """ YOUR ROLE Machine Learning Applications: You will develop modern, scalable machine learning solutions on the Google Cloud.

        Deployment: You use Python to integrate machine learning models into production-ready data pipelines.

        Customized solutions: You efficiently translate customer requirements into tailored machine learning solutions.

        Google Cloud: You work with Google Cloud products and frameworks such as TensorFlow, PyTorch or scikit-learn.

        Software architecture: You will contribute to the design and consulting for component-based software architectures.

        Programming skills: You are proficient in Python and other common technologies. """,
        "BODY_WORD_COUNT": "180",
        "TIMEZONE": "Europe/Berlin",                                                                                  
        "TEMPLATE_PATH": "src/template.docx",
        "OUTPUT_FILE_NAME": "Cover_Letter_Sarvesh_Telang",
        "LIBREOFFICE_PATH": "/usr/bin/soffice",  # Render path
        #"LIBREOFFICE_PATH" : r"C:\Program Files\LibreOffice\program\soffice.exe", # Local path for testing (Windows)
    }

    get_timezone = pytz.timezone(config["TIMEZONE"])

    config["DATE"] = datetime.now(get_timezone).strftime("%d %B %Y"),

    return config