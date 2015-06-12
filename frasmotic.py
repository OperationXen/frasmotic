import os, sys, re, unicodedata
from sortedcontainers import SortedDict
from datetime import datetime
from docopt import docopt

DocString = """Usage: frasmotic.py SOURCE [-sptu] [--min=N --max=N] 

Generates a wordlist based on the contents of files

Arguments:
  SOURCE  Source file or folder path (required)

Options:
  -h --help  		Print this help text
  -s --suppress  	Suppress single word generation
  -u --html  		Unescape HTML characters first [default: false]
  -p --phrases  	Generate phrase dictionary
  -t --linktitles  	Create compound dictionary from link titles
  --singlewords=(true|false)  Generate a dictionary of 1-grams
  --min=N  		Minimum word length [default: 5]
  --max=N  		Maximum word length [default: 32]

  --version  Print current version information	
"""
Target = "."

MaxLength = 32								#maximum word length allowed into dictionary
MinLength = 5								#minimum word length allowed into dictionary

StripChars = '[]'
SplitChars = '\' '							#possessive apostrophes
SplitChars+= '|\s'							#all whitespace	
SplitChars+= '|\[|\]|\{|\}|\(|\)|\<|\>|\=|:|;|,|#|\"|\.|\||/|\\|\'|\x27|\`|\&|\x9C|\x9D|\x99|\xE2|\x98'		#all these characters
AlphaChars = '[a-zA-Z]'
QuotesString = '(\".+?\")'
TitleString = '" ?>.+?</a'
LinkString = '<a href=".*?".*?>.*?</'
LinkTitleString = '">.*?</\Z'
WikiLinkString = '\[\[.*?\]\]'

ConcatonateChars = '-+_'

StripLine = False
HTMLUnescape = True

DoSingleWords = True
ForceLowerCase = True
GroupQuotations = False
GroupTitles = False
GroupLinkText = False
GroupWikiLinks = False

OmitNumericOnly = True
IgnoredFileExtensions = [".inc", ".jpg", ".jpeg"]
UseResumeFile = False

# Text strings (usage etc)
INVALIDPATHERROR = "Target path does not exist."

SingleWords = SortedDict()
CompoundWords = SortedDict()

FileList = { }
#Precompiled regexes
reSplitter = re.compile(SplitChars)
reAlphaChars = re.compile(AlphaChars)
reQuotes = re.compile(QuotesString)
reTitles = re.compile(TitleString)
reLinks = re.compile(LinkString)
reLinkTitles= re.compile(LinkTitleString)
reWikiLinks = re.compile(WikiLinkString)

##################################################################################
#	Removes HTML encoding from a given line	(TODO: Optimise)		 #
##################################################################################
def UnescapeLine(Line):
	Line = Line.replace("&lt;", "<")
	Line = Line.replace("&gt;", ">")
	Line = Line.replace("&quot;", "\"")
	Line = Line.replace("&amp", "&")
	Line = Line.replace("&#039;", "\'")
	Line = Line.replace("%22", "\"",)
	Line = Line.replace("%20", " ",)
	return(Line)

##################################################################################
#		Convert non-ascii chars in words to ascii			 #
##################################################################################
def Transliterate(Line):
	Line = ''.join(c for c in unicodedata.normalize('NFD', Line) if unicodedata.category(c) != 'Mn	')
	return(Line)

##################################################################################
#       	Worker function to perform sorted insert in thread safe way	 #
##################################################################################
def DoInsert(Word, Dictionary, LowerCase):
	try:
		Length = len(Word)						#calculate length once
		if((Length >= MaxLength) or (Length <= MinLength)):		#check word length is valid (never change at runtime)
			return							#outside of defined limits, discard

		if(LowerCase):							#check if we have been asked to force to lower case
			Word = Word.lower()					#in which case we force it to lower

		if(Word not in Dictionary):					#don't duplicate words
			Dictionary[Word] = 0					#add it to the dictionary structure, value 0

	except Exception as message:
		print(message)
	return

