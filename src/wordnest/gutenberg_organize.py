import re
from time import strptime
from collections import namedtuple

from requests import get

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


"""
  given text of this pattern:
    eBooks:  1 Jun 2019 to 30 Jun 2019 ~ ~ ~ ~
  return a YearMonth named tuple
  return None if not found 

"""
def extract_year_month(text):
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
    response = get(link)
    return response.content.decode('utf-8')

def parse_table(text):
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
    halves = re.split(RE_PATTERNS.listing_start, text)
    book_list = []
    if len(halves) != 2:
        raise Exception('not', 'divided')
    for table_text in re.split(RE_PATTERNS.listing_date_divider, halves[1]):
        book_list += parse_table(table_text)
    return book_list

def gutenberg_text_to_json(text):
    return gutenberg_divide_index_into_tables(text)

def arrange_book_text(text):
    text = remove_extra_whitespace(text)
    text = text.replace('[', '\n[')
    return text

"""
 remove multiple whitespaces in a row
 remove leading and trailing whitespace
"""
def remove_extra_whitespace(text):
    return re.sub(r'(\s){2,}', ' ', text).strip()

"""
 normalize the full text of document
  - normalize line ends

"""
def normalize_text(text):
    return text.replace("\r\n", "\n")

def main():
    retrieved_text = get_file_text('http://gutenberg.readingroo.ms/GUTINDEX.2018')
    normalized_text = normalize_text(retrieved_text)
    print(gutenberg_text_to_json(normalized_text))

if __name__ == '__main__':
    main()