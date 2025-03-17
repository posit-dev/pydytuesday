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
    
    def tt_load_gh(self, date_or_year: Union[str, int], week: Optional[int] = None) -> Dict[str, Any]:
        """
        Load TidyTuesday metadata from GitHub.
        
        Args:
            date_or_year: Either a date string (YYYY-MM-DD) or a year (YYYY)
            week: If date_or_year is a year, which week number to use
            
        Returns:
            A dictionary with metadata about the TidyTuesday dataset
        """
        if self.rate_limit_check(quiet=True) < 5:
            print("GitHub API rate limit is too low. Try again later.")
            return {}
        
        try:
            # Handle year and week number
            if week is not None:
                year = str(date_or_year)
                # Get list of weeks for the year
                datasets = self.tt_datasets(year, print_output=False)
                if not datasets:
                    print(f"No datasets found for year {year}")
                    return {}
                
                if week < 1 or week > len(datasets):
                    print(f"Week number {week} is out of range for year {year}")
                    return {}
                
                # Adjust for 0-based indexing
                date = datasets[week - 1]["date"]
            else:
                # Handle direct date
                date = str(date_or_year)
                year = date[:4]
            
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
            
            # Get README content - try main branch first, then fall back to master
            readme_url = f"{self.RAW_GITHUB_URL_MAIN}/{year}/{date}/README.md"
            readme_response = requests.get(readme_url)
            
            # If main branch doesn't work, try master branch
            if readme_response.status_code != 200:
                readme_url = f"{self.RAW_GITHUB_URL_MASTER}/{year}/{date}/README.md"
                readme_response = requests.get(readme_url)
                
            readme_content = readme_response.text if readme_response.status_code == 200 else ""
            
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
    
    def tt_download_file(self, tt_data: Dict[str, Any], file_identifier: Union[str, int], verbose: bool = True) -> pd.DataFrame:
        """
        Download a specific file from a TidyTuesday dataset.
        
        Args:
            tt_data: TidyTuesday metadata from tt_load_gh
            file_identifier: Either the file name or index (0-based)
            verbose: If True, print download progress
            
        Returns:
            A pandas DataFrame with the file contents
        """
        if not tt_data or "files" not in tt_data:
            if verbose:
                print("Invalid TidyTuesday data. Use tt_load_gh first.")
            return pd.DataFrame()
        
        try:
            files = tt_data["files"]
            if isinstance(file_identifier, int):
                if file_identifier < 0 or file_identifier >= len(files):
                    if verbose:
                        print(f"File index {file_identifier} is out of range")
                    return pd.DataFrame()
                file_info = files[file_identifier]
            else:
                file_info = next((f for f in files if f["name"] == file_identifier), None)
                if not file_info:
                    if verbose:
                        print(f"File '{file_identifier}' not found")
                    return pd.DataFrame()
            
            if verbose:
                print(f"Downloading {file_info['name']}...")
            response = requests.get(file_info["download_url"])
            response.raise_for_status()
            
            file_name = file_info["name"].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            try:
                if file_name.endswith('.csv'):
                    df = pd.read_csv(tmp_path)
                elif file_name.endswith('.tsv'):
                    df = pd.read_csv(tmp_path, sep='\t')
                elif file_name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(tmp_path)
                elif file_name.endswith('.json'):
                    df = pd.read_json(tmp_path)
                elif file_name.endswith('.parquet'):  # Added support
                    df = pd.read_parquet(tmp_path)
                else:
                    if verbose:
                        print(f"Unsupported file format: {file_name}")
                    return pd.DataFrame()
            finally:
                os.unlink(tmp_path)
            
            if verbose:
                print(f"Successfully loaded {file_info['name']}")
            return df
            
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Error downloading file: {e}")
            return pd.DataFrame()
        except pd.errors.ParserError as e:
            if verbose:
                print(f"Error parsing file: {e}")
            return pd.DataFrame()
    
    def tt_download(self, tt_data: Dict[str, Any], files: Union[str, List[str]] = "All") -> Dict[str, pd.DataFrame]:
        """
        Download all or specific files from a TidyTuesday dataset.
        
        Args:
            tt_data: TidyTuesday metadata from tt_load_gh
            files: Either "All" to download all files, or a list of file names
            
        Returns:
            Dictionary mapping file names to pandas DataFrames
        """
        if not tt_data or "files" not in tt_data:
            print("Invalid TidyTuesday data. Use tt_load_gh first.")
            return {}
        
        try:
            available_files = tt_data["files"]
            
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
            
            result = {}
            for file_info in files_to_download:
                file_name = file_info["name"]
                print(f"Downloading {file_name}...")
                
                response = requests.get(file_info["download_url"])
                
                if response.status_code != 200:
                    print(f"Error downloading {file_name}: {response.status_code}")
                    continue
                
                # Save to a temporary file first
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                # Read the file based on its extension
                file_name_lower = file_name.lower()
                try:
                    if file_name_lower.endswith('.csv'):
                        df = pd.read_csv(tmp_path)
                    elif file_name_lower.endswith('.tsv'):
                        df = pd.read_csv(tmp_path, sep='\t')
                    elif file_name_lower.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(tmp_path)
                    elif file_name_lower.endswith('.json'):
                        df = pd.read_json(tmp_path)
                    else:
                        print(f"Unsupported file format: {file_name}")
                        continue
                    
                    # Store in result dictionary, using the name without extension as the key
                    key = os.path.splitext(file_name)[0]
                    result[key] = df
                    print(f"Successfully loaded {file_name}")
                    
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_path)
            
            return result
            
        except Exception as e:
            print(f"Error downloading files: {e}")
            return {}
    
    def tt_load(self, date_or_year: Union[str, int], week: Optional[int] = None, 
                files: Union[str, List[str]] = "All") -> Dict[str, Any]:
        """
        Load TidyTuesday data from GitHub.
        
        Args:
            date_or_year: Either a date string (YYYY-MM-DD) or a year (YYYY)
            week: If date_or_year is a year, which week number to use
            files: Either "All" to download all files, or a list of file names
            
        Returns:
            Dictionary with the downloaded data and metadata
        """
        # First get the metadata
        tt_data = self.tt_load_gh(date_or_year, week)
        
        if not tt_data:
            return {}
        
        # Then download the data
        data = self.tt_download(tt_data, files)
        
        # Combine metadata and data
        result = {
            "date": tt_data["date"],
            "year": tt_data["year"],
            "readme_content": tt_data["readme_content"],
            "readme_html": tt_data["readme_html"],
            **data  # Add all the dataframes
        }
        
        return result
    
    def readme(self, tt_data: Dict[str, Any]) -> None:
        """
        Display the README for a TidyTuesday dataset.
        
        Args:
            tt_data: TidyTuesday data from tt_load or tt_load_gh
        """
        if not tt_data or "readme_html" not in tt_data:
            print("No README available for this dataset.")
            return
        
        # Create a temporary HTML file and open it in the browser
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as tmp:
            tmp.write(tt_data["readme_html"])
            tmp_path = tmp.name
        
        webbrowser.open(f"file://{tmp_path}")
        print(f"README opened in your browser.")
    

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

