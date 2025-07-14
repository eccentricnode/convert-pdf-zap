import sys
sys.path.append('.')
from converters import SimplePyMuPDFConverter

if __name__ == '__main__':
    print('SimplePyMuPDFConverter test:')
    converter = SimplePyMuPDFConverter()
    converter_info = converter.get_converter_info()
    print(f'Name: {converter_info["name"]}')
    print(f'Features: {converter_info["features"]}')
    print(f'Limitations: {converter_info["limitations"]}')
    print('✓ Simple PyMuPDF Converter loaded successfully!')