##################################################################################
#      	Return a string with the first letter of each word capitalised		 #
##################################################################################
def CapitaliseString(String):
	Output = ''
	try:
		Words = String.split(' ')
		CapitalisedWords = []
		for Word in Words:
			if(len(Word) > 2):	
				TitleCaseWord = Word[0].upper() + Word[1:]
			else:
				TitleCaseWord = Word[0].upper()
			CapitalisedWords.append(TitleCaseWord)
		Output = ''.join(CapitalisedWords)
	except Exception as Message:
		pass

	return(Output)

##################################################################################
#		Break a line of text down to words and sort them		 #
##################################################################################
def CrunchLine(Line):
	
	if(HTMLUnescape):
		Line = UnescapeLine(Line)

	if(DoSingleWords):
		SplitLine = reSplitter.split(Line)				#precompiled regex split function
		for Word in SplitLine:						#iterate through the elements now split out
			if(Word == None):					#check that the word was recovered properly
				continue					#discard this one and move to the next

			if(OmitNumericOnly):					#check word for alpha characters before adding it
				if(reAlphaChars.search(Word) == None):		#words without alpha characters get excluded
					continue				#more efficient than using error handling approach...
	
			DoInsert(Word, SingleWords, ForceLowerCase)		#add word to dictionary


	if(GroupQuotations):
		Quotes = reQuotes.findall(Line)
		for Quote in Quotes:
			if(Quote != None):
				Quote = re.sub('[\"\-\.,\xe2]', '', Quote)

				Output = CapitaliseString(Quote)
				UpperQuote = re.sub('[\s]', '', Output)	#remove all whitespace
				DoInsert(UpperQuote, CompoundWords, True)

				Quote = re.sub('[\s]', '', Quote)	#remove all whitespace
				DoInsert(Quote, CompoundWords, False)

	if(GroupTitles):
		Titles = reTitles.findall(Line)
		for Title in Titles:
			if(Title == None):
				break
			
			Title = re.sub('(\A" ?>)|(</a)', '', Title)
			Title = re.sub('\(.*\)', '', Title)
			Title = UnescapeLine(Title)
			
			print(Title)

	if(GroupLinkText):
		Links = reLinks.findall(Line)
		if(Links != []):
			print(Links)
			for Link in Links:
				LinkTitle = reLinkTitles.findall(Link)
				for Title in LinkTitle:
					Title = re.sub('(\A"?>)|(</\Z)', '', Title)	#remove the functional chars left at the start and end
					Title = re.sub('\(.*?\)', '', Title)		#remove stuff in brackets
					Title = UnescapeLine(Title)			#remove encoded html
					Title = re.sub('\s', '', Title) 		#remove whitespace
					Title = CapitaliseString(Title)
					DoInsert(Title, CompoundWords, False)
					DoInsert(Title, CompoundWords, True)
					Title = re.sub('\W', '', Title)
					DoInsert(Title, CompoundWords, False)
	
	if(GroupWikiLinks):
		Links = reWikiLinks.findall(Line)
		if(Links != []):
			for Link in Links:
				Link = re.sub('(\A\[\[)|(\]\]\Z)', '', Link)
				for Title in re.split('|', Link):
					if(not ":" in Title):
						Title = re.sub('\(.*?\)', '', Title)		#remove stuff in brackets
						Title = CapitaliseString(Title)
						Title = re.sub('[\s\W]', '', Title) 		#remove whitespace and punctuation
						DoInsert(Title, CompoundWords, True)
						DoInsert(Title, CompoundWords, False)

##################################################################################
#			Process file, line by line				 #
##################################################################################
def CreateWordList(Path, Position):
	with open(Path) as File:						#open the file
		for Line in File:						#iterate through line by line
			try:
				if(HTMLUnescape):				#unescape any html encoding	
					Line = UnescapeLine(Line)
				if(StripLine):					#if we want to strip various chars
					Line = re.sub(StripChars, '', Line)	#substitute them with nothing

				CrunchLine(Line)				#data suitable for splitting and processing
			except Exception as Message:
				print(Message)
		return
##################################################################################
#		Check a passed file name to see if we should ignore it		 #
##################################################################################
def IgnoreFile(File):
	for Extension in IgnoredFileExtensions:
		if(Extension in File):
			return(True)
	return(False)

