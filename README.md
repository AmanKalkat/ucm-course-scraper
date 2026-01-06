# UC Merced Course Catalog Scraper and API

A Python tool that scrapes course information from UC Merced’s online course catalog and provides an API for querying the data. It scrapes 8,388 courses across 4 academic years using Selenium and BeautifulSoup.

Information extracted:

- Course codes

- Course names

- Course descriptions

- Credits

- Prerequisites

- Corequisites

- Class levels

- Repeats allowed for credit  

Data is exported to Excel spreadsheets and loaded into a PostgreSQL database, then exported to SQLite for the API. Utility scripts handle both PostgreSQL population and SQLite export. FastAPI endpoints provided filtering by prefix, prerequisites, year, and more.


## 1. Features

- **Dynamic Scraping**: Uses Selenium to navigate JavaScript-heavy dropdown and BeautifulSoup for HTML parsing

- **Concurrent Execution:** Leverages ThreadPoolExecutor to scrape 4 academic years simultaneously. 

- **Flexible Data Storage:** Exports data to Excel and SQLite, with a dedicated script for PostgreSQL

- **Read APIs:** Allows users to filter courses by prefix, prerequisites, year, and class level


## 2. Tech Stack

- Python 3.13

- FastAPI (API framework)

- Selenium + BeautifulSoup (web scraping)

- SQLAlchemy (ORM)

- Pandas (data processing)

- SQLite/PostgreSQL (database options)


## 3. Project Structure 

\`\`\`

course\_scraper/

    ├── .gitignore

    ├── api/

    │   ├── test/

    │   │   └── test\_api.py

    │   ├── config.py

    │   ├── database.py

    │   ├── main.py

    │   ├── models.py

    │   ├── schemas.py

    ├── logs/

    ├── spreadsheets/

    │   ├── 2022\_2023.xlsx

    │   ├── 2023\_2024.xlsx

    │   ├── 2024\_2025.xlsx

    │   ├── 2025\_2026.xlsx

    ├── utils/

    │   ├── export\_to\_sqlite.py

    │   └── fill\_db.py

    ├── venv/

    ├── course\_catalog.db

    ├── main.py

    ├── requirements.txt

    └── scraper.py

\`\`\`

- [scraper.py](http://scraper.py) - Core scraping logic

- [main.py](http://main.py) - Multi-threaded scraper orchestrator

- utils/ - Database population scripts

- api/ - FastAPI endpoints

- course\_catalog.db - SQLite database exported from PostgreSQL, used by the API

- logs/ - contains files that record what happened during the scraping process


## 4. Installation

1. Clone repository

2. Create and start virtual environment

3. Install dependencies from requirements.txt: pip install -r requirements.txt


## 5. Configuration

Required for Database Population: To populate the database from Excel files, create a .env file in the utils/ directory with PostgreSQL connection details:

DB\_USER=your\_postgres\_username

DB\_PASSWORD=your\_postgres\_password

DB\_HOST=localhost

DB\_PORT=5432

DB\_NAME=course\_catalog

The API uses SQLite (course\_catalog.db) which is exported from PostgreSQL and requires no configuration to run.


## 6. Usage 

Populating the Database:

After scraping, populate PostgreSQL, and export to SQLite

1. cd utils

2. python fill\_db.py

3. python export\_to\_sqlite.py

The SQLite database (course\_catalog.db) is then used by the API.

Running the Scraper:

1. cd /path/to/course\_scraper

2. python main.py

This will scrape all 4 catalog years concurrently (2022-2026), generate Excel files in spreadsheets/, create logs in logs/, and display execution time and summary statistics

Note: The scraper runs in non-headless mode by default. To enable headless mode, uncomment line 40 in [main.py](http://main.py):

chrome\_options.add\_argument("--headless")

Starting the API:

1. cd api

2. uvicorn main:app --reload

   1. Or specify a specific port with uvicorn main:app --reload --port \<port\_num>

3. Test with: pytest

See /docs for Interactive API documentation




API Endpoints:

|        |                                         |                                                   |
| ------ | --------------------------------------- | ------------------------------------------------- |
| Method | Endpoint                                | Description                                       |
| GET    | /courses                                | Get all courses (supports filtering)              |
| GET    | /courses/code/{course\_code}            | Get all versions of a course across catalog years |
| GET    | /courses/{course\_code}/{catalog\_year} | Get a specific course from a specific year        |
| GET    | /catalog\_years                         | Get all available catalog years                   |
| GET    | /prefixes                               | Get all course prefixes (CSE, MATH, BIO, etc.)    |
| GET    | /health                                 | Health check endpoint                             |

Available Filters (for /courses):

|                  |          |                                       |               |
| :--------------: | :------: | :-----------------------------------: | :-----------: |
|    **Filter**    | **Type** |            **Description**            |  **Example**  |
|   course\_code   |  string  |        Exact course code match        |    CSE 031    |
|  course\_prefix  |  string  |       Course prefix (department)      |      CSE      |
|   catalog\_year  |  string  |         Specific academic year        |   2024\_2025  |
|   has\_prereqs   |  boolean |    Filter by prerequisite existence   |      true     |
|    has\_coreqs   |  boolean |    Filter by corequisite existence    |      true     |
| prereq\_contains |  string  |      Search within prerequisites      |    MATH 024   |
|  coreq\_contains |  string  |       Search within corequisites      |    CSE 100    |
|   class\_level   |  string  |         Filter by class level         | Undergraduate |
| repeats\_allowed |  boolean |        Filter by repeatability        |      true     |
|    min\_repeat   |  integer |          Minimum repeat count         |       2       |
|     sort\_by     |  string  | Sort by field (default: course\_code) |  course\_name |

\
\



## 7. Limitations

1. External Links: Courses that open in a new window or tab when clicked are not automatically scraped. These are logged in the external links list for manual review, which can be found in the log files and console output.

2. Must have Google Chrome installed on your system


## 8. Data Schema

Course Fields

|                               |                   |                                                           |
| ----------------------------- | ----------------- | --------------------------------------------------------- |
| Field                         | Type              | Description                                               |
| course\_code                  | string            | Course identifier (“CSE 100”)                             |
| course\_name                  | string            | Full course name                                          |
| credits                       | Int or list\[int] | Credit house (single value or range \[min, max])          |
| course\_description           | string            | Full course description                                   |
| prereqs                       | list\[string]     | List of prerequisite courses (\[“CSE 100“, “MATH 141”])   |
| coreqs                        | list\[string]     | List of corequisite courses                               |
| class\_levels                 | list\[string]     | Eligible class levels (\[“Sophmore”, “Junior”, “Senior”]) |
| repeats\_allowed\_for\_credit | integer           | Number of times a course can be completed                 |
| catalog\_year                 | string            | Academic year (“2024\_2025”)                              |

\


Database Schema Differences:

Postgresql

- Fields that contain lists are stored as JSONB

- Requires .env variables

- Populated from Excel files (utils/fill\_db.py)

SQLite

- Fields that contain lists are stores as JSON strings

- Exported from PostgreSQL (utils/export\_to\_sqlite.py)

Workflow: Scraper → Excel files → PostgreSQL → SQLite → API

\
\


_Used_ [_https://www.readmecodegen.com/file-tree/manual-file-tree-creater_](https://www.readmecodegen.com/file-tree/manual-file-tree-creater) _for file tree in 3. Project Structure_ 
