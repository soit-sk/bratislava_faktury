#!/usr/bin/python

import scraperwiki
from urllib import urlopen
from bs4 import BeautifulSoup
from StringIO import StringIO
from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams

def pdf2xml(infile):
    '''
    Return a string of XML representation for given PDF file handle.
    Uses pdfminer to do the conversion and does some final post-processing.
    '''

    outfile = StringIO()

    # See pdf2txt.py
    laparams = LAParams()
    rsrcmgr = PDFResourceManager()
    device = XMLConverter(rsrcmgr, outfile, codec='utf-8', laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page in PDFPage.get_pages(infile, set()):
        interpreter.process_page(page)

    infile.close()
    return outfile.getvalue().replace("\n", "")


def do_page(soup):
    '''
    Return list of lists of ordered cell contents for given XML page.
    '''

    # Wall all textlines, taking a note of their absolute position
    # along with the textual values.
    cells = {}
    for cell in soup.find_all('textline'):
        # The bounding box
        x, y, _, _ = cell.get('bbox').split(',')
        x = float(x)
        y = float(y)

        if not cells.has_key(y):
            cells[y] = {}
        cells[y][x] = cell.get_text()

    # Fetch values from columns and rows sorted by their absolute
    # positions. 0,0 is left bottom corner in PDF.
    ret = []
    for row in reversed(sorted(cells.keys())):
        values = []
        for col in sorted(cells[row].keys()):
            values.append(cells[row][col])
        ret.append(values)

    return ret

# Do the parsing
inf = StringIO(urlopen('http://www.bratislava.sk/register/VismoOnline_ActionScripts/File.ashx?id_org=700026&id_dokumenty=27222').read())
xml = pdf2xml(inf)
soup = BeautifulSoup(xml)

# Walk all pages
values = []
for page in soup.find_all('page'):
    this_page = do_page(page)
    values = values + this_page

# Format into the database
header = values.pop(0)
for row in values:
    scraperwiki.sql.save([], dict(zip(header, row)))
