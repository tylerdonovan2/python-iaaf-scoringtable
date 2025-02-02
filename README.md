# Mark and ScoringTable Classes


**NOTE THAT THIS DOCUMENTATION WAS ALMOST ENTIRELY WRITTEN BY CHATGPT AND WAS NOT THOROUGHLY CHECKED**


## Overview
This repository provides two primary classes:
1. **Mark**: Represents an event mark and provides utility functions for converting between time formats.
2. **ScoringTable**: Manages scoring tables, calculates performance points, and provides utilities for loading and saving data from JSON or PDF files.

---

## Installation
```bash
pip install pandas numpy pdfplumber
```

---

## Class: `Mark`
### Description
The `Mark` class represents a performance mark for an event. It stores the original mark (either a string or a numeric value), converts it into a floating-point time format, and provides methods for conversions.

### Attributes
- `event` (str): The name of the event.
- `mark` (str): The original mark in string format.
- `float_mark` (float): The mark converted into a numerical time representation.
- `points` (int, optional): The performance points assigned based on the mark (gets assigned to the mark when points are calculated).

### Methods
#### `convert_to_seconds(time_str: str) -> float`
Converts a time string (e.g., "2:30" or "1:10:05") into total seconds.

#### `convert_to_time(seconds: float) -> str`
Converts a numerical time in seconds back into a formatted time string.

#### `__repr__()`
Returns a string representation of the Mark object, including event, mark, and points if available.

---

## Class: `ScoringTable`
### Description
The `ScoringTable` class represents a performance scoring table, allowing for event-based scoring calculations and data manipulation.

### Attributes
- `table_data` (dict): Raw data containing event scores.
- `dataframe` (pd.DataFrame): Pandas DataFrame representation of the scoring table.
- `events` (list): List of event keys.

### Methods
#### `search_event_keys(...) -> list`
Filters and searches for event keys based on criteria like gender, discipline, and event type (e.g., road race, steeplechase, race walk).
- Event keys are stored in the format {GENDER}-{EVENT} [-{IDENTIFIERS}]
- Identifiers include: -RW (Racewalk) -RD (Roadrace) -SC (Steeple Chase) -SH (Short track) -MX (Mixed Relays)
##### Examples: 
- M-100m is the event key for the Men's 100m
- M-4x400m-MX-SH is the event key for the 4x400m mixed relay on a short track 
##### NOTE: M-4x400m-MX-SH is the same as W-4x400m-MX-SH since the relays are mixed genders

#### `calculate_coefficients(event: str, flip_axis: bool = False, deg: int = 15) -> list`
Generates polynomial coefficients for the event's performance curve.

#### `model_equation(event: str, flip_axis: bool = False, deg: int = 15) -> np.poly1d`
Creates a polynomial equation model for predicting marks based on points.

#### `calculate_points_from_mark(mark: Mark) -> int`
Determines the point value of a given mark using the event's scoring model.

#### `calculate_mark_from_points(event: str, points: int) -> Mark`
Predicts a mark for a given event based on performance points.

#### `calculate_equivalent_mark(mark: Mark, event: str) -> Mark`
Finds the equivalent mark in another event based on the same point score.

#### `save_json(file_path: str) -> None`
Saves the scoring table as a JSON file.

#### `from_pdf(file_path: str, ...) -> Self`
Extracts scoring data from a PDF file and converts it into a `ScoringTable`.

#### `from_json(file_path: str) -> Self`
Loads a scoring table from a JSON file.

---

## Usage Example
```
# Load scoring table from a PDF file
scoring_table = ScoringTable.from_pdf("World Athletics Scoring Tables of Athletics.pdf", save_file="scoring_data.json")

# Load scoring table from a JSON file
scoring_table = ScoringTable.from_json("scoring_data.json")

# Create a mark and calculate points
mark = Mark("M-100m", "10.23")
points = scoring_table.calculate_points_from_mark(mark)
print(mark)
```

---

## Contributing
Feel free to fork the repository and submit pull requests for improvements.

---
