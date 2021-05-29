import os, io
import pickle
import pandas as pd
import re
from datetime import date, datetime
from src.Exam import Question


# Returns all exam questions in file as a dictionary of topic-->difficulty-->[list of Questions]
# Parameters:   questionsfilepath (string): path to the .tsv file containing exam question data
def readquestionsfromfile(questionsfilepath):
    allquestions = {}  # dictionary of topic-->difficulty-->[list of Questions]
    with io.open(questionsfilepath, "r", encoding="utf-8") as qfile:
        df = pd.read_csv(qfile, sep="\t", header=0, names=["uniqueid", "topic", "difficulty", "source2020S", "source2020W", "datecompleted", "questiontypes", "instructions", "data1", "data2", "image1", "image1caption", "image2", "image2caption", "imagearrangement", "notes", "omit", "instructornotes"], keep_default_na=False)
        for index, row in df.iterrows():
            uniqueid = row["uniqueid"]
            topic = row["topic"]
            difficulty = row["difficulty"]
            source = row["source2020W"]
            datecompleted = makedate(row["datecompleted"])
            questiontypes = []
            typestext = row["questiontypes"]
            if typestext != "":
                types = typestext.split(",")
                questiontypes = [qtype.strip() for qtype in types]
            instr = row["instructions"]
            data1 = row["data1"]
            data2 = row["data2"]
            image1 = row["image1"]
            image1caption = row["image1caption"]
            image2 = row["image2"]
            image2caption = row["image2caption"]
            imagearrangement = row["imagearrangement"]
            notes = row["notes"]
            omit = False
            if row["omit"] != "":
                omit = True
            instrnotes = row["instructornotes"]

            # currently the omitted questions are not even included in the question bank;
            # this might be worth changing in future
            if omit is True or topic == "":
                continue

            if topic not in allquestions.keys():
                allquestions[topic] = {}
            if difficulty not in allquestions[topic].keys():
                allquestions[topic][difficulty] = []

            currentq = Question(uniqueid, topic, difficulty, source, datecompleted, questiontypes, instr, data1, data2, image1, image1caption, image2, image2caption, imagearrangement, notes, omit, instrnotes)
            allquestions[topic][difficulty].append(currentq)

    return allquestions


# Returns a date object corresponding to the input date (or None if no yyyy-mm-dd found in input)
# Parameters:   thedate (string *or* date object): the date in question, which must be either a date object
#                   or, if a string, must contain a substring of the form yyyy-mm-dd
def makedate(thedate):
    if isinstance(thedate, date):
        return thedate
    else:  # must be a string
        returndate = None
        matches = re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", thedate)
        if len(matches) > 0:
            returndate = date.fromisoformat(matches[0])
        return returndate


# Writes to binary file the current state of info re which students have had which questions on which exams_old
# Parameters:   existingexams (dictionary of studentID --> examtype --> [list of Questions]):
#                   questions that have been used for which students on which exam(s)
#               existingexamsfilepath (string): path to the file where this data will be recorded for next generation
def recordexistingexamstofile(existingexams, existingexamsfilepath):
    timestampedfilepath = existingexamsfilepath+datetime.now().strftime("%Y%m%d%H%M%S")
    print("recording existing exams_old to "+timestampedfilepath)
    with open(timestampedfilepath, "wb") as xfile:
        pickle.dump(existingexams, xfile)


# Returns the current state of info re which students have had which questions on which exams_old,
#   as a dictionary of studentID --> examtype --> [list of Questions]
# Parameters:   existingexamsfilepath (string): path to the file where this data was stored at last generation
def readexistingexamsfromfile(existingexamsfilepath):
    existing = {}

    existingexamsfiles = [f for f in os.listdir('..') if f.startswith(existingexamsfilepath)]
    if len(existingexamsfiles) > 0:  # ie, if some exams_old do exist already and we're not starting from scratch
        mostrecentfilepath = sorted(existingexamsfiles)[-1]
        print("reading existing exams_old from "+mostrecentfilepath)
        if os.path.isfile(mostrecentfilepath):
            with open(mostrecentfilepath, "rb") as xfile:
                existing = pickle.load(xfile)
    return existing
