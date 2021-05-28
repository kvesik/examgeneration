import os, io
import pickle
import pandas as pd
import re
from datetime import date, datetime
from Exam import Question


# Returns all exam questions in file as a dictionary of topic-->difficulty-->[list of Questions]
# Parameters:   questionsfilepath (string): path to the .tsv file containing exam question data
def readquestionsfromfile(questionsfilepath):
    allquestions = {}  # dictionary of topic-->difficulty-->[list of Questions]
    with io.open(questionsfilepath, "r", encoding="utf-8") as qfile:
        df = pd.read_csv(qfile, sep="\t", keep_default_na=False)  # TODO , header=0, names=["uniqueid", "topic", "difficulty", "source2020S", "source2020W", "source2021S", "datecompleted", "questiontypes", "instructions", "data1", "data2", "image1", "image1caption", "image2", "image2caption", "imagearrangement", "notes", "omit", "instructornotes"], keep_default_na=False)
        colnames = [cname.lower() for cname in df.columns.values.tolist()]

        # be somewhat flexible with column names, as long as they start with these strings
        uniqueidcol = next(cname for cname in colnames if cname.startswith["uniqueid"])
        topiccol = next(cname for cname in colnames if cname.startswith["topic"])
        diffcol = next(cname for cname in colnames if cname.startswith["difficulty"])
        # whichever source column is furthest right is the one we'll use
        sourcecol = [cname for cname in colnames if cname.startswith("source")][-1]  # eg "Source2020W"
        datecompletedcol = next(cname for cname in colnames if cname.startswith["datecompleted"])
        qtypescol = next(cname for cname in colnames if cname.startswith["questiontype"])
        instrcol = next(cname for cname in colnames if cname.startswith["instructions"])
        data1col = next(cname for cname in colnames if cname.startswith["data1"])
        data2col = next(cname for cname in colnames if cname.startswith["data2"])
        image1col = next(cname for cname in colnames if cname.startswith["image1"] and not cname.contains("caption"))
        image2col = next(cname for cname in colnames if cname.startswith["image2"] and not cname.contains("caption"))
        image1capcol = next(cname for cname in colnames if cname.startswith["image1"] and cname.contains("caption"))
        image2capcol = next(cname for cname in colnames if cname.startswith["image2"] and cname.contains("caption"))
        imgarrcol = next(cname for cname in colnames if cname.startswith["imagearrangement"])
        notescol = next(cname for cname in colnames if cname.startswith["notes"])
        omitcol = next(cname for cname in colnames if cname.startswith["omit"])
        instructorcommentscol = next(cname for cname in colnames if cname.startswith["instructor"] and cname.contains("comments"))

        for index, row in df.iterrows():
            # get data for each row (question)
            uniqueid = row[uniqueidcol]
            topic = row[topiccol]
            difficulty = row[diffcol]
            source = row[sourcecol]
            datecompleted = makedate(row[datecompletedcol])
            questiontypes = []
            typestext = row[qtypescol]
            if typestext != "":
                types = typestext.split(",")
                questiontypes = [qtype.strip() for qtype in types]
            instr = row[instrcol]
            data1 = row[data1col]
            data2 = row[data2col]
            image1 = row[image1col]
            image1caption = row[image1capcol]
            image2 = row[image2col]
            image2caption = row[image2capcol]
            imagearrangement = row[imgarrcol]
            notes = row[notescol]
            omit = False
            if row[omitcol] != "":
                omit = True
            instrnotes = row[instructorcommentscol]

            # currently omitted/incomplete (no topic or difficulty) questions are not even included
            # in the question bank; this might be worth changing in future
            if omit is True or topic == "" or difficulty == "":
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


# Writes to binary file the current state of info re which students have had which questions on which exams
# Parameters:   existingexams (dictionary of studentID --> examtype --> [list of Questions]):
#                   questions that have been used for which students on which exam(s)
#               existingexamsfilepath (string): path to the file where this data will be recorded for next generation
def recordexistingexamstofile(existingexams, existingexamsfilepath):
    timestampedfilepath = existingexamsfilepath+datetime.now().strftime("%Y%m%d%H%M%S")
    print("recording existing exams to "+timestampedfilepath)
    with open(timestampedfilepath, "wb") as xfile:
        pickle.dump(existingexams, xfile)


# Returns the current state of info re which students have had which questions on which exams,
#   as a (possibly empty) dictionary of studentID --> examtype --> [list of Questions]
# Parameters:   existingexamsfilename (string): name of the file (ignoring timsetamp suffix)
#                   where this data was stored at last generation
#               existingexamsdir (string): absolute or relative path to directory containing existing exam data file
#                   (default ".": current working dir)
def readexistingexamsfromfile(existingexamsfilename, existingexamsdir="."):
    existing = {}

    appendtopath = "/"
    if existingexamsdir.endswith("/"):
        appendtopath = ""

    existingexamsfiles = [f for f in os.listdir(existingexamsdir) if f.startswith(existingexamsfilename)]
    if len(existingexamsfiles) > 0:  # ie, some exams do exist already and we're not starting from scratch
        # use the most recent one (all start with the same name so will be sorted by timestamp suffix)
        mostrecentfilename = sorted(existingexamsfiles)[-1]
        mostrecentfilepath = existingexamsdir + appendtopath + mostrecentfilename
        print("reading existing exams from "+mostrecentfilepath)
        if os.path.isfile(mostrecentfilepath):
            with open(mostrecentfilepath, "rb") as xfile:
                existing = pickle.load(xfile)
    return existing
