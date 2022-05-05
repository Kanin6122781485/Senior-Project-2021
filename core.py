# Short Installation Guide 
# Install Python
# Install requests, selenium via pip
# run by 'python *this file name*' in cmd

import csv
import re
import requests
import json
import os
import math
import time 
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

### First Step: get data form NCBI database ###
### All paths and downloadPath may need maintainance if web structure changes###

genome = input("Enter Genome: ").lower() #vibrio parahaemolyticus

driver = webdriver.Chrome()
driver.get('https://www.ncbi.nlm.nih.gov/genome')

#Path to input box in ncbi genome
xpath1 = '//*[@id="term"]'
searchinput = driver.find_element(by=By.XPATH, value=xpath1)

searchinput.send_keys(genome)
searchinput.send_keys(Keys.ENTER)

#Path to Annonation report
xpath2 = '//*[@id="maincontent"]/div/div[5]/div/div[2]/div/a[1]'
searchinput2 = driver.find_element(by=By.XPATH, value=xpath2)
searchinput2.click()

#Path to Download
xpath3 = '//*[@id="maincontent"]/div[2]/div/div/div/div[1]/div[4]/div/div/div/div[1]/button[2]'
searchinput3 = driver.find_element(by=By.XPATH, value=xpath3)
searchinput3.click()

downloadPath = 'C:/Users/User/Downloads/prokaryotes.csv'
targetPath = './' + genome
targetFilePath = targetPath + '/' + genome + '.csv'

while not os.path.exists(downloadPath):
    time.sleep(1)

driver.close()

if not os.path.exists(targetPath):
    os.makedirs(targetPath)

shutil.move(downloadPath, targetFilePath)

### Second Step: read data for NCBI database, get acession number ###

filename = open(targetFilePath, 'r')

file = csv.DictReader(filename)

acessionNumber = []
acessionNumberCount = 0

for row in file:
    if row['Level'] == 'Complete':
        s = row['Replicons'] + ";"
        pattern = ":(.*?);"
        substring = re.split(pattern, s)
        for index, item in enumerate(substring):
            if index%2!=0:
                substring2 = re.split("/", item)
                for number in substring2:
                    acessionNumber.append(number)
                    acessionNumberCount = acessionNumberCount + 1
                    
print("Acession Number Extraction: Done")

### Third Step: call PHASTER API ###

acessionNumberPath = targetPath + '/AcessionNumber'
# Check whether the specified path exists or not

if not os.path.exists(acessionNumberPath):
  # Create a new directory because it does not exist 
    os.makedirs(acessionNumberPath)

for index, number in enumerate(acessionNumber):
    if index%50==0 or index%acessionNumberCount==0:
        print("{:.2f}".format(index*100/acessionNumberCount) + " % Download Done")
# Define the remote file to retrieve
    remote_url = "https://phaster.ca/jobs/" + number + "/detail.txt"
# Define the local filename to save data
    local_file = acessionNumberPath + '/' + number + '.txt'
# Make http request for remote file data
    data = requests.get(remote_url)
# Save file data to local copy
    with open(local_file, 'wb') as file:
        file.write(data.content)

### Fourth Step: Keyword Search, Holin Check ###

keyword = ['hydrolase','lysin','amidase','wall','lysozyme','murami','glycosidase','glucosaminidase']
holin = ['holin']

count2 = 0

sequence = []
sequenceWithHolin = []

