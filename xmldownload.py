from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
import re
import os
import sys, argparse
import xml.dom.minidom


def read_url(url, start_year, end_year, verbose):
    url = url.replace(" ","%20")
    req = Request(url)
    a = urlopen(req).read()
    indexPage = BeautifulSoup(a, 'html.parser')
    
    baseUrl = 'http://legislation.govt.nz'
    
    #Find any directories to recurse
    dirs = (indexPage.find_all('li', class_='directory'))
    for i in dirs:
        #find link addresses
        link = i.find('a')
        dirUrl = baseUrl + link['href']
        #print(dirUrl)
        
        #Regex to check if this directory is newer than year 2000
        pattern = re.compile("public/([0-9]{4})")
        match = pattern.search(dirUrl)
        #print(match)
        if match:
            #print("Group 1: " + match.group(1))
            year = int(match.group(1))
            if year != None and year >= start_year and year <= end_year:
                #print('Going in to dir ' + dirUrl)
                
                #Recurse in to the directory
                read_url(dirUrl, start_year, end_year, verbose)
                
    #absolute dir the script is in
    root_path = os.path.dirname(os.path.realpath(__file__))
    
    #Find any files to download
    files = (indexPage.find_all('li', class_='file'))
    for i in files:
        #get the link to the file
        link = i.find('a')
        fileUrl = baseUrl + link['href']
        
        #regex to check if the file is XML within the appropriate dir structure
        pattern = re.compile("[0-9]{4}/[0-9]{1,}\.[0-9]{1}/(.*\.xml)")
        match = pattern.search(fileUrl)
        if match:
            #download the file here...
            print("Download file: " + fileUrl)
            req = Request(fileUrl)
            xmlFile = urlopen(req).read()
            xmlString = xmlFile.decode("utf-8")
            
            soup = BeautifulSoup(xmlString, 'lxml-xml')
            title = soup.find('title').contents[0]
            title = re.sub(r"/", "-", title)
            title = re.sub(r"\s", "_", title)
            title += '.xml'
            
            versionPattern = re.compile('/([0-9]{1,}\.[0-9]{1})/')
            versionMatch = versionPattern.search(fileUrl)

            if versionMatch:
                version = versionMatch.group(1)
                version = version[:-2].rjust(4, '0')
                title = version + '_' +  title
            
            #Make the xml pretty for easy reading in the file
            if verbose:
                xmlString = xml.dom.minidom.parseString(xmlString)
                xmlString = xmlString.toprettyxml()

            #set up the directory to save the file
            #this will be relative to the location of the python script!
            #file_path = os.path.join(root_path, 'legislation/data', link['href'][1:-20], title)
            
            linkPathPattern = re.compile('/{1,}(.*)/[0-9]{1,}\.[0-9]{1}/.{16}\.xml')
            linkPathMatch = linkPathPattern.search(link['href'])
            if linkPathMatch:
                linkPath = linkPathMatch.group(1)

            file_path = os.path.join(root_path, 'legislation/xml', linkPath, title)
            
            #If the directory doesn't exist yet, create it recursively
            dirname = os.path.dirname(file_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            
            #Open the new file and write the xml as a utf8 string
            file = open(file_path, 'w')
            file.write(xmlString.encode('ascii', 'ignore').decode('utf-8'))
            file.close()
            print("Downloaded to: " + file_path)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action = "store_true", 
        help = "Pretty print status to console")
    parser.add_argument("-s", "--start_year",
        help = "Collect all legislation from after this year", 
        required = True, type = int)
    parser.add_argument("-e", "--end_year",
        help = "Collect all legislation up until this year", 
        required = True, type = int)

    args = parser.parse_args()

    read_url(
        "http://legislation.govt.nz/subscribe/act/public", 
        args.start_year, 
        args.end_year, 
        args.verbose)
