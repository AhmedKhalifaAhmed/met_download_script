courses_ = [
    #Add courses here like this example and make sure you add commas
    #at the end except for the last course name like this example
    'CSEN 701 Embedded Systems',
    'CSEN 702 Microprocessors',
    'CSEN 703 Analysis and Design of Algorithms',
    'DMET 502 Computer Graphics'
]
#====================================================================

import json
import os
import getpass
import requests
import re
from bs4 import BeautifulSoup
import mechanize
from http import cookiejar

# Creating browser and cookiejar
cj = cookiejar.CookieJar()
browser = mechanize.Browser()
browser.set_cookiejar(cj)


class ANSI:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_green(*args, **kwargs):
    print(ANSI.OKGREEN, end='')
    print(*args, end='')
    print(ANSI.ENDC, **kwargs)


def print_blue(*args, **kwargs):
    print(ANSI.OKBLUE, end='')
    print(*args, end='')
    print(ANSI.ENDC, **kwargs)


def print_fail(*args, **kwargs):
    print(ANSI.FAIL, end='')
    print(*args, end='')
    print(ANSI.ENDC, **kwargs)


dict_ = None
downloaded_content_ = 0


def parse_string(s):
    '''Get the actual line from the html text'''
    pattern = r'[A-Za-z0-9]+'
    match = re.findall(pattern, s)
    match = ' '.join(match)
    return match


def get_course(course_name):
    # Making soup
    base_url = 'http://met.guc.edu.eg/Courses/Undergrad.aspx'
    browser.open(base_url)
    soup = BeautifulSoup(browser.response().read(), 'html.parser')
    # Getting all course list anchor tags from the page
    courses_list = soup.find_all('a', class_='coursesLst', href=True)
    course_home_url = None
    # Getting the link to the course's home page
    for course in courses_list:
        if course.get_text() == course_name:
            course_home_url = 'http://met.guc.edu.eg/Courses/'+course.get('href')
            break
    # return None if the course is not found
    if not course_home_url:
        return
    # getting the link to the course material page
    browser.open(course_home_url)
    soup = BeautifulSoup(browser.response().read(), 'html.parser')
    side_menu = soup.find_all('div', class_='blueMiddleSideMenu')[0]
    items = side_menu.find_all('a', href=True)
    for item in items:
        if len(item.get_text().split('Material')) > 1:
            return 'http://met.guc.edu.eg/Courses/{}'.format(item.get('href'))


def mkdict(course_name):
    ''' Returns a new dictionary object for a course to add to the json'''
    url = get_course(course_name)
    if not url:
        return
    return {
        'directory':course_name,
        'url':url
    }


def create_dictionary():
    ''' Creating a list of dictionaries containing course info'''
    global dict_
    courses = []
    for course_name in courses_:
        course = mkdict(course_name)
        if course:
            courses.append(course)
            print('Added course: {}'.format(course_name))
        else:
            print_fail('ERR L62: Could not find course: {}'.format(course_name))
    # Creating the dictionary
    dict_ = {'courses':courses, 'links':[]}
    # Writing the json object
    with open('dictionary.json', 'w') as json_file:
        json.dump(dict_, json_file)

def download(link, path):
    global downloaded_content_
    # Getting the file type from the href
    file_type = link.get('href').split('.')[-1]
    # Make sure the directory exists within the course directory
    try:
        os.mkdir(path)
        # Logging
        print_blue('Created directory', path)
    except FileExistsError:
        pass
    filename = '{}/{}.{}'.format(path, link.get('name'), file_type)
    url = 'http://met.guc.edu.eg/'+link.get('href')
    # Downloading the file
    browser.retrieve(url, filename)[0]
    # Printing log
    print_green('Downloaded {} @ \'{}\''.format(link.get('name'), filename))
    downloaded_content_ += 1


def load_links(page):
    global dict_
    #global dict_
    # Getting existing links
    links = dict_.get('links')
    # Making soup
    url = page.get('url')
    browser.open(url)
    soup = BeautifulSoup(browser.response().read(), 'html.parser')
    # Getting the badge containers
    containers = soup.find_all('div', class_='badgeDetails')
    for container in containers:
        # Getting the directory name to use later to download content
        directory_name = container.find_all('h3')[0].get_text()
        directory_name = parse_string(directory_name)
        # Making sure the directory exists
        # Getting the material list
        material_list = container.find_all('ul', class_='materialList')[0]
        # Checking each link in the list
        for item in material_list.find_all('a', href=True):
            href = item.get('href').split('/')[1]
            if not href in links: # New content found
                name = item.get_text()
                name = parse_string(name)
                new_link = {'name':name, 'href':href}
                # Downloading the file
                path = page.get('directory')+'/'+directory_name
                download(new_link, path)
                # Adding the link to the page dictionary
                links.append(href)


def main():
    # Log in
    browser.open('http://met.guc.edu.eg')
    browser.select_form(nr=0)
    browser.form['LoginUserControl1$usernameTextBox'] = str(input('Email: '))
    browser.form['LoginUserControl1$passwordTextBox'] = getpass.getpass(prompt='Password: ')
    browser.submit()
    # Nerd stuff
    global dict_
    # Checking for the json dictionary
    try:
        with open('dictionary.json', 'r') as json_file:
            dict_ = json.load(json_file)
    except Exception: # File not found or corrupt jsonw
        create_dictionary()
    # Looping through the links for the course pages
    for page in dict_.get('courses'):
        # Making sure the course directory exists
        try:
            dir_name = page.get('directory')
            os.mkdir(dir_name)
            print_blue('Created directory {}'.format(dir_name))
        except FileExistsError:
            pass
        # Loading the content links into the dictionary and download new content
        load_links(page)
    # Printing log
    print('downloaded {} item(s).'.format(downloaded_content_))
    # Writing the new data to the json file
    with open('dictionary.json', 'w') as json_file:
        json.dump(dict_, json_file)


if __name__ == '__main__':
    main()