##################################################################################
#	Update the list of files done with the current position and file	 #
##################################################################################
def UpdateFileList(FileName, Position):
	FileList[FileName] = Position
	return

##################################################################################
#			TODO: Write proper display				 #
##################################################################################
def UpdateDisplay():
	pass

##################################################################################
#		Create a resume file, or output the finished article		 #
##################################################################################
def CreateOutputFile(Finished):
	if not Finished and UseResumeFile:					#if the parameter is false, it means we're writing a resume file
		OutputFile = "words.resume"
		with open(OutputFile, "w") as File:				#this syntax is recommended as "pythonic" apparently
			for FileName, Position in FileList.iteritems():
				File.write("File:%s:%d\n" % (FileName, Position))

	OutputFile = "singlewords.temp"
	with open(OutputFile, "w") as File:
		for Word in SingleWords.iteritems():			#iterate on the sorted dictionary of words
			File.write(Word[0] + '\n')				#outputing the words one at a time to the file

		os.rename("singlewords.temp", "singlewords.lst")
	return

##################################################################################
#			Process a given file into a wordlist		         #
##################################################################################
def ProcessFile(File):
	try:
		Position = FileList[File]			#look up the file in the list of processed files
	except Exception as Message:				#unable to find it
		Position = 0					#start at the beginning
		UpdateFileList(File, Position)			#add the file to the file list (mark as position 0)

	if(IgnoreFile(File)):					#omit certain file extensions
		return
	if(Position == -1):					#already completed this file
		print("Skipping %s" % File)
		return

	Start = datetime.now()					#get the starting time
	CreateWordList(File, Position)				#create wordlist from file
	UpdateFileList(File, -1)				#mark file as completed in internal records (used to resume)
	End = datetime.now()					#get the ending time	
	
	Elapsed = (End - Start).seconds				#calculate how long it took
	CreateOutputFile(False)
	print("%s\t\t%d") % (File, Elapsed)	 		#output number of unique words recovered from file

##################################################################################
#			Initialise things that need initialisation		 #
##################################################################################
def Init():
	try:
		Options = docopt(DocString, version="0.2")

		Target = Options["SOURCE"]
		DoSingleWords = not Options["--suppress"]
		MaxLength = Options["--max"]
		MinLength = Options["--min"]
		HTMLUnescape = Options["--html"]

		print(DoSingleWords)

	except Exception as Message:
		print("Exception:" + str(Message))
	return

##################################################################################
#			Import an existing resume file				 #
##################################################################################
def ImportResumeFile():
	if(not UseResumeFile):
		return

	try:
		with open("words.resume", "r") as File:
			print("Found resume file...")
			for Line in File:
				if("File:" not in Line):
					return
				FileName = Line.split(':')[1]
				Position = Line.split(':')[2]

				FileName = FileName.strip("\'\n")
				Position = Position.strip("\'\n")
				FileList[FileName] = int(Position)

	except Exception as Message:
#		print Message
		print("Error with resume file")
		return

##################################################################################
#				Main function				         #
##################################################################################
def Main():
	Init()
	ImportResumeFile()

	if(os.path.isfile(Target)):						#called on a single file
		ProcessFile(Target)

	elif(os.path.isdir(Target)):						#we've been handed a folder
		print("Starting in \"%s\" folder:" % os.path.relpath(Target))
		for SubDirectory, Directory, Files in os.walk(Target):		#walk from start path
			if(len(Files) > 0):
				print("%s:" % os.path.abspath(Target))
#				print("%s\r\nFile\t\tTime(s)\t\tWords\t\t%% complete" % SubDirectory)	#new subdirectory, print header
			else:
				print("%s (no files)" % SubDirectory)		#no files, only directories

			for File in Files:					#for each file found
				File = SubDirectory + os.sep + File		#get its absolute path
				File = os.path.abspath(File)
				ProcessFile(File)

	else:
		print(INVALIDPATHERROR)
		exit(0)

	exit(1)

Main()
##################################################################################
#				End of code					 #
##################################################################################


#concatonate phrases and quotes based on " character
#link titles?
#concatonate hyphonated words
#concatonate titles and names
#preserve cases in these cases
#corpuses - wikiquote, wiktionary, urban dictionary
