import requests
import re
import html2text
from bs4 import BeautifulSoup


class Query:
    """Requests the page of a dictionary entry from priberam.pt

    Args:
        term (str): The desired entry.

    Attributes:
        url (str): The url of the page which contains the definitions.
        content (str): The raw html content of the page.
        code (int): Htpp request exception error code.

    Raises:
        Exception: Http request exception.
        ValueError: If term is empty or contains characters other than
        spaces and/or alphanumerics.
    """
    favicon = 'https://cdn.discordapp.com/attachments/398647613886431243/409440249635274754/favicon.png'

    def __init__(self, term=None):
        self.term = term.strip()  
        if not self.term:
            raise ValueError('Entry must not be empty.')
        elif bool(re.search(r'[^\w\s-]', term)):
            raise ValueError('Entry must contain only' + \
                             ' alphanumeric characters and spaces.')
            
        self.url = 'https://www.priberam.pt/dlpo/' + \
                   _urlify(self.term) + '/'
        r = requests.get(self.url)
        self.code = r.status_code
        if self.code != 200:
            raise Exception(str(r.status_code) + 'Error')
        self.content = r.content


class Entry(Query):
    """
    This is a scraper to look up words on priberam.pt
    The definitions and examples might be in pre-1990 agreement Portuguese.
    See the table_of_contents property.

    Raises:
        ValueError: 'No results found.'
    """
    def __init__(self, term):
        super().__init__(term)
        soup = BeautifulSoup(self.content, 'html.parser')
        self.raw = soup.find('div', id='resultados')
        if self.raw.find('div', class_='alert'):
            raise ValueError('No results found.')
        
    @property
    def table_of_contents(self):
        """
        Returns a list containing the morphemes found.
        Each element is a dictionary which contains:
            key         item
            pt_bef      European variant before the agreement
            pt_aft      European variant after the agreement
            br_bef      Brazilian variant before the agreement
            br_aft      Brazilian variant after the agreement
            class       the class of the morpheme
            affect      a boolean that tells if the 1990 agreement
                        affected the morpheme
        """
        r = self.raw.find('div')
        r = r.find('div')
        r = r.find('div')
        for match in r.find_all('span', class_='varpt'):
            if match.parent.name == 'span':
                match.replaceWithChildren()
        r = r.find_all('div', recursive=False)

        morphemes = []
        for _, item in enumerate(r):
            affect = False
            if item.find('span', class_='aAO'):
                affect = True
                pt_before = item.find('span', class_='varpt')
                pt_before = pt_before.find('span', class_='aAO').text
                pt_after = item.find('span', class_='varpt')
                pt_after = pt_after.find('span', class_='dAO').text
                br_before = item.find('span', class_='varpb')
                br_before = br_before.find('span', class_='aAO').text
                br_after = item.find('span', class_='varpb')
                br_after = br_after.find('span', class_='dAO').text
            else:
                pt_before = item.find('span', class_='varpt').text
                pt_after = pt_before
                br_before = item.find('span', class_='varpb').text
                br_after = br_before
            morphology = item.find('em').text
            morpheme = {'pt_bef': pt_before, 'pt_aft': pt_after,
            'br_bef': br_before, 'br_aft': br_after,'class': morphology,
            'affect': affect}
            morphemes.append(morpheme)
        return morphemes

    @property
    def definitions(self):
        """
        Returns a list which contains all the definitions found.
        """
        r = self.raw.find('div')
        r = r.find_all('div', recursive=False)[-1]
        for item in r.find_all('categoria_ext_aao'):
            item.parent.decompose()
        for item in r.find_all('strong'):
            item.parent.decompose()
        for item in r.find_all('span', class_='varpb'):
            item.decompose()
        for item in r.find_all('span', class_='dAO'):
            item.decompose()
        r = r.find_all('div', id='', class_='', recursive=False)
        r = list(map(_html_to_markdown, r))
        return r


def _html_to_markdown(value):
    h = html2text.HTML2Text()
    return h.handle(str(value))


def _urlify(s):
    # Remove all non-word characters
    s = re.sub(r'[^\w\s]', '', s)
    # Replace all runs of whitespace with +
    s = re.sub(r'\s', '+', s)
    return s


def _trim(value):
    if len(value) > 400:
        value = value[:400] + '...'
    return value


if __name__ == "__main__":
    results = Entry('fato')
    for n, defin in enumerate(results.table_of_contents):
        print('{}: {}'.format(n + 1, defin))
        print('{}'.format(results.definitions[n]))
