import os, sys, bisect, re
from datetime import datetime
from string import whitespace as WHITESPACECHARS

MaxLength = 16								#maximum word length allowed into dictionary
MinLength = 3								#minimum word length allowed into dictionary
SplitChars = '\' '							#possessive apostraphes
SplitChars+= '|\s'							#all whitespace	
SplitChars+= '|(\[\]\{\}\(\)\<\>\=\:\;\.\,\")'				#all these characters
ForceLowerCase = True
Dictionary = []

##################################################################################
def CreateWordList(Path):
	List = []							#build a list of words in this file

	with open(Path) as File:					#open the file
		for Line in File:					#iterate through line by line
			Line = Line.strip('\r\n')			#get rid of newlines and carriage returns

			Line = re.split(SplitChars, Line)		#split based on preselected characters
			for Word in Line:
				Length = len(Word)
				if((Length <= MaxLength) and (Length >= MinLength)):
					if(ForceLowerCase):
						Word = Word.lower()
					List.append(Word)		#add word to dictionary
	return(List)							#list can contain duplicates at this stage	

##################################################################################
def InsertWords(Words):							#insert into sorted dictionary, uniquely
	for Word in Words:	
		Index = bisect.bisect_left(Dictionary, Word)		#work out where it should go
		
		#insert if going at the end, or different to current index occupant
		if(Index >= len(Dictionary) or Dictionary[Index] != Word):
			Dictionary.insert(Index, Word)			#should be unique inserts

##################################################################################
if(len(sys.argv) > 1):							#check for argument
	RootFolder = sys.argv[1]					#use arg as start path
else:
	RootFolder = '.'						#otherwise use current dir

print("Starting in %s" % RootFolder)

for SubDirectory, Directory, Files in os.walk(RootFolder):		#walk from start path

	if(len(Files) > 0):
		print("%s\r\nWords\tTime(ms)\tFile" % SubDirectory)
	else:
		print("%s (no files)" % SubDirectory)

	for File in Files:						#for each file found
		Start = datetime.now()					#get the starting time
		Path = SubDirectory + os.sep + File			#get its absolute path
		Words = CreateWordList(Path)				#create wordlist from file
		
		if(len(Words)):
			InsertWords(Words)
			End = datetime.now()					#get the ending time		
			Elapsed = (End - Start).microseconds			#calculate how long it took
			print("%d\t%d\t\t%s") % (len(Words), Elapsed, File) 	#output number of unique words recovered from file
		
Output = open("word.lst", "w")
for Word in Dictionary:
	Output.write(Word + '\n')
Output.close()
##################################################################################
