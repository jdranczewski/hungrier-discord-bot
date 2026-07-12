import datetime
import re
from dataclasses import dataclass

@dataclass
class Day:
    day: int

@dataclass
class Month:
    month: int

@dataclass
class Year:
    year: int

@dataclass
class Date:
    year: int | None
    month: int
    day: int

    @property
    def date(self) -> datetime.date:
        if self.year is None:
            raise Exception("No year set")
        return datetime.date(self.year, self.month, self.day)

@dataclass
class Range:
    start: Date
    end: Date

class Ranger:
    def __repr__(self):
        return "Ranger()"

months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
sub_months = [x[:3] for x in months]
separators = ".,()[]" # handling - and / separately
number_ends = ["th", "st", "nd", "rd"]

def parse_month(string) -> Month | None:
    if string in months:
        return Month(months.index(string) + 1)
    elif string in sub_months:
        return Month(sub_months.index(string) + 1)
    return None

def parse_day(string) -> Day | None:
    try:
        for number_end in number_ends:
            string = string.replace(number_end, "")
        return Day(int(string))
    except ValueError:
        return None

def _regex_search(string) -> tuple[int | None, int, int, str] | None:
    if (match := re.search(r"([0-9]{4})\/([0-9]{2})\/([0-9]{2})", string)) is not None:
        year, month, day = (int(match.group(i)) for i in range(1, 4))
        return year, month, day, string.replace(match.group(0), "DATEFOUND")
    if (match := re.search(r"([0-9]{2})\/([0-9]{2})\/([0-9]{4})", string)) is not None:
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        return year, month, day, string.replace(match.group(0), "DATEFOUND")
    if (match := re.search(r"([0-9]{2})\/([0-9]{2})\/([0-9]{2})", string)) is not None:
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        year += 2000
        return year, month, day, string.replace(match.group(0), "DATEFOUND")
    if (match := re.search(r"([0-9]{2})\/([0-9]{2})", string)) is not None:
        day, month = (int(match.group(i)) for i in range(1, 3))
        return None, month, day, string.replace(match.group(0), "DATEFOUND")

def _parse_part(part) -> list[None | Date | Ranger| Month| Day]:
    if "/" in part:
        match = _regex_search(part)
        if match is None:
            return [None]
        year, month, day, _ = match
        return [Date(year, month, day)]
    if part == "-":
        return [Ranger()]
    if (month := parse_month(part)) is not None:
        return [month]
    if (day := parse_day(part)) is not None:
        return [day] if day.day < 32 else [None]
    return [None]

def _set_years(parts, past_reference):
    for part in parts:
        if isinstance(part, Date) and part.year is None:
            part.year = past_reference.year
            if part.date < past_reference:
                part.year += 1

def _handle_rangers(parsed_parts):
    i = 1
    while i < len(parsed_parts) - 1:
        if not isinstance(parsed_parts[i], Ranger):
            i += 1
            continue
        a, b = parsed_parts[i-1], parsed_parts[i+1]
        if isinstance(a, Day) and isinstance(b, Day):
            del parsed_parts[i]
            for j, k in enumerate(range(a.day+1, parsed_parts[i].day)):
                parsed_parts.insert(i, Day(k))
                i += 1
        elif isinstance(a, Date) and isinstance(b, Date):
            # figure out a daterange thing?
            # need to deal with years before this point to account for leap years
            delta = b.date - a.date
            del parsed_parts[i]
            for j in range(delta.days-1):
                new_day = a.date + datetime.timedelta(days=j+1)
                parsed_parts.insert(i, Date(new_day.year, new_day.month, new_day.day))
                i += 1
        i += 1
    if sum(isinstance(x, Day) for x in parsed_parts) > 20:
        # oops, something got messed up somewhere and a lot of days were added, abort
        parsed_parts = []

def parse_dates(string, past_reference) -> list[Date]:
    print(string)
    # Normalising to a standard format
    # Time should always use ":"
    string = re.sub(R"[0-9]\.[0-9][0-9]", lambda x: x.group(0).replace(".", ":"), string)
    # Date ranges should have spaces:
    string = string.replace("-", " - ")
    # Everything lowercase
    adapted_string = string.lower()
    
    # Split the string using the separator characters
    for separator in separators:
        adapted_string = adapted_string.replace(separator, " ")
    parts = adapted_string.split(" ")
    # Remove empty parts
    parts = [x for x in parts if len(x)]
    parsed_parts = []
    # print(parts)
    
    # Parse parts into objects
    for part in parts:
        parsed_parts.extend(_parse_part(part))
    # Set years on any Date objects parsed so far
    _set_years(parsed_parts, past_reference)
    # print(parsed_parts)

    # Deal with Rangers
    _handle_rangers(parsed_parts)

    # Collapse Months and Days into Dates
    month = None
    days_todo = []
    for i, part in enumerate(parsed_parts):
        if isinstance(part, Month):
            if len(days_todo):
                for day_i in days_todo:
                    day = parsed_parts[day_i]
                    if isinstance(day, Day):
                        parsed_parts[day_i] = Date(None, part.month, day.day)
                month = None
            else:
                month = part
            days_todo = []
        elif isinstance(part, Day):
            if month is not None:
                parsed_parts[i] = Date(None, month.month, part.day)
            else:
                days_todo.append(i)
        else:
            month = None
            days_todo = []
    parsed_parts = [x for x in parsed_parts if not isinstance(x, Month)]
    _set_years(parsed_parts, past_reference)
    _handle_rangers(parsed_parts)
    for part in parsed_parts:
        if isinstance(part, Date):
            print("  ", part)
    return [x for x in parsed_parts if isinstance(x, Date)]
