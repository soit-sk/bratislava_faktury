#!/usr/bin/python

import scraperwiki
from warnings import warn
from urllib import urlopen
from bs4 import BeautifulSoup
from StringIO import StringIO
from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
try:
    from pdfminer.pdfpage import PDFPage
    page_api = True
except ImportError:
    from pdfminer.pdfinterp import process_pdf
    page_api = False

def pdf2xml(infile):
    '''
    Return a string of XML representation for given PDF file handle.
    Uses pdfminer to do the conversion and does some final post-processing.
    '''

    outfile = StringIO()

    # Empirically determined...
    laparams = LAParams()
    laparams.char_margin = 0.4

    # See pdf2txt.py
    rsrcmgr = PDFResourceManager()
    device = XMLConverter(rsrcmgr, outfile, codec='utf-8', laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    if page_api:
        for page in PDFPage.get_pages(infile, set()):
            interpreter.process_page(page)
    else:
        process_pdf(rsrcmgr, device, infile, set())

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
        y = int(float(y))

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

# Fold long columns
for row in values:
    while len(row) > 11:
        row[-2] = row[-2] + ' ' + row.pop()

# Format into the database
header = values.pop(0)
for row in values:
    scraperwiki.sql.save([], dict(zip(header, row)))