for filename in os.scandir(acessionNumberPath):
    #if count2 >= 200: #only 20 file for test 
    if True:
        #print(filename.path)
        file = open(filename.path, "r")
        #count2 = count2 + 1
        lines = file.readlines()
        holinExist = False
        ignoreCheck = False
        matchingKey = False
        intermediateSequence = []
        
        for line in lines:
            if (line.strip() == "<!DOCTYPE html>"):
                ignoreCheck = True #ignore useless file
                break
            
            cleanText = line.strip().split()
            cleanText = [x.lower() for x in cleanText]

            if len(cleanText) > 0:
                matchingHolin = [True for s in cleanText if any(xs in s for xs in holin)]
                if matchingHolin:
                    holinExist = True
                    
                matching = [True for s in cleanText if any(xs in s for xs in keyword)]
                if matching:
                    matchingKey = True
                    print(os.path.splitext(os.path.basename(filename.path))[0]) #Acession Number
                    print(cleanText[-1]) #Sequence
                
                    sequence.append(cleanText[-1].upper())
                    
                    intermediateSequence.append(cleanText[-1].upper())
                    
        ### PUT JSON OUTPUT AROUND HERE SOMEWHERE ###
        
        if not ignoreCheck and matchingKey:
            print(holinExist) #Holin Exist?
            
            for index, item in enumerate(intermediateSequence):
                intermediateSequence[index] = [item, holinExist]
            
                sequenceWithHolin.append(intermediateSequence)
            
                #print(intermediateSequence)

sequenceFileCount = 0
sequenceOutputLimit = 1000
baseSequenceFileName = targetPath + '/SequenceOutput'

if not os.path.exists(baseSequenceFileName):
    os.makedirs(baseSequenceFileName)
    
baseSequenceFileName = baseSequenceFileName + '/SequenceOutput'

for index, item in enumerate(sequence):
    if index%sequenceOutputLimit == 0:
        sequenceFileCount = sequenceFileCount + 1
        SequenceFileName = baseSequenceFileName + str(sequenceFileCount) + '.txt'
        fileOutput = open(SequenceFileName, 'w')
        fileOutput.close()
    SequenceFileName = baseSequenceFileName + str(sequenceFileCount) + '.txt'
    fileOutput = open(SequenceFileName, 'a')
    fileOutput.write(item + "\n\n")

SequenceWithHolinFileName = targetPath + '/sequenceWithHolin.txt'
fileOutput = open(SequenceWithHolinFileName, 'w')
fileOutput.close()

for index, item in enumerate(sequenceWithHolin):
    fileOutput = open(SequenceWithHolinFileName, 'a')
    for index, itemInside in enumerate(item):
        fileOutput.write(itemInside[0] + " " + str(itemInside[1]) + "\n\n")

### Fifth Step: NCBI Conserved Domain ###

# Use SequenceOutput file to CD-Batch Search at https://www.ncbi.nlm.nih.gov/Structure/bwrpsb/bwrpsb.cgi? 

FileCount = 0

for filename in os.scandir('./' + genome + '/SequenceOutput'):
    print (os.path.abspath(filename))
    FileCount = FileCount + 1

    driver = webdriver.Chrome()
    driver.get('https://www.ncbi.nlm.nih.gov/Structure/bwrpsb/bwrpsb.cgi?')

    #Path to Upload File
    xpath4 = '//*[@id="frm_New_Search"]/div/table/tbody/tr/td/table/tbody/tr[1]/td[1]/div[4]/input'
    searchinput4 = driver.find_element(by=By.XPATH, value=xpath4)
    searchinput4.send_keys(os.path.abspath(filename))

    #Path to Submit Form
    xpath5 = '//*[@id="frm_New_Search"]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[3]/input'
    searchinput5 = driver.find_element(by=By.XPATH, value=xpath5)
    searchinput5.click()

    try:
        element = WebDriverWait(driver, 600).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="tbl_DLPanel"]/tbody/tr[3]/td[3]/input'))
        )
    finally:
        driver.find_element(by=By.XPATH, value='//*[@id="hid_dmode_full"]').click()
        driver.find_element(by=By.XPATH, value='//*[@id="tbl_DLPanel"]/tbody/tr[3]/td[3]/input').click()
    
        downloadPath = 'C:/Users/User/Downloads/hitdata.txt'
        targetPath = './' + genome
        targetFilePath = targetPath + '/hitdata' + str(FileCount) + '.txt'

        while not os.path.exists(downloadPath):
            time.sleep(1)

        driver.close()
        shutil.move(downloadPath, targetFilePath)
    
print('Done')