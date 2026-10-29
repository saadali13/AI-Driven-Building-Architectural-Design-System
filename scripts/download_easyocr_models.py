import os
import zipfile
import requests

def download_file(url, target_path):
    print(f"Downloading {url} -> {target_path}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, stream=True, timeout=60)
    r.raise_for_status()
    with open(target_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {os.path.getsize(target_path)} bytes.")

def main():
    model_dir = os.path.expanduser('~/.EasyOCR/model')
    os.makedirs(model_dir, exist_ok=True)
    
    # 1. Detection model (CRAFT)
    craft_zip = os.path.join(model_dir, 'craft_mlt_25k.zip')
    craft_pth = os.path.join(model_dir, 'craft_mlt_25k.pth')
    if not os.path.exists(craft_pth):
        craft_url = 'https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip'
        download_file(craft_url, craft_zip)
        with zipfile.ZipFile(craft_zip, 'r') as zf:
            zf.extractall(model_dir)
        print("Extracted CRAFT model.")
        
    # 2. English recognition model
    rec_zip = os.path.join(model_dir, 'english_g2.zip')
    rec_pth = os.path.join(model_dir, 'english_g2.pth')
    if not os.path.exists(rec_pth):
        rec_url = 'https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip'
        download_file(rec_url, rec_zip)
        with zipfile.ZipFile(rec_zip, 'r') as zf:
            zf.extractall(model_dir)
        print("Extracted English recognition model.")
        
    print("EasyOCR models ready in", model_dir)

if __name__ == '__main__':
    main()