def tt_load_gh(date_or_year, week=None):
    """Load TidyTuesday metadata from GitHub."""
    tt = TidyTuesdayPy()
    return tt.tt_load_gh(date_or_year, week)

def tt_download_file(tt_data, file_identifier):
    """Download a specific file from a TidyTuesday dataset."""
    tt = TidyTuesdayPy()
    return tt.tt_download_file(tt_data, file_identifier)

def tt_download(tt_data, files="All"):
    """Download all or specific files from a TidyTuesday dataset."""
    tt = TidyTuesdayPy()
    return tt.tt_download(tt_data, files)

def tt_load(date_or_year, week=None, files="All"):
    """Load TidyTuesday data from GitHub."""
    tt = TidyTuesdayPy()
    return tt.tt_load(date_or_year, week, files)

def readme(tt_data):
    """Display the README for a TidyTuesday dataset."""
    tt = TidyTuesdayPy()
    return tt.readme(tt_data)

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
    tt = TidyTuesdayPy()
    data = tt.tt_load(week)
    return data

def get_week(year, week_num):
    """
    Takes a year and a week number, and downloads the TidyTuesday data files from the Github repo.
    
    Args:
        year: Year (YYYY)
        week_num: Week number (1-based)
    """
    tt = TidyTuesdayPy()
    data = tt.tt_load(year, week=week_num)
    return data


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
        "tt_load_gh": """
Usage: pydytuesday tt_load_gh <date_or_year> [week]

Load TidyTuesday metadata from GitHub.

Arguments:
  date_or_year    Required. Either a date string (YYYY-MM-DD) or a year (YYYY).
  week            Optional. If date_or_year is a year, which week number to use.

Examples:
  pydytuesday tt_load_gh 2025-03-10
  pydytuesday tt_load_gh 2025 3
""",
        "tt_download_file": """
Usage: pydytuesday tt_download_file <tt_data> <file_identifier>

Download a specific file from a TidyTuesday dataset.
Note: This command requires data loaded with tt_load_gh first.

Arguments:
  tt_data           Required. TidyTuesday metadata from tt_load_gh.
  file_identifier   Required. Either the file name or index (0-based).

Examples:
  # First load metadata, then download a file
  data = pydytuesday tt_load_gh 2025-03-10
  pydytuesday tt_download_file "$data" data.csv
  pydytuesday tt_download_file "$data" 0
""",
        "tt_download": """
Usage: pydytuesday tt_download <tt_data> [files]

Download all or specific files from a TidyTuesday dataset.
Note: This command requires data loaded with tt_load_gh first.

Arguments:
  tt_data    Required. TidyTuesday metadata from tt_load_gh.
  files      Optional. Either "All" to download all files, or a list of file names.
             Defaults to "All".

Examples:
  # First load metadata, then download files
  data = pydytuesday tt_load_gh 2025-03-10
  pydytuesday tt_download "$data" All
  pydytuesday tt_download "$data" data.csv summary.json
""",
        "tt_load": """
Usage: pydytuesday tt_load <date_or_year> [week] [files]

Load TidyTuesday data from GitHub.

Arguments:
  date_or_year    Required. Either a date string (YYYY-MM-DD) or a year (YYYY).
  week            Optional. If date_or_year is a year, which week number to use.
  files           Optional. Either "All" to download all files, or a list of file names.
                  Defaults to "All".

Examples:
  pydytuesday tt_load 2025-03-10
  pydytuesday tt_load 2025 3 All
  pydytuesday tt_load 2025 3 data.csv
""",
        "readme": """
Usage: pydytuesday readme <tt_data>

Display the README for a TidyTuesday dataset.
Note: This command requires data loaded with tt_load_gh or tt_load first.

Arguments:
  tt_data    Required. TidyTuesday data from tt_load or tt_load_gh.

Examples:
  # First load data, then display README
  data = pydytuesday tt_load_gh 2025-03-10
  pydytuesday readme "$data"
""",
        "rate_limit_check": """
Usage: pydytuesday rate_limit_check [quiet]

Check the GitHub API rate limit.

Arguments:
  quiet    Optional. If True, don't print rate limit info. Defaults to False.

Examples:
  pydytuesday rate_limit_check
  pydytuesday rate_limit_check True
""",
        "get_date": """
Usage: pydytuesday get_date <week>

Takes a week in string form and downloads the TidyTuesday data files from the Github repo.

Arguments:
  week    Required. Week in YYYY-MM-DD format.

Examples:
  pydytuesday get_date 2025-03-10
""",
        "get_week": """
Usage: pydytuesday get_week <year> <week_num>

Takes a year and a week number, and downloads the TidyTuesday data files from the Github repo.

Arguments:
  year       Required. Year (YYYY).
  week_num   Required. Week number (1-based).

Examples:
  pydytuesday get_week 2025 3
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
        print("  tt_load_gh       - Load TidyTuesday metadata from GitHub")
        print("  tt_download_file - Download a specific file from a dataset")
        print("  tt_download      - Download all or specific files from a dataset")
        print("  tt_load          - Load TidyTuesday data from GitHub")
        print("  readme           - Display the README for a dataset")
        print("  rate_limit_check - Check the GitHub API rate limit")
        print("  get_date         - Get data for a specific week by date")
        print("  get_week         - Get data for a specific week by year and week number")
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
        "tt_load_gh": tt_load_gh,
        "tt_download_file": tt_download_file,
        "tt_download": tt_download,
        "tt_load": tt_load,
        "readme": readme,
        "rate_limit_check": rate_limit_check,
        "get_date": get_date,
        "get_week": get_week,
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
