import sys
import time
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode, PictureItem

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0

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
        print("============ Converting PDF ============")

        result = converter.convert(submittedPDF)

        print(result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED))
        print("----------- File Converted to Markdown! --------------")
        file = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        with open("text.md", "w") as f:
            f.write(file)
        print(f"Look at file: text.md")



def validpdf(submittedFile):
    # check if the pdf is valid
    if submittedFile.endswith('pdf'):
        return True
    else:
        print("not a valid pdf")
        sys.exit(1)


if __name__ == "__main__":
    main()    
