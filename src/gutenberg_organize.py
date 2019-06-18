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
    buffer_lines = []
    for line in text.splitlines():
        if listing_comment_pattern.match(line) or listing_header_line_pattern.match(line):
            return None
        title_line_match = listing_title_line_pattern.match(line)
        listing_metadata_match = listing_metadata_pattern.match(line)
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
            listing_metadata_match = listing_metadata_pattern.match(line)
            if listing_metadata_match:
                [key, value] = listing_metadata_match.groups()[:2]
                metadata[key.strip().lower()] = value.strip()
    if title and book_id:
            title = title.strip()
            book_data = ({'info_text': combined_text, 'title_line': title, 'book_id':book_id.strip()})
            title_parts =  title.split(', by')
            book_data['title'] = title_parts[0]
            if len(title_parts) > 1:
                book_data['author'] = title_parts[1].strip()
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
    return gutenberg_divide_index_into_tables(text)

def arrange_book_text(text):
    text = removed_duplicate_spaces(text)
    text = text.replace('[','\n[')
    return text

def removed_duplicate_spaces(text):
    return text.replace("  ", " ")

def normalize_text(text):
    return text.replace("\r\n", "\n")

if __name__ == '__main__':
    text = get_file_text('http://gutenberg.readingroo.ms/GUTINDEX.2018')
    text = normalize_text(text)
    print(gutenberg_text_to_json(text))
