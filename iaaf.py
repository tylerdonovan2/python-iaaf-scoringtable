import pandas as pd
import numpy as np
from typing import Self
import pdfplumber, json

class Mark:
    def __init__(self, event: str, mark: str | int):
        self.event = event

        self.mark: str = mark
        self.float_mark: float = Mark.convert_to_seconds(mark) if type(mark) == str else Mark.convert_to_time(mark)
        
        if type(mark) != str:
            self.mark, self.float_mark = self.float_mark, self.mark

        self.points = None

    def __repr__(self):
        return f"{self.event} - {self.mark} ({self.float_mark}s) - {self.points} Points" if self.points else f"{self.event} - {self.mark} ({self.float_mark}s)"

    # Thanks CHATGPT for the `convert_to_seconds` and `convert_to_time` functions
    def convert_to_seconds(time_str: str) -> float:
        try:
            # if the input is a float already
            return float(time_str)
        except ValueError:
            # split the time by colons
            parts: list = time_str.split(":")
            
            # handle mm:ss format
            if len(parts) == 2:
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            
            # handle hh:mm:ss format
            elif len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
        

    def convert_to_time(seconds: float) -> str:
        seconds = seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        formatted_seconds = f"{seconds:.2f}" 

        if hours > 0:
            return f"{int(hours)}:{minutes:02}:{formatted_seconds.zfill(6)}"
        elif minutes > 0:
            return f"{int(minutes)}:{formatted_seconds.zfill(5)}"
        else:
            return f"{formatted_seconds}"
        

class ScoringTable:
    def __init__(self, table_data: dict) -> None:
        self.table_data = table_data

        self.dataframe = pd.DataFrame.from_dict(table_data)

        self.events = list(self.dataframe)[1:-1]

        self.event_models = {}

    def search_event_keys(self, 
                 gender: str = "", 
                 discipline: str = "",
                 road_race: bool = None, 
                 racewalk: bool = None, 
                 steeple: bool = None, 
                 mixed: bool = None, 
                 short_track: bool = None,
                 exact_match: bool = True) -> list:


        discipline = discipline.lower().replace("km","000m").replace(" ","")
        
        # make sure these ARE in the event key
        inclusive_identifiers = []
        if short_track == True: inclusive_identifiers.append("SH")
        if racewalk == True: inclusive_identifiers.append("RW")
        if steeple == True: inclusive_identifiers.append("SC")
        if mixed == True: inclusive_identifiers.append("MX")
        if road_race == True: inclusive_identifiers.append("RD")

        # make sure these are NOT in the event key
        exclusive_identifiers = []
        if short_track == False: exclusive_identifiers.append("SH")
        if racewalk == False: exclusive_identifiers.append("RW")
        if steeple == False: exclusive_identifiers.append("SC")
        if mixed == False: exclusive_identifiers.append("MX")
        if road_race == False: exclusive_identifiers.append("RD")

        key_matches = []
        for event_key in self.events:
            g, d, *i = event_key.split("-")

            if not gender.lower() == g.lower() and gender:
                continue

            if (d.lower() != discipline.lower()) or (not exact_match and not d.lower() in discipline.lower()) and discipline:
                continue

            # handle inclusive identifiers
            matches_identifiers = True
            for identifier in inclusive_identifiers:
                if not identifier in i:
                    matches_identifiers = False

            if not matches_identifiers:
                continue

            # handle exclusive identifiers
            matches_identifiers = False
            for identifier in exclusive_identifiers:
                if identifier in i:
                    matches_identifiers = True

            if matches_identifiers:
                continue

            key_matches.append(event_key)

        return key_matches


    def calculate_coefficients(self, event: str, flip_axis: bool = False, deg: int = 15) -> list:
        event_col = self.dataframe[event]

        mask = ~np.isnan(event_col)

        x = event_col[mask]
        y = self.dataframe["Points"][mask]

        # Used to create a function f(x) where x is points and f(x) is the mark
        if flip_axis: x, y = y, x

        return list(np.polyfit(x, y, deg))
    
    def model_equation(self, event: str, flip_axis: bool = False, deg: int = 15) -> np.poly1d:
        coefficients = self.calculate_coefficients(event, flip_axis=flip_axis, deg=deg)

        return np.poly1d(coefficients)
    
    def calculate_points_from_mark(self, mark: Mark) -> int:
        event_model = self.model_equation(mark.event)

        points = round(
            event_model(mark.float_mark)
        )

        mark.points = points

        return points
    
    def calculate_mark_from_points(self, event: str, points: int) -> Mark:
        point_model = self.model_equation(event, flip_axis=True)

        float_mark = point_model(points)

        mark = Mark(event, float_mark)

        mark.points = points

        return mark
    
    def calculate_equivalent_mark(self, mark: Mark, event: str) -> Mark:
        points = self.calculate_points_from_mark(mark)
        mark.points = points

        equivalent_mark = self.calculate_mark_from_points(event, points)

        return equivalent_mark
    
    def save_json(self, file_path: str):
        with open(file_path, 'w') as f:
            f.write(json.dumps(self.table_data, indent=3))

    def from_pdf(
            file_path: str, 
            convert_time_strings: bool = True, 
            show_progress: bool = False, 
            save_file: str = "") -> Self:

        table_data = {
            "Points": list(range(1400,0,-1))
        }

        with pdfplumber.open(file_path) as pdf: 
            for page in pdf.pages:
                # filter for text
                clean_page = page.filter(lambda obj: obj["object_type"] == "char" and "Bold" in obj["fontname"])
                
                # seperate by lines and cleanup column titles and normalize event names
                page_lines = clean_page.extract_text().replace("ix","-MX").replace(" sh","-SH").replace(" km", "000m").replace("km","000m").replace(" Miles","Mile").replace(" SC","-SC").replace(",","").replace("t.","t").replace("W","-RW").split("\n")

                # progress bar
                if show_progress: print("Page:", page.page_number, "/", len(pdf.pages))

                if len(page_lines) == 53: # * the point tables pages have exactly 53 lines *

                    # remove page number line
                    page_number = page_lines.pop()

                    # remove section title line and determine gender
                    section_title = page_lines.pop(0).lower()

                    # add event identifiers
                    gender = "W-" if "women" in section_title else "M-"
                    road = "-RD" if "road" in section_title else ""

                    # get event column titles
                    title_row = page_lines.pop(0)
                    titles = title_row.split()


                    for line in page_lines:

                        for index, value in enumerate(line.split()):
                            # prevent repeat points columnn
                            if titles[index] == "Points": continue

                            # create unique key for event
                            event = gender + titles[index] + road

                            # clean up the values
                            if value == "-":
                                value = None

                            if convert_time_strings and value:
                                value = Mark.convert_to_seconds(value)
                            
                            # append to existing column or create new 
                            if table_data.get(event):
                                table_data[event].append(value)
                            else:
                                table_data[event] = [value]

        scoring_table = ScoringTable(table_data)

        if save_file:
            scoring_table.save_json(save_file)

        return scoring_table
    
    def from_json(file_path: str) -> Self | None:
        try:
            with open(file_path) as f:
                df_data = json.loads(f.read())

            return ScoringTable(df_data)

        except Exception as e:
            raise e
    

