# PidyTuesday

PidyTuesday is a Python library that ports the functionality of the TidyTuesday CRAN package to Python. It provides a suite of command-line tools for accessing and downloading TidyTuesday datasets hosted on GitHub.

## Features

- **Get the most recent Tuesday date:** Useful for aligning with TidyTuesday releases.
- **List available datasets:** Discover available TidyTuesday datasets across years.
- **Download datasets:** Retrieve individual files or complete datasets.
- **Display dataset README:** Open the dataset's README in your web browser.
- **Check GitHub API rate limits:** Monitor your GitHub API usage.

## Installation

### Using uv (recommended)

We make extensive use of uv and uv tools to enable command-line scripts without too much managing of virtual environments.

Please note the **PyPi library is case sensitive** - you must use **PyDyTuesday**.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Install PyDyTuesday to your commandline by using `uv tool install`

   ```bash
   uv tool install PyDyTuesday

   pydytuesday last-tuesday
   ```

Alternatively, you can use `uv tool` or `uvx` to avoid adding the command to your path.

   ```bash
   uv tool PyDyTuesday last-tuesday
   ```
   or using uvx:
   ```bash
   uvx PyDyTuesday last-tuesday
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
   (Consult your system's documentation on how entry points are installed if you encounter issues.)

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

- **Download Specific File**
  - **Description:** Downloads a specified file from a TidyTuesday dataset by date.
  - **Usage:**
    ```bash
    pydytuesday tt-download-file 2025-03-10 data.csv
    ```
    (The example downloads the file 'data.csv' from the dataset for March 10, 2025.)

- **Download Dataset Files**
  - **Description:** Downloads all or selected files from a TidyTuesday dataset by date.
  - **Usage:**
    ```bash
    pydytuesday tt-download 2025-03-10
    pydytuesday tt-download 2025-03-10 data.csv summary.json
    ```
    (The first example downloads all files from the dataset for March 10, 2025. The second example downloads only the specified files.)

- **Display Dataset README**
  - **Description:** Opens the README for a TidyTuesday dataset in your default web browser.
  - **Usage:**
    ```bash
    pydytuesday readme 2025-03-10
    ```
    (The example opens the README for the dataset from March 10, 2025.)

- **Check GitHub Rate Limit**
  - **Description:** Checks the remaining GitHub API rate limit.
  - **Usage:**
    ```bash
    pydytuesday rate-limit-check
    ```

## Example Workflow

Here's a complete example of how to discover, download, and explore TidyTuesday data:

```bash
# 1. Find the most recent Tuesday date
pydytuesday last-tuesday
# Output: 2025-03-11

# 2. List available datasets for a specific year
pydytuesday tt-datasets 2025
# Output: Lists all datasets for 2025 with dates and titles

# 3. Download a specific file from a dataset by date
pydytuesday tt-download-file 2025-03-11 example.csv
# Output: Successfully saved example.csv to /path/to/example.csv

# 4. After downloading, you can read the CSV file using pandas in Python:
import pandas as pd

# Read the downloaded CSV file
df = pd.read_csv("example.csv")

# Display the first few rows
print(df.head())

# Get basic information about the dataset
print(df.info())

# Generate summary statistics
print(df.describe())

# Perform data analysis and visualization
import matplotlib.pyplot as plt
df.plot(kind='bar', x='category', y='value')
plt.title('TidyTuesday Data Analysis')
plt.show()
```

This workflow demonstrates how to use the command-line tools to discover and download data, and then use pandas to analyze the downloaded data.

## Contributing

Contributions are welcome! Here's how you can help improve PidyTuesday:

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
   Add new features, fix bugs, or improve documentation. Ensure your code adheres to the project's style guidelines.
   
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
