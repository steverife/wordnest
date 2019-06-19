import unittest
import sys

sys.path.append('wordnest')
print(sys.path)

import gutenberg_organize as gorg

'''
coverage to add: 
    parse_table
    parse_book_info
    gutenberg_divide_index_into_tables
    arrange_book_text
'''

class test_extract_year_month(unittest.TestCase):
    def test(self):
        text = '~ ~ ~ ~ Posting Dates for the below eBooks:  1 Jun 2019 to 30 Jun 2019 ~ ~ ~ ~'
        date_result = gorg.extract_year_month(text)
        self.assertEqual('2019-06', '%s-%s' %(date_result.year, str(date_result.month).zfill(2))) 

class test_normalize_text(unittest.TestCase):
    def test(self):
        text_in = '1\r\n2\n3\r\n'
        text_fixed = '1\n2\n3\n'
        self.assertEqual(gorg.normalize_text(text_in), text_fixed) 

class test_remove_duplicate_spaces(unittest.TestCase):
    def test(self):
        text_in = '1  2   3 4 \n '
        text_fixed = '1 2 3 4'
        self.assertEqual(gorg.remove_duplicate_spaces(text_in), text_fixed) 

if __name__ == '__main__':
    unittest.main()