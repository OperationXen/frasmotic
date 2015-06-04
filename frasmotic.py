import os, sys, bisect, re, threading, curses
from datetime import datetime
from string import whitespace as WHITESPACECHARS

MaxLength = 16								#maximum word length allowed into dictionary
MinLength = 6								#minimum word length allowed into dictionary
StripChars = ''
SplitChars = '\' '							#possessive apostraphes
SplitChars+= '|\s'							#all whitespace	
SplitChars+= '|\[|\]|\{|\}|\(|\)|\<|\>|\=|:|;|,|#|\"|\.|\||/|\\|\'|\x27|\`|\&|\x9C|\x9D|\x99|\xE2|\x98'		#all these characters
UseThreading = False
ForceLowerCase = False
ConcatonateChars = '-+_'
HTMLUnescape = False
SortOnLast = False		#option to avoid performance hit on wordlists that are already sorted
IgnoredFileExtensions = [".inc", ".jpg", ".jpeg"]
MaxNumThreads = 1

HEADER = "frasmotic creates wordlists from raw data, for example a site dump or folder of ebooks"
USAGE = "Usage: python frasmotic.py <target file or folder>"
INVALIDPATHERROR = "Target path does not exist. I'm sorry to have caused you such pericombobulation."

####	Pre declare a bunch of lists, this approach allows for parallelism with inserts ###
DictionaryA = []
DictionaryB = []
DictionaryC = []
DictionaryD = []
DictionaryE = []
DictionaryF = []
DictionaryG = []
DictionaryH = []
DictionaryI = []
DictionaryJ = []
DictionaryK = []
DictionaryL = []
DictionaryM = []
DictionaryN = []
DictionaryO = []
DictionaryP = []
DictionaryQ = []
DictionaryR = []
DictionaryS = []
DictionaryT = []
DictionaryU = []
DictionaryV = []
DictionaryW = []
DictionaryX = []
DictionaryY = []
DictionaryZ = []
Dictionary0 = []
Dictionary1 = []
Dictionary2 = []
Dictionary3 = []
Dictionary4 = []
Dictionary5 = []
Dictionary6 = []
Dictionary7 = []
Dictionary8 = []
Dictionary9 = []
DictionaryMisc = []

Dictionaries = dict([\
	('a' , DictionaryA), ('b' , DictionaryB), ('c' , DictionaryC), ('d' , DictionaryD), ('e' , DictionaryE),\
	('f' , DictionaryF), ('g' , DictionaryG), ('h' , DictionaryH), ('i' , DictionaryI), ('j' , DictionaryJ),\
	('k' , DictionaryK), ('l' , DictionaryL), ('m' , DictionaryM), ('n' , DictionaryN), ('o' , DictionaryO),\
	('p' , DictionaryP), ('q' , DictionaryQ), ('r' , DictionaryR), ('s' , DictionaryS), ('t' , DictionaryT),\
	('u' , DictionaryU), ('v' , DictionaryV), ('w' , DictionaryW), ('x' , DictionaryX), ('y' , DictionaryY),\
	('z' , DictionaryZ), ('0' , Dictionary0), ('1' , Dictionary1), ('2' , Dictionary2), ('3' , Dictionary3),\
	('4' , Dictionary4), ('5' , Dictionary5), ('6' , Dictionary6), ('7' , Dictionary7), ('8' , Dictionary8),\
	('9' , Dictionary9), ('?' , DictionaryMisc)\
])

FileList = { }
DictionariesLock = threading.Lock()
ThreadLimiter = threading.BoundedSemaphore(1)

##################################################################################
#	Removes HTML encoding from a given line	(TODO: Optimise)		 #
##################################################################################
def UnescapeLine(Line):
	Line = Line.replace("&lt;", "<")
	Line = Line.replace("&gt;", ">")
	Line = Line.replace("&quot;", "&")
	Line = Line.replace("&amp", "&")
	return(Line)

