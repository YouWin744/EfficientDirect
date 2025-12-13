import os
import requests
from bs4 import BeautifulSoup

output_dir = "csv_downloads"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

index_url = "https://www.math.mun.ca/distanceregular/indexes/upto50vertices.html"
csv_base_url = "https://www.math.mun.ca/distanceregular/graphdata/"

try:
    response = requests.get(index_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    for link in soup.find_all('a'):
        href = link.get('href')
        
        if href and 'graphs/' in href and href.endswith('.html'):
            slug = href.split('/')[-1].replace('.html', '')
            csv_filename = f"{slug}.am.csv"
            csv_url = f"{csv_base_url}{csv_filename}"
            save_path = os.path.join(output_dir, csv_filename)

            try:
                print(f"Downloading {csv_url} ...")
                file_response = requests.get(csv_url)
                
                if file_response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(file_response.content)
                else:
                    print(f"Skipping {slug}: HTTP {file_response.status_code}")
            except Exception as e:
                print(f"Error processing {slug}: {e}")

except Exception as e:
    print(f"Fatal error: {e}")