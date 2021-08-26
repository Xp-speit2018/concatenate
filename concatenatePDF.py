import os
import PyPDF2

import imaplib
import json
import time

from email.parser import BytesParser

def mergePDFs(pdfNames, output):
    writer = PyPDF2.PdfFileWriter()
    for pdfName in pdfNames:
        reader = PyPDF2.PdfFileReader(pdfName)
        for page in range(reader.getNumPages()):
            writer.addPage(reader.getPage(page))
    
    with open(output, 'wb') as outFile:
        writer.write(outFile)

def fetchPDFs():
    with open('./config.json') as jsonFile:
        config = json.load(jsonFile)

    M = imaplib.IMAP4_SSL(config["IMAP"])
    M.login(config["email"],config["password"])

    myFolder = M.list()[1][0][-17:-1]

    # print(myFolder+b'/'+bytes(config["unhandledFolder"], 'utf-8'))
    unhandledFolder = myFolder+b'/'+bytes(config["unhandledFolder"], 'utf-8')
    handledFolder = myFolder+b'/'+bytes(config["handledFolder"], 'utf-8')

    result, message = M.select(unhandledFolder)
    typ, data = M.search(None, 'ALL')

    mailNums = data[0].split()
    if not mailNums:
        return None
    
    directory = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    os.mkdir(directory)
    directory += '/'

    for mailNum in mailNums:
        typ, data = M.fetch(mailNum, '(RFC822)')
        msg = BytesParser().parsebytes(data[0][1])
        for part in msg.walk():
            fileName = part.get_filename()
            if fileName and ".pdf" in fileName:
                print(fileName)
                fileContent = part.get_payload(decode=True)
                with open(directory+fileName, 'wb') as file:
                    file.write(fileContent)
                    print("File Saved：{}".format(fileName))
        M.copy(mailNum, handledFolder)
        M.store(mailNum, '+FLAGS', '\\Deleted')
    
    M.expunge()
    M.close()
    M.logout()

    return directory
                    

if __name__ == '__main__':

    directory = fetchPDFs()
    if directory:
        pdfNames = []
        for fileName in os.listdir(directory):
            if '.pdf' in fileName:
                pdfNames.append(directory+fileName)
        
        if pdfNames:
            mergePDFs(pdfNames, output=directory+'concatenated.pdf')
            print("Concatenated pdf generated at:: ", directory+'concatenated.pdf')     
    else:
        print("No mails unhandled!")

    
