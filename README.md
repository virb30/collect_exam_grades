# ENEM Exam Grades Collector - WebScraping

Webscraping for collect exam grades from ENEM systems page.

# Description

The ENEM Sistems pages makes available to teaching institutions, upon an username and password, a resource for collect the student grades in the exam by sending some data and receiving a text file with the results. However, to achieve this goal, the user must do some repeatable steps inside the system:

- Access the main page
- Put the username and password
- Expand a menu corresponding to the realization year
- Access a submenu for selecte the request method among some options
- Input the data (via a form or file upload containing a list of requested students)
- Access another submenu for collect the successful results
- Download the results file

If the user already knows the year the student took the test, its easy and fast to get the results file. But, if the year is unknown, the user must then access all the year options to collect the results. At the time of writing, there are 10 years to look for, and this number tends to increase.

What this script do:

- get an input file containing a mass data;
- extract the relevant portion of it and put into another file
- access the systems page;
- login;
- loops through the available years;
- for each year found:
  - send the request file generated;
  - access the results page;
  - download the results file to the desired location

# Requirements

Python 3
Chrome browser & Chromedriver corresponding versions

# Usage

- Clone this repository
- Download chromedriver for your system

`git clone https://github.com/virb30/collect_exam_grades.git`

- Navigate to folder

`cd collect_exam_grades`

- Install the requirements

`pip install -r requirements.txt`

- Set `WS_USERNAME` and `WS_PASSWORD` environment variables

- Run command with the desired input and output files

`python ./exam_grades.py <input_file> <output_file>`

## Optional Params

`--col=[int]`: Indicates which column looking for data (default: 0)

`--sep=[str]`: Indicates which separator character to use (default: ';')

# TODO

- [ ] Improve code style
- [ ] Generalize some options like download result file path
- [ ] Add possibility to the user select the desired webdriver via CLI
- [ ] Flexibilize data formatting through the CLI command
