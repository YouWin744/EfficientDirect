import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

output_dir = "csv_downloads"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

index_url = "https://www.math.mun.ca/distanceregular/indexes/upto50vertices.html"
csv_base_url = "https://www.math.mun.ca/distanceregular/graphdata/"


def download_file(url, save_path, filename_hint):
    try:
        file_response = requests.get(url)
        if file_response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(file_response.content)
            print(f"Successfully downloaded {filename_hint} from {url}")
            return True
        else:
            print(
                f"HTTP {file_response.status_code} for {filename_hint} at {url}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request error for {filename_hint} at {url}: {e}")
        return False
    except Exception as e:
        print(f"Error saving {filename_hint}: {e}")
        return False


try:
    response = requests.get(index_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    for link in soup.find_all('a'):
        href = link.get('href')

        if href and 'graphs/' in href and href.endswith('.html'):

            slug = href.split('/')[-1].replace('.html', '')
            csv_filename = f"{slug}.am.csv"

            # Phase 1: Try the direct URL construction method
            csv_url_direct = f"{csv_base_url}{csv_filename}"
            save_path = os.path.join(output_dir, csv_filename)

            print(
                f"Attempting direct download for {csv_filename} from {csv_url_direct}...")

            if download_file(csv_url_direct, save_path, csv_filename):
                continue  # Success, move to the next graph

            # Phase 2: Fallback to accessing the graph page and scraping the link
            print(
                f"Direct download failed/skipped. Falling back to scraping {slug}'s page...")

            graph_page_url = urljoin(index_url, href)

            try:
                graph_response = requests.get(graph_page_url)
                graph_response.raise_for_status()
                graph_soup = BeautifulSoup(
                    graph_response.content, 'html.parser')

                csv_link_tag = graph_soup.find(
                    'a', string='Adjacency matrix in CSV format')

                if csv_link_tag:
                    csv_relative_href = csv_link_tag.get('href')
                    csv_url_fallback = urljoin(
                        graph_page_url, csv_relative_href)

                    # Get the correct filename from the fallback URL in case it differs slightly
                    fallback_filename = os.path.basename(csv_url_fallback)
                    save_path_fallback = os.path.join(
                        output_dir, fallback_filename)

                    print(
                        f"Attempting fallback download for {fallback_filename} from {csv_url_fallback}...")

                    if not download_file(csv_url_fallback, save_path_fallback, fallback_filename):
                        print(
                            f"Fallback download failed for {fallback_filename}.")

                else:
                    print(f"Failed to find CSV link on page {graph_page_url}.")

            except requests.exceptions.RequestException as e:
                print(f"Error accessing graph page {graph_page_url}: {e}")
            except Exception as e:
                print(f"Error during fallback scraping for {slug}: {e}")

except Exception as e:
    print(f"Fatal error: {e}")
