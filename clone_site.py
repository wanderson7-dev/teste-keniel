import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://chocoburn1fr.online/ztes1-fquiz-pit32-pag/"
INPUT_FILE = "index_raw.html"
OUTPUT_FILE = "index.html"
ASSETS_DIR = "assets"

def download_file(url, local_path):
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {url} -> {local_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def process_html():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Process CSS
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            full_url = urljoin(BASE_URL, href)
            # Determine local path
            if href.startswith('http'):
                # External CDN, maybe keep as is or download?
                # For this task, let's try to download everything to be safe, 
                # unless it's a font CDN which might be complex.
                # Let's verify if it's a relative path in the original site structure
                parsed = urlparse(href)
                filename = os.path.basename(parsed.path)
                if not filename.endswith('.css'):
                    filename += '.css'
                local_path = os.path.join(ASSETS_DIR, 'css', filename)
            else:
                # Relative path
                # Clean up path to avoid 'assets/pages/...' deep nesting if possible, OR keep structure.
                # Let's keep structure to be safe with relative imports inside CSS.
                # Actually, simplest is to flatten or keep specific structure.
                # The user wants "exact replica". 
                # Let's mirror the path structure for relative paths to avoid breaking things.
                local_path = href # Keep the relative path structure
                # But we need to make sure we're not writing outside project
                if local_path.startswith('/'): local_path = local_path[1:]
            
            # Download
            if download_file(full_url, local_path):
                link['href'] = local_path

    # Process Images
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            full_url = urljoin(BASE_URL, src)
            local_path = src
            if local_path.startswith('/'): local_path = local_path[1:]
            
            if download_file(full_url, local_path):
                img['src'] = local_path

    # Process Scripts
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            full_url = urljoin(BASE_URL, src)
            # Skip tracking/analytics scripts? 
            # The prompt says "copie exatamente igual". 
            # But tracking scripts might not work or be desired.
            # However, I will download them if they are local assets.
            # If they are external (facebook, google, etc), keep them as is?
            # "copy this site exactly as it is".
            # I will download relative scripts. External scripts I will leave as links.
            
            if not src.startswith('http') and not src.startswith('//'):
                 local_path = src
                 if local_path.startswith('/'): local_path = local_path[1:]
                 if download_file(full_url, local_path):
                     script['src'] = local_path

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Done processing HTML.")

if __name__ == "__main__":
    process_html()
