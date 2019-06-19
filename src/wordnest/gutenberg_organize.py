"""
script for downloading and parsing gutenberg.org catalog of book files
turns flat text files into json

list of books
  each book is a dictionary with metadata book_id and title
  as well as optionals such as subtitle, language
"""
import re
import json
from time import strptime
from collections import namedtuple

from requests import get

class UnexpectedParsingResult(Exception):
    """
    for when our regex patterns fail on the text docs
    """
    pass

class Patterns:
    listing_start = "<==LISTINGS==>"
    listing_comment = re.compile(r"[\s]?[\*]{4}[\s\S]+[\*]{4}[\s]?")
    listing_date = re.compile(r"to (?P<date>[0-9]{1,2}) (?P<month>[A-Z]{1}[a-z]{2,3}) (?P<year>[0-9]{4})")
    listing_date_divider = r"~ ~ ~ ~ Posting Dates for the below eBooks:  "
    listing_title_line = re.compile(r"([\w]+[\s\S]+)[\s]+([0-9]+)")
    listing_header_line = re.compile(r"TITLE and AUTHOR[\s\S]+EBOOK NO\.")
    listing_metadata = re.compile(r" \[((?:).*)\: ((?:).*)\]")

RE_PATTERNS = Patterns()
YearMonth = namedtuple('year_month', ['year', 'month'])

def extract_year_month(text):
    """
      given text of this pattern:
        eBooks:  1 Jun 2019 to 30 Jun 2019 ~ ~ ~ ~
      return a YearMonth named tuple
      return None if not found
    """
    match = RE_PATTERNS.listing_date.search(text)
    if match:
        try:
            month_text = match.groupdict().get('month')
            if len(month_text) == 3:
                month_number = strptime(match.groupdict().get('month'), '%b').tm_mon
            else:
                month_number = strptime(match.groupdict().get('month'), '%B').tm_mon
        except:
            month_number = None
        return YearMonth(year=int(match.groupdict().get('year')), month=month_number)
    return None

def get_file_text(link):
    """
    download text file
    """
    response = get(link)
    return response.content.decode('utf-8')

def parse_table(text):
    """
    given text of month table of book listings
    return list of books
    """
    book_list = []
    current_date = None
    current_date = extract_year_month(text)
    for book_text in text.split('\n\n'):
        book_info = parse_book_info(book_text)
        if not book_info:
            continue
        book_info['year_month'] = current_date
        book_list.append(book_info)
    return book_list

def parse_book_info(text):
    """
    given text of book info return dictionary of book metadata
    return None on failure
    """
    metadata = {}
    book_id = None
    buffer_lines = []
    for line in text.splitlines():
        if RE_PATTERNS.listing_comment.match(line) or RE_PATTERNS.listing_header_line.match(line):
            return None
        title_line_match = RE_PATTERNS.listing_title_line.match(line)
        listing_metadata_match = RE_PATTERNS.listing_metadata.match(line)
        if title_line_match:
            book_id = title_line_match.groups()[1].strip()
            buffer_lines.append(title_line_match.groups()[0].strip())
        else:
            buffer_lines.append(line)
    combined_text = ' '.join(buffer_lines)
    combined_text = arrange_book_text(combined_text)
    arranged_lines = combined_text.splitlines()
    if not arranged_lines:
        return None
    title = arranged_lines[0]
    if len(arranged_lines) > 1:
        for line in arranged_lines[1:]:
            listing_metadata_match = RE_PATTERNS.listing_metadata.match(line)
            if listing_metadata_match:
                [key, value] = listing_metadata_match.groups()[:2]
                metadata[key.strip().lower()] = value.strip()
    if title and book_id:
        title = title.strip()
        book_data = ({'info_text': combined_text, 'title_line': title, 'book_id':book_id.strip()})
        title_parts = title.split(', by')
        book_data['title'] = title_parts[0]
        if len(title_parts) > 1:
            book_data['author'] = title_parts[1].strip()
        book_data.update(metadata)
        return book_data
    return None

def gutenberg_divide_index_into_tables(text):
    """
    parse text of full doc and for each month table create a book list
    combine all book lists as one list and return
    """
    halves = re.split(RE_PATTERNS.listing_start, text)
    book_list = []
    if len(halves) != 2:
        raise UnexpectedParsingResult
    for table_text in re.split(RE_PATTERNS.listing_date_divider, halves[1]):
        book_list += parse_table(table_text)
    return book_list

def gutenberg_text_to_json(text):
    """
    take text document and return json representation
    list of books, each book is a dictionary of book metadata

    """
    return json.dumps(gutenberg_divide_index_into_tables(text))

def arrange_book_text(text):
    """
    clean up book info text so that metadata are on separate lines
    """
    text = remove_extra_whitespace(text)
    text = text.replace('[', '\n[')
    return text

def remove_extra_whitespace(text):
    """
    remove multiple whitespaces in a row
    remove leading and trailing whitespace
    """
    return re.sub(r'(\s){2,}', ' ', text).strip()

def normalize_text(text):
    """
    normalize the full text of document
    normalize line ends
    """
    return text.replace("\r\n", "\n")

def main():
    """
    example of how to run on one text doc and return json representation
    """
    retrieved_text = get_file_text('http://gutenberg.readingroo.ms/GUTINDEX.2018')
    normalized_text = normalize_text(retrieved_text)
    print(gutenberg_text_to_json(normalized_text))

if __name__ == '__main__':
    main()
