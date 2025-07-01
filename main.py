import sys
import time
import logging
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 0.5

output_dir = Path("scratch")

_log = logging.getLogger(__name__)

def main():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    if len(sys.argv) < 2:
        print("Usage: python3 main.py <file-to-submit>.pdf")
        sys.exit(1)

    else: 
        submittedPDF = sys.argv[1]
        start_time = time.time()
        print("============ Converting PDF ============")
        result = converter.convert(submittedPDF)

        file = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)

        _log.info("----------- File Converted to Markdown! --------------")
        
        with open("text.md", "w") as f:
            _log.info("Writing markdown file to text.md")
            f.write(file)
        _log.info(f"Look at file: text.md")
        end_time = time.time()
        _log.info(f"Time taken: {end_time - start_time} seconds")


def validpdf(submittedFile):
    # check if the pdf is valid
    if submittedFile.endswith('pdf'):
        return True
    else:
        print("not a valid pdf")
        sys.exit(1)


if __name__ == "__main__":
    main()    