##################################################################################
# 		Dertermine the correct dictionary for the word in question	 #
##################################################################################
def IdentifyDictionary(Word):
	SortChar = ''
	try:
		if(SortOnLast):							#to use for pre-sorted corpuses
			SortChar = Word[-1::1].lower()				#use cut to get the last character
		else:
			SortChar = Word[0].lower()

		Dictionary = Dictionaries[SortChar]				#attempt to identify a suitable dictionary for the word
	except:
		return(DictionaryMisc)

	return(Dictionary)
##################################################################################
#       	Worker function to perform sorted insert in thread safe way	 #
##################################################################################
def DoInsert(Word):
	try:
		Length = len(Word)						#calculate length once
		if((Length >= MaxLength) or (Length <= MinLength)):		#check word length is valid (these should never change at runtime)
			return							#outside of defined limits, discard

		if(ForceLowerCase):						#check if we have been asked to force to lower case
			Word = Word.lower()					#in which case we force it to lower

		with DictionariesLock:
			Dictionary = IdentifyDictionary(Word)			#identify the right dictionary for this word
	

#obtain semaphore
		Index = bisect.bisect_left(Dictionary, Word)			#work out where it should go

		try:
			if((Index < len(Dictionary)) and (Dictionary[Index] == Word)):				#already there
				return
		except Exception as Message:
			print(Message)

		Dictionary.insert(Index, Word)				#should be unique inserts
	#print("Inserted \"%s\" at %d" % (Word, Index))
#release semaphore
	except Exception as message:
		print(message)
	return

##################################################################################
#		Break a line of text down to words and sort them		 #
##################################################################################
def CrunchLine(Line):
	Line = re.split(SplitChars, Line)				#split based on preselected characters with regex

	for Word in Line:						#iterate through the elements now split out
		if Word == None:					#check that the word was recovered properly
			continue					#discard this one and move to the next

		DoInsert(Word)						#add word to dictionary

##################################################################################
#		Worker thread processes raw data in a thread safe way		 #
##################################################################################
def Worker(Line):

	if(UseThreading):
		ThreadLimiter.acquire()
	try:
		if(HTMLUnescape):				#unescape any html encoding	
			Line = UnescapeLine(Line)
		if(len(StripChars)):				#if we have been given characters to strip
			Line = Line.strip(StripChars)		#strip them before passing the line on to worker

		CrunchLine(Line)				#data suitable for splitting and processing
	except Exception as Message:
		print(Message)
	finally:
		if(UseThreading):
			ThreadLimiter.release()
	return

##################################################################################
#			Process file, line by line				 #
##################################################################################
def CreateWordList(Path, Position):

	with open(Path) as File:			#open the file
		for Line in File:			#iterate through line by line
			if(UseThreading):		#shovel off threads as fast as possible
				#Number = threading.active_count()
				#if(Number > 8):
				#	print(Number)
				Thread = threading.Thread(target = Worker, args=(Line,))
				Thread.start()		#yay for optimisation
			else:
				Worker(Line)

##################################################################################
#		Check a passed file name to see if we should ignore it		 #
##################################################################################
def IgnoreFile(File):
	for Extension in IgnoredFileExtensions:
		if(Extension in File):
			return(True)
	return(False)

def UpdateFileList(FileName, Position):
	FileList[FileName] = Position
	return

def UpdateDisplay():
	pass

##################################################################################
#		Create a resume file, or output the finished article		 #
##################################################################################
def CreateOutputFile(Finished):
	if not Finished:							#if the parameter is false, it means we're writing a resume file
		OutputFile = "words.resume"
		with open(OutputFile, "w") as File:				#this syntax is recommended as "pythonic" apparently
			for FileName, Position in FileList.iteritems():
				File.write("File:%s:%d\n" % (FileName, Position))

	OutputFile = "words.temp"
	with open(OutputFile, "w") as File:
		for Key, List in Dictionaries.iteritems():			#iterate on the list of dictionaries
			for Word in List:					#then iterate through each dictionary
				File.write(Word + '\n')				#outputing the words one at a time

		os.rename("words.temp", "words.lst")
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
	ThreadLimiter = threading.BoundedSemaphore(MaxNumThreads)

def ImportResumeFile():
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

	print(HEADER)
	print(USAGE)

	if(len(sys.argv) > 1):							#check for argument
		Target = sys.argv[1]
	else:
		Target = '.'							#otherwise use current dir

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
