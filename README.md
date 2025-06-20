# Interactive Baby Names Visualization in France

This is a Streamlit application for visualizing baby names in France over time, by region, and by sex. The application uses Altair for creating interactive charts and GeoPandas for handling geographic data.

## Features

1. **Baby Names Over Time**: A line chart showing the evolution of selected baby names over the years.
2. **Regional Effect**: A geographic map showing the popularity of a selected baby name across different regions.
3. **Names by Sex Over Time**: A stacked bar chart showing the proportion of selected baby names by sex over the years.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Steps

1. **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows, use `.\venv\Scripts\activate.ps1`
    ```

3. **Install the required packages**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Place the datasets**:
    Make sure the following datasets are in the project directory:
    - `dpt2020.csv`
    - `departements-version-simplifiee.geojson`

## Running the Application

1. **Activate the virtual environment** (if not already activated):
    ```bash
    source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
    ```

2. **Run the Streamlit application**:
    ```bash
    streamlit run app.py
    ```

3. **Open the application in your browser**:
    After running the above command, Streamlit will provide a local URL (typically `http://localhost:8501`). Open this URL in your browser to view the application.

## Data Preprocessing

The application performs the following data preprocessing steps:
- Removes rows with rare baby names (`_PRENOMS_RARES`) and invalid department codes (`XX`).
- Merges baby names data with geographic data of French departments.
- Groups the data by department, name, and sex, and aggregates the number of occurrences.

## Visualizations

### Baby Names Over Time
Select multiple baby names to see how their popularity has evolved over the years. The line chart will display the number of occurrences for each selected name from 1900 to 2020.

### Regional Effect
Select a baby name to see its popularity across different regions of France. The map will color the regions based on the number of occurrences of the selected name.

### Names by Sex Over Time
Select multiple male and female baby names to see their proportions over the years. The stacked bar chart will display the proportion of each selected name for each year.

## Example

Here are some example visualizations you can create with this application:
- **Evolution of the names "Marie" and "Jean" over time**.
- **Popularity of the name "Lucien" across different regions in France**.
- **Proportion of the names "Marie" and "Lucie" (female) and "Jean" and "Pierre" (male) over time**.

## Troubleshooting

- **Dependency issues**: Make sure all required packages are installed correctly by checking `requirements.txt`.
- **Data loading issues**: Ensure that the `dpt2020.csv` and `departements-version-simplifiee.geojson` files are correctly placed in the project directory.
- **Streamlit errors**: Ensure that you are using the correct version of Streamlit as specified in `requirements.txt`.


