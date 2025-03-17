# PidyTuesday

PidyTuesday is a Python library that ports the functionality of the TidyTuesday CRAN package to Python. It provides a suite of command-line tools for accessing and processing TidyTuesday datasets hosted on GitHub.

## Features

- **Get the most recent Tuesday date:** Useful for aligning with TidyTuesday releases.
- **List available datasets:** Discover available TidyTuesday datasets across years.
- **Download datasets:** Retrieve individual files or complete datasets.
- **Display dataset README:** Open the dataset's README in your web browser.
- **Check GitHub API rate limits:** Monitor your GitHub API usage.

## Installation

### Using uv (recommended)

We make extensive use of uv and uv tools to enable command-line scripts without too much managing of virtual environments.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Install PyDyTuesday to your commandline by using `uv tool install`

   ```bash
   uv tool install pydytuesday

   pydytuesday last-tuesday
   ```

Alternatively, you can use `uv tool` or `uvx` to avoid adding the command to your path.

   ```bash
   uv tool pydytuesday last-tuesday
   ```
   or using uvx:
   ```bash
   uvx pydytuesday last-tuesday
   ```

### Using pip

Alternatively, you can install the library directly into your environment using pip.

1. Install the package (preferably in editable mode during development):
   ```bash
   pip install -e .
   ```
   
2. Once installed, the CLI commands defined in the package (via the `[project.scripts]` section in `pyproject.toml`) will be automatically added to your PATH. This means you can run the commands directly from your terminal. For example:
   ```bash
   last-tuesday
   tt-available
   ```
   If the commands are not directly available in your PATH, you may invoke them using Python's module execution:
   ```bash
   python -m pydytuesday
   ```
   (Consult your system’s documentation on how entry points are installed if you encounter issues.)

## Usage

Once you have installed the library using uv, you should be able to run your commands from anywhere on your system.

- **Last Tuesday**
  - **Description:** Prints the most recent Tuesday date relative to today's date or an optionally provided date.
  - **Usage:**
    ```bash
    pydytuesday last-tuesday
    pydytuesday last-tuesday 2025-03-10
    ```
    (The second example passes a specific date argument in YYYY-MM-DD format.)

- **TidyTuesday Available**
  - **Description:** Lists all available TidyTuesday datasets.
  - **Usage:**
    ```bash
    pydytuesday tt-available
    ```

- **TidyTuesday Datasets**
  - **Description:** Lists datasets for a specific year.
  - **Usage:**
    ```bash
    pydytuesday tt-datasets 2025
    ```
    (Example passes the year as an argument.)

- **Load GitHub Metadata**
  - **Description:** Loads TidyTuesday metadata from GitHub for a given date or year.
  - **Usage:**
    ```bash
    pydytuesday tt-load-gh 2025-03-10
    pydytuesday tt-load-gh 2025 3
    ```
    (The first example uses a date string; the second example uses a year and a week number.)

- **Download Specific File**
  - **Description:** Downloads a specified file from a TidyTuesday dataset.
  - **Usage:**
    ```bash
    pydytuesday tt-download-file data.csv
    pydytuesday tt-download-file 0
    ```
    (The first example passes the file name; the second example passes the file index.)

- **Download Dataset Files**
  - **Description:** Downloads all or selected files from a TidyTuesday dataset.
  - **Usage:**
    ```bash
    pydytuesday tt-download All
    pydytuesday tt-download data.csv summary.json
    ```
    (Example shows using "All" or a list of specific file names.)

- **Load Complete Dataset**
  - **Description:** Loads the entire TidyTuesday dataset, including metadata and files.
  - **Usage:**
    ```bash
    pydytuesday tt-load 2025-03-10
    pydytuesday tt-load 2025 3 All
    ```
    (The first example uses a date string; the second example uses a year, week number, and optionally file selection.)

- **Display Dataset README**
  - **Description:** Opens the README for a TidyTuesday dataset in your default web browser.
  - **Usage:**
    ```bash
    pydytuesday readme
    ```

- **Check GitHub Rate Limit**
  - **Description:** Checks the remaining GitHub API rate limit.
  - **Usage:**
    ```bash
    pydytuesday rate-limit
    ```

- **Get Data by Date**
  - **Description:** Retrieves data for a specific week given as a date string.
  - **Usage:**
    ```bash
    pydytuesday get-date 2025-03-10
    ```

- **Get Data by Week Number**
  - **Description:** Retrieves data for a specified week number within a given year.
  - **Usage:**
    ```bash
    pydytuesday get-week 2025 3
    ```
    (The command takes a year and a week number as arguments.)

## Contributing

Contributions are welcome! Here’s how you can help improve PidyTuesday:

1. **Fork the Repository:**  
   Click on the "Fork" button at the top right of the repository page and create your own copy.
   
2. **Clone Your Fork:**  
   ```bash
   git clone https://github.com/your-username/PidyTuesday.git
   cd PidyTuesday
   ```

3. **Create a New Branch:**  
   Start a new feature or bugfix branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes:**  
   Add new features, fix bugs, or improve documentation. Ensure your code adheres to the project’s style guidelines.
   
5. **Commit Your Changes:**  
   Write clear commit messages that describe your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. **Push to Your Fork:**  
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Submit a Pull Request:**  
   Open a pull request on the main repository. Provide a detailed description of your changes and reference any issues your PR addresses.

For larger contributions, consider discussing your ideas by opening an issue first so that we can provide guidance before you start coding.

## License

This project is licensed under MIT as per the [LICENSE](LICENSE) file.
