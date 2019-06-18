from requests import get  
import re

listing_start_pattern = "<==LISTINGS==>"
listing_comment_pattern = re.compile("[\s]?[\*]{4}[\s\S]+[\*]{4}[\s]?")
listing_date_divider_pattern = re.compile("~ ~ ~ ~ ([\s\S]+)~ ~ ~ ~")
listing_title_line_pattern = re.compile("([\w]+[\s\S]+)[\s]+([0-9]+)")
listing_header_line_pattern = re.compile("TITLE and AUTHOR[\s\S]+EBOOK NO\.")
listing_metadata_pattern = re.compile(" \[((?:).*)\: ((?:).*)\]")

def get_file_text(link):
    response = get(link)
    return response.content.decode('utf-8')

def gutenberg_divide_index_into_parts(text):
    halves = re.split(listing_start_pattern, text)
    book_list = []
    if len(halves) != 2:
        raise Exception('not', 'divided')
    current_date = None
    current_title = None
    book_id = None
    metadata = {}
    for line in halves[1].split('\n'):
        if listing_comment_pattern.match(line) or listing_header_line_pattern.match(line):
            continue
        divider_match =  listing_date_divider_pattern.match(line)
        title_line_match = listing_title_line_pattern.match(line)
        listing_metadata_match = listing_metadata_pattern.match(line)
        if divider_match:
            current_date = divider_match.group(0).strip()
        elif title_line_match:
            current_title = title_line_match.groups()[0].strip()
            book_id = title_line_match.groups()[1].strip()
        elif listing_metadata_match:
            [key, value] = listing_metadata_pattern.search(line).groups()[:2]
            metadata[key.lower()] = value
        elif len(line.strip()) == 0:
            if current_title and book_id and current_date:
                book_data = ({'title':current_title, 'book_id':book_id, 'date_info':current_date})
                book_data.update(metadata)
                book_list.append(book_data)
                metadata = {}
    return book_list

def gutenberg_text_to_json(text):
    print (gutenberg_divide_index_into_parts(text))


if __name__ == '__main__':
    text = get_file_text('http://gutenberg.readingroo.ms/GUTINDEX.2019')
    print(gutenberg_text_to_json(text))
