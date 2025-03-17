import os
import re
import json
import datetime
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pytz
import markdown
from bs4 import BeautifulSoup

import requests
import pandas as pd


class TidyTuesdayPy:
    """Main class for TidyTuesdayPy package."""
    
    GITHUB_API_URL = "https://api.github.com/repos/rfordatascience/tidytuesday/contents/data"
    RAW_GITHUB_URL_MASTER = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data"
    RAW_GITHUB_URL_MAIN = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data"
    RAW_GITHUB_URL_REFS_MAIN = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/refs/heads/main/data"
    
    def __init__(self):
        """Initialize the TidyTuesdayPy class."""
        self.rate_limit_remaining = None
        self._update_rate_limit()
    
    def _update_rate_limit(self):
        """Check GitHub API rate limit."""
        try:
            response = requests.get("https://api.github.com/rate_limit")
            response.raise_for_status()  # Raises HTTPError for bad responses
            data = response.json()
            self.rate_limit_remaining = data["resources"]["core"]["remaining"]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rate limit: {e}")
            self.rate_limit_remaining = None
    

    def rate_limit_check(self, quiet: bool = False) -> Optional[int]:
        """
        Check the GitHub API rate limit.
        
        Args:
            quiet: If True, don't print rate limit info
            
        Returns:
            Number of requests remaining, or None if unable to check
        """
        self._update_rate_limit()
        
        if not quiet and self.rate_limit_remaining is not None:
            print(f"Requests remaining: {self.rate_limit_remaining}")
        
        return self.rate_limit_remaining

    def last_tuesday(self, date: Optional[Union[str, datetime.datetime]] = None) -> str:
        """
        Find the most recent Tuesday relative to a specified date.
        
        Args:
            date: A date string in YYYY-MM-DD format or a datetime object. Defaults to today's date in New York time.
            
        Returns:
            The TidyTuesday date in the same week as the specified date
        """
        if date is None:
            ny_tz = pytz.timezone('America/New_York')
            date_obj = datetime.datetime.now(ny_tz)
        elif isinstance(date, str):
            try:
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        elif isinstance(date, datetime.datetime):
            date_obj = date
        else:
            raise TypeError("Date must be a string in YYYY-MM-DD format or a datetime object")
        
        days_since_tuesday = (date_obj.weekday() - 1) % 7
        last_tues = date_obj - datetime.timedelta(days=days_since_tuesday)
        
        return last_tues.strftime("%Y-%m-%d")


    def tt_available(self) -> Dict[str, List[Dict[str, str]]]:
        """
        List all available TidyTuesday datasets across all years.
        
        Returns:
            Dictionary with years as keys and lists of datasets as values
        """
        remaining = self.rate_limit_check(quiet=True)
        if remaining is not None and remaining == 0:
            print("GitHub API rate limit exhausted. Try again later.")
            return {}
        
        try:
            response = requests.get(self.GITHUB_API_URL)
            response.raise_for_status()
            years_data = response.json()
            years = [item["name"] for item in years_data if item["type"] == "dir"]
            
            all_datasets = {}
            for year in years:
                datasets = self.tt_datasets(year, print_output=False)
                all_datasets[year] = datasets
            
            # Printing separated for clarity; could be made optional with a parameter
            print("Available TidyTuesday Datasets:")
            print("==============================")
            for year, datasets in all_datasets.items():
                print(f"\n{year}:")
                for dataset in datasets:
                    print(f"  {dataset['date']} - {dataset['title']}")
            
            return all_datasets
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching years: {e}")
            return {}

    
    def tt_datasets(self, year: Union[str, int], print_output: bool = True) -> List[Dict[str, str]]:
        """
        List available TidyTuesday datasets for a specific year.
        
        Args:
            year: The year to get datasets for
            print_output: Whether to print the results
            
        Returns:
            List of dictionaries with dataset information
        """
        remaining = self.rate_limit_check(quiet=True)
        if remaining is not None and remaining == 0:
            print("GitHub API rate limit exhausted. Try again later.")
            return []
        
        try:
            year = str(year)
            
            # First try to get the HTML version of the year's main readme.md file
            # Note: GitHub uses 'main' as the default branch name now, not 'master'
            html_url = f"https://github.com/rfordatascience/tidytuesday/blob/main/data/{year}/readme.md"
            try:
                html_response = requests.get(html_url)
                
                # If 'main' branch doesn't work, try 'master' branch as fallback
                if html_response.status_code != 200:
                    html_url = f"https://github.com/rfordatascience/tidytuesday/blob/master/data/{year}/readme.md"
                    html_response = requests.get(html_url)
                
                datasets = []
                
                if html_response.status_code == 200:
                    # Parse the HTML with BeautifulSoup
                    soup = BeautifulSoup(html_response.text, 'html.parser')
                    
                    # Find the table in the readme
                    tables = soup.find_all('table')
                    if tables:
                        # Get the first table
                        table = tables[0]
                        
                        # Extract rows from the table
                        rows = table.find_all('tr')
                        
                        # Skip the header row
                        for row in rows[1:]:
                            cells = row.find_all(['td', 'th'])
                            
                            # Make sure we have enough cells
                            if len(cells) >= 3:
                                # Extract date and title
                                date_cell = cells[1].text.strip()
                                title_cell = cells[2].text.strip()
                                
                                # Make sure date is in the correct format
                                if re.match(r"^\d{4}-\d{2}-\d{2}$", date_cell):
                                    datasets.append({
                                        "date": date_cell,
                                        "title": title_cell,
                                        "path": f"{year}/{date_cell}"
                                    })
                
                # If no datasets found from HTML parsing, fall back to API
                if not datasets:
                    url = f"{self.GITHUB_API_URL}/{year}"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    folders = [item for item in data if item["type"] == "dir"]
                    
                    for folder in folders:
                        week_name = folder["name"]
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", week_name):
                            date = week_name
                            datasets.append({
                                "date": date,
                                "title": "Unknown",  # Default title
                                "path": f"{year}/{date}"
                            })
            
            except requests.exceptions.RequestException:
                # Fallback to API if HTML parsing fails
                url = f"{self.GITHUB_API_URL}/{year}"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                folders = [item for item in data if item["type"] == "dir"]
                
                datasets = []
                for folder in folders:
                    week_name = folder["name"]
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", week_name):
                        date = week_name
                        datasets.append({
                            "date": date,
                            "title": "Unknown",  # Default title
                            "path": f"{year}/{date}"
                        })
            
            # Sort datasets by date
            datasets.sort(key=lambda x: x["date"])
            
            if print_output:
                print(f"Available TidyTuesday Datasets for {year}:")
                print("======================================")
                for dataset in datasets:
                    print(f"{dataset['date']} - {dataset['title']}")
            
            return datasets
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching datasets for year {year}: {e}")
            return []
    
    def _get_dataset_metadata(self, date: str) -> Dict[str, Any]:
        """
        Get metadata for a TidyTuesday dataset by date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Dictionary with dataset metadata
        """
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            print(f"Invalid date format: {date}. Use YYYY-MM-DD format.")
            return {}
        
        year = date[:4]
        
        try:
            # Get files for the week
            url = f"{self.GITHUB_API_URL}/{year}/{date}"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Error fetching data for {date}: {response.status_code}")
                return {}
            
            files_data = response.json()
            files = []
            
            for item in files_data:
                if item["type"] == "file" and not item["name"].lower().startswith("readme"):
                    files.append({
                        "name": item["name"],
                        "download_url": item["download_url"],
                        "path": item["path"]
                    })
            
            # Get README content - try different URL patterns
            readme_urls = [
                f"{self.RAW_GITHUB_URL_REFS_MAIN}/{year}/{date}/readme.md",  # refs/heads/main with lowercase readme
                f"{self.RAW_GITHUB_URL_REFS_MAIN}/{year}/{date}/README.md",  # refs/heads/main with uppercase README
                f"{self.RAW_GITHUB_URL_MAIN}/{year}/{date}/readme.md",       # main with lowercase readme
                f"{self.RAW_GITHUB_URL_MAIN}/{year}/{date}/README.md",       # main with uppercase README
                f"{self.RAW_GITHUB_URL_MASTER}/{year}/{date}/readme.md",     # master with lowercase readme
                f"{self.RAW_GITHUB_URL_MASTER}/{year}/{date}/README.md"      # master with uppercase README
            ]
            
            readme_response = None
            readme_url = None
            
            for url in readme_urls:
                print(f"Trying to fetch README from: {url}")
                response = requests.get(url)
                if response.status_code == 200:
                    readme_response = response
                    readme_url = url
                    print(f"Successfully fetched README from: {url}")
                    break
            
            readme_content = readme_response.text if readme_response is not None else ""
            
            # Create HTML version of README for display
            readme_html = self._markdown_to_html(readme_content)
            
            return {
                "date": date,
                "year": year,
                "files": files,
                "readme_content": readme_content,
                "readme_html": readme_html
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def tt_download_file(self, date: str, file_name: str, save_to_disk: bool = True, verbose: bool = True) -> Optional[pd.DataFrame]:
        """
        Download a specific file from a TidyTuesday dataset by date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            file_name: Name of the file to download
            save_to_disk: Whether to save the file to disk
            verbose: If True, print download progress
            
        Returns:
            A pandas DataFrame with the file contents if save_to_disk is False,
            otherwise None (file is saved to disk)
        """
        # Get dataset metadata
        metadata = self._get_dataset_metadata(date)
        
        if not metadata or "files" not in metadata:
            if verbose:
                print(f"No dataset found for date {date}")
            return None
        
        try:
            # Find the file
            file_info = next((f for f in metadata["files"] if f["name"] == file_name), None)
            if not file_info:
                if verbose:
                    print(f"File '{file_name}' not found in dataset for {date}")
                    print("Available files:")
                    for f in metadata["files"]:
                        print(f"  {f['name']}")
                return None
            
            if verbose:
                print(f"Downloading {file_info['name']}...")
            
            response = requests.get(file_info["download_url"])
            response.raise_for_status()
            
            file_name_lower = file_info["name"].lower()
            
            if save_to_disk:
                # Save to disk
                with open(file_info["name"], "wb") as f:
                    f.write(response.content)
                
                if verbose:
                    print(f"Successfully saved {file_info['name']} to {os.path.abspath(file_info['name'])}")
                return None
            else:
                # Return as DataFrame
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name_lower)[1]) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                try:
                    if file_name_lower.endswith('.csv'):
                        df = pd.read_csv(tmp_path)
                    elif file_name_lower.endswith('.tsv'):
                        df = pd.read_csv(tmp_path, sep='\t')
                    elif file_name_lower.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(tmp_path)
                    elif file_name_lower.endswith('.json'):
                        df = pd.read_json(tmp_path)
                    elif file_name_lower.endswith('.parquet'):
                        df = pd.read_parquet(tmp_path)
                    else:
                        if verbose:
                            print(f"Unsupported file format: {file_name_lower}")
                        return None
                finally:
                    os.unlink(tmp_path)
                
                if verbose:
                    print(f"Successfully loaded {file_info['name']}")
                return df
            
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Error downloading file: {e}")
            return None
        except pd.errors.ParserError as e:
            if verbose:
                print(f"Error parsing file: {e}")
            return None
    
    def tt_download(self, date: str, files: Union[str, List[str]] = "All", save_to_disk: bool = True, verbose: bool = True) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Download files from a TidyTuesday dataset by date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            files: Either "All" to download all files, or a list of file names
            save_to_disk: Whether to save the files to disk
            verbose: If True, print download progress
            
        Returns:
            Dictionary mapping file names to pandas DataFrames if save_to_disk is False,
            otherwise None (files are saved to disk)
        """
        # Get dataset metadata
        metadata = self._get_dataset_metadata(date)
        
        if not metadata or "files" not in metadata:
            if verbose:
                print(f"No dataset found for date {date}")
            return None
        
        try:
            available_files = metadata["files"]
            
            if files == "All":
                files_to_download = available_files
            else:
                if isinstance(files, str):
                    files = [files]
                
                files_to_download = []
                for file_name in files:
                    file_info = next((f for f in available_files if f["name"] == file_name), None)
                    if file_info:
                        files_to_download.append(file_info)
                    else:
                        print(f"Warning: File '{file_name}' not found")
                        print("Available files:")
                        for f in available_files:
                            print(f"  {f['name']}")
            
            if save_to_disk:
                # Save files to disk
                for file_info in files_to_download:
                    file_name = file_info["name"]
                    if verbose:
                        print(f"Downloading {file_name}...")
                    
                    response = requests.get(file_info["download_url"])
                    
                    if response.status_code != 200:
                        print(f"Error downloading {file_name}: {response.status_code}")
                        continue
                    
                    with open(file_name, "wb") as f:
                        f.write(response.content)
                    
                    if verbose:
                        print(f"Successfully saved {file_name} to {os.path.abspath(file_name)}")
                
                return None
            else:
                # Return as DataFrames
                result = {}
                for file_info in files_to_download:
                    file_name = file_info["name"]
                    if verbose:
                        print(f"Downloading {file_name}...")
                    
                    response = requests.get(file_info["download_url"])
                    
                    if response.status_code != 200:
                        print(f"Error downloading {file_name}: {response.status_code}")
                        continue
                    
                    # Save to a temporary file first
                    file_name_lower = file_name.lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name_lower)[1]) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    
                    # Read the file based on its extension
                    try:
                        if file_name_lower.endswith('.csv'):
                            df = pd.read_csv(tmp_path)
                        elif file_name_lower.endswith('.tsv'):
                            df = pd.read_csv(tmp_path, sep='\t')
                        elif file_name_lower.endswith(('.xls', '.xlsx')):
                            df = pd.read_excel(tmp_path)
                        elif file_name_lower.endswith('.json'):
                            df = pd.read_json(tmp_path)
                        elif file_name_lower.endswith('.parquet'):
                            df = pd.read_parquet(tmp_path)
                        else:
                            print(f"Unsupported file format: {file_name}")
                            continue
                        
                        # Store in result dictionary, using the name without extension as the key
                        key = os.path.splitext(file_name)[0]
                        result[key] = df
                        if verbose:
                            print(f"Successfully loaded {file_name}")
                        
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
                    
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_path)
                
                return result
            
        except Exception as e:
            print(f"Error downloading files: {e}")
            return None
    
    def readme(self, date: str) -> None:
        """
        Display the README for a TidyTuesday dataset by date.
        
        Args:
            date: Date string in YYYY-MM-DD format
        """
        # Get dataset metadata
        metadata = self._get_dataset_metadata(date)
        
        if not metadata or "readme_html" not in metadata or not metadata["readme_content"]:
            print(f"No README available for dataset {date}")
            return
        
        # Create a temporary HTML file and open it in the browser
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as tmp:
            tmp.write(metadata["readme_html"])
            tmp_path = tmp.name
        
        webbrowser.open(f"file://{tmp_path}")
        print(f"README for {date} opened in your browser.")
        print(f"README content length: {len(metadata['readme_content'])} characters")
    

    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown to HTML.
        
        Args:
            markdown_text: Markdown text
            
        Returns:
            HTML representation of the markdown
        """
        html = markdown.markdown(markdown_text)
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TidyTuesday README</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
                a {{ color: #0366d6; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        return full_html


# Convenience functions that create an instance and call the methods

def last_tuesday(date=None):
    """Find the most recent Tuesday relative to a specified date."""
    tt = TidyTuesdayPy()
    return tt.last_tuesday(date)

def tt_available():
    """List all available TidyTuesday datasets."""
    tt = TidyTuesdayPy()
    return tt.tt_available()

def tt_datasets(year):
    """List available TidyTuesday datasets for a specific year."""
    tt = TidyTuesdayPy()
    return tt.tt_datasets(year)

def tt_download_file(date, file_name, save_to_disk=True):
    """
    Download a specific file from a TidyTuesday dataset by date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        file_name: Name of the file to download
        save_to_disk: Whether to save the file to disk (default: True)
    
    Returns:
        If save_to_disk is True, None (file is saved to disk)
        If save_to_disk is False, a pandas DataFrame with the file contents
    """
    tt = TidyTuesdayPy()
    return tt.tt_download_file(date, file_name, save_to_disk)

def tt_download(date, files="All", save_to_disk=True):
    """
    Download files from a TidyTuesday dataset by date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        files: Either "All" to download all files, or a list of file names
        save_to_disk: Whether to save the files to disk (default: True)
    
    Returns:
        If save_to_disk is True, None (files are saved to disk)
        If save_to_disk is False, a dictionary mapping file names to pandas DataFrames
    """
    tt = TidyTuesdayPy()
    return tt.tt_download(date, files, save_to_disk)

def readme(date):
    """
    Display the README for a TidyTuesday dataset by date.
    
    Args:
        date: Date string in YYYY-MM-DD format
    """
    tt = TidyTuesdayPy()
    return tt.readme(date)

def rate_limit_check(quiet=False):
    """Check the GitHub API rate limit."""
    tt = TidyTuesdayPy()
    return tt.rate_limit_check(quiet)

def get_date(week):
    """
    Takes a week in string form and downloads the TidyTuesday data files from the Github repo.
    
    Args:
        week: Week in YYYY-MM-DD format
    """
    return tt_download(week)

def get_week(year, week_num):
    """
    Takes a year and a week number, and downloads the TidyTuesday data files from the Github repo.
    
    Args:
        year: Year (YYYY)
        week_num: Week number (1-based)
    """
    # Get list of weeks for the year
    tt = TidyTuesdayPy()
    datasets = tt.tt_datasets(year, print_output=False)
    if not datasets:
        print(f"No datasets found for year {year}")
        return None
    
    if week_num < 1 or week_num > len(datasets):
        print(f"Week number {week_num} is out of range for year {year}")
        return None
    
    # Adjust for 0-based indexing
    date = datasets[week_num - 1]["date"]
    return tt_download(date)


def cli():
    """
    Command-line interface dispatcher for pydytuesday.
    
    This function parses command-line arguments and routes them to the appropriate function.
    It allows running commands like: pydytuesday last_tuesday [args]
    """
    import sys
    
    # Help text for each command
    help_text = {
        "last_tuesday": """
Usage: pydytuesday last_tuesday [date]

Find the most recent Tuesday relative to a specified date.

Arguments:
  date    Optional. A date string in YYYY-MM-DD format. Defaults to today's date in New York time.

Examples:
  pydytuesday last_tuesday
  pydytuesday last_tuesday 2025-03-10
""",
        "tt_available": """
Usage: pydytuesday tt_available

List all available TidyTuesday datasets across all years.

This command fetches data from the TidyTuesday GitHub repository and displays
a list of all available datasets organized by year.

Examples:
  pydytuesday tt_available
""",
        "tt_datasets": """
Usage: pydytuesday tt_datasets <year>

List available TidyTuesday datasets for a specific year.

Arguments:
  year    Required. The year to get datasets for (e.g., 2025).

Examples:
  pydytuesday tt_datasets 2025
""",
        "tt_download_file": """
Usage: pydytuesday tt_download_file <date> <file_name>

Download a specific file from a TidyTuesday dataset by date.

Arguments:
  date        Required. Date string in YYYY-MM-DD format.
  file_name   Required. Name of the file to download.

Examples:
  pydytuesday tt_download_file 2025-03-10 data.csv
""",
        "tt_download": """
Usage: pydytuesday tt_download <date> [files]

Download all or specific files from a TidyTuesday dataset by date.

Arguments:
  date     Required. Date string in YYYY-MM-DD format.
  files    Optional. Either "All" to download all files, or a list of file names.
           Defaults to "All".

Examples:
  pydytuesday tt_download 2025-03-10
  pydytuesday tt_download 2025-03-10 data.csv summary.json
""",
        "readme": """
Usage: pydytuesday readme <date>

Display the README for a TidyTuesday dataset by date.

Arguments:
  date    Required. Date string in YYYY-MM-DD format.

Examples:
  pydytuesday readme 2025-03-10
""",
        "rate_limit_check": """
Usage: pydytuesday rate_limit_check [quiet]

Check the GitHub API rate limit.

Arguments:
  quiet    Optional. If True, don't print rate limit info. Defaults to False.

Examples:
  pydytuesday rate_limit_check
  pydytuesday rate_limit_check True
"""
    }
    
    # Add dash versions of the help text
    dash_help_text = {cmd.replace('_', '-'): text for cmd, text in help_text.items()}
    help_text.update(dash_help_text)
    
    if len(sys.argv) < 2:
        print("Usage: pydytuesday <command> [arguments]")
        print("\nAvailable commands:")
        print("  last_tuesday     - Find the most recent Tuesday relative to a date")
        print("  tt_available     - List all available TidyTuesday datasets")
        print("  tt_datasets      - List datasets for a specific year")
        print("  tt_download_file - Download a specific file from a dataset")
        print("  tt_download      - Download all or specific files from a dataset")
        print("  readme           - Display the README for a dataset")
        print("  rate_limit_check - Check the GitHub API rate limit")
        print("\nFor more information on a specific command, run:")
        print("  pydytuesday <command> --help")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    # Check for help flag
    if len(sys.argv) > 2 and sys.argv[2] == "--help":
        if cmd in help_text:
            print(help_text[cmd])
            sys.exit(0)
    
    args = sys.argv[2:]
    
    # Map command names to functions
    commands = {
        "last_tuesday": last_tuesday,
        "tt_available": tt_available,
        "tt_datasets": tt_datasets,
        "tt_download_file": tt_download_file,
        "tt_download": tt_download,
        "readme": readme,
        "rate_limit_check": rate_limit_check,
    }
    
    # Also support commands with dashes instead of underscores
    dash_commands = {cmd.replace('_', '-'): func for cmd, func in commands.items()}
    commands.update(dash_commands)
    
    if cmd in commands:
        try:
            # Remove --help flag if present
            args = [arg for arg in args if arg != "--help"]
            result = commands[cmd](*args)
            # If the function returns a value, print it
            if result is not None:
                print(result)
        except TypeError as e:
            print(f"Error: {e}")
            print(f"Check the arguments for the '{cmd}' command.")
            print(f"Run 'pydytuesday {cmd} --help' for usage information.")
            sys.exit(1)
    else:
        print(f"Unknown command: {cmd}")
        print("Available commands:", ", ".join(sorted(set(commands.keys()))))
        print("\nFor more information on a specific command, run:")
        print("  pydytuesday <command> --help")
        sys.exit(1)


if __name__ == "__main__":
    cli()
