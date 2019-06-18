from requests import get  
import re

listing_start_pattern = "<==LISTINGS==>"
listing_comment_pattern = re.compile("[\s]?[\*]{4}[\s\S]+[\*]{4}[\s]?")
listing_date_pattern = re.compile("([\s\S]+)~ ~ ~ ~")
listing_date_divider_pattern = "~ ~ ~ ~ Posting Dates for the below eBooks:  "

listing_title_line_pattern = re.compile("([\w]+[\s\S]+)[\s]+([0-9]+)")
listing_header_line_pattern = re.compile("TITLE and AUTHOR[\s\S]+EBOOK NO\.")
listing_metadata_pattern = re.compile(" \[((?:).*)\: ((?:).*)\]")

def get_file_text(link):
    response = get(link)
    return response.content.decode('utf-8')

def parse_table(text):
    book_list = []
    current_date = None
    date_match = listing_date_pattern.match(text)
    if date_match:
        current_date = date_match.groups()[0]
    print(current_date)
    for book_text in text.split('\n\n'):
        book_info = parse_book_info(book_text)
        book_list.append(book_info)
    return book_list


def parse_book_info(text):
    metadata = {}
    current_title = None
    book_id = None
    print(text)
    for line in text.splitlines():
        if listing_comment_pattern.match(line) or listing_header_line_pattern.match(line):
            continue
        title_line_match = listing_title_line_pattern.match(line)
        listing_metadata_match = listing_metadata_pattern.match(line)
        if title_line_match:
            current_title = title_line_match.groups()[0].strip()
            book_id = title_line_match.groups()[1].strip()
        elif listing_metadata_match:
            [key, value] = listing_metadata_pattern.search(line).groups()[:2]
            metadata[key.lower()] = value
    if current_title and book_id:
            book_data = ({'title':current_title, 'book_id':book_id})
            book_data.update(metadata)
            return book_data
    else:
            return None

def gutenberg_divide_index_into_tables(text):
    halves = re.split(listing_start_pattern, text)
    book_list = []
    if len(halves) != 2:
        raise Exception('not', 'divided')
    for text in re.split(listing_date_divider_pattern, halves[1]):
        book_list += parse_table(text)
    return book_list

def gutenberg_text_to_json(text):
    print (gutenberg_divide_index_into_tables(text))

def normalize_text(text):
    return text.replace("\r\n", "\n")

if __name__ == '__main__':
    text = get_file_text('http://gutenberg.readingroo.ms/GUTINDEX.2019')
    text = normalize_text(text)
    gutenberg_text_to_json(text)
