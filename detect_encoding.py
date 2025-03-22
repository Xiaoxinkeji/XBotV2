import chardet
import sys

def detect_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    print(f"File: {file_path}")
    print(f"Detected encoding: {result['encoding']} with confidence: {result['confidence']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        detect_file_encoding(file_path)
    else:
        print("Usage: python detect_encoding.py <file_path>") 