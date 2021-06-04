# -*- coding: utf-8 -*-
"""
written May-July 2020 by Kaili Vesik: kvesik@gmail.com
updated Sep-Oct 2020 by Kaili Vesik
updated May 2021 by Kaili Vesik
"""

import os
import sys
import io
import pickle
import subprocess
import pandas as pd
import re
from datetime import date, datetime, timedelta
from Exam import Question
# from generateexams_beta20210603 import WILD  # TODO


WILD = "WILD"


# Returns the date object which is the most recent Friday strictly before (not equal to) the input date
# Parameters:   thedate (date): the date whose previous Friday to find
def getfrioflastweek(thedate):
    dayofweek = thedate.weekday()  # Monday=0 through Sunday=6
    prevfri = thedate - timedelta(days=(dayofweek+3))
    return prevfri


# Returns the date object which is the closest future Friday after (or equal to) the input date
# Parameters:   thedate (date): the date whose next (or current) Friday to find
def getfriofthisweek(thedate):
    dayofweek = thedate.weekday()  # Monday=0 through Sunday=6
    daystoadd = (11-dayofweek) % 7
    nextfri = thedate + timedelta(days=daystoadd)
    return nextfri




# Returns all exam questions in file as a dictionary of topic-->difficulty-->[list of Questions]
# Parameters:   questionsfilepath (string): path to the .tsv file containing exam question data
def readquestionsfromfile(questionsfilepath):
    allquestions = {}  # dictionary of topic-->difficulty-->[list of Questions]
    with io.open(questionsfilepath, "r", encoding="utf-8") as qfile:
        df = pd.read_csv(qfile, sep="\t", keep_default_na=False)  # read column names from file
        colnames = [cname.lower() for cname in df.columns.values.tolist()]
        df.columns = colnames

        # be somewhat flexible with column names, as long as they start with these strings
        uniqueidcol = next(cname for cname in colnames if cname.startswith("uniqueid"))
        topiccol = next(cname for cname in colnames if cname.startswith("topic"))
        diffcol = next(cname for cname in colnames if cname.startswith("difficulty"))
        # whichever source column is furthest right is the one we'll use
        sourcecol = [cname for cname in colnames if cname.startswith("source")][-1]  # eg "Source2021S"
        datecompletedcol = next(cname for cname in colnames if cname.startswith("datecompleted"))
        qtypescol = next(cname for cname in colnames if cname.startswith("questiontype"))
        instrcol = next(cname for cname in colnames if cname.startswith("instructions"))
        data1col = next(cname for cname in colnames if cname.startswith("data1"))
        data2col = next(cname for cname in colnames if cname.startswith("data2"))
        image1col = next(cname for cname in colnames if cname.startswith("image1") and "caption" not in cname)
        image2col = next(cname for cname in colnames if cname.startswith("image2") and "caption" not in cname)
        image1capcol = next(cname for cname in colnames if cname.startswith("image1") and "caption" in cname)
        image2capcol = next(cname for cname in colnames if cname.startswith("image2") and "caption" in cname)
        imgarrcol = next(cname for cname in colnames if cname.startswith("imagearrangement"))
        notescol = next(cname for cname in colnames if cname.startswith("notes"))
        omitcol = next(cname for cname in colnames if cname.startswith("omit"))
        instructorcommentscol = next(cname for cname in colnames
                                     if cname.startswith("instructor") and "comments" in cname)

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

            currentq = Question(
                uniqueid, topic, difficulty, source, datecompleted, questiontypes,
                instr, data1, data2, image1, image1caption, image2, image2caption, imagearrangement,
                notes, omit, instrnotes)
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
#               existingexamsfilename (string): name of the file (ignoring timsetamp suffix)
#                     where this data will be recorded for next generation
#               existingexamsdir (string): absolute or relative path to directory containing existing exam data file
#                    (default ".": current working dir)
def recordexistingexamstofile(existingexams, existingexamsfilename, existingexamsdir="."):

    appendtopath = "/"
    if existingexamsdir.endswith("/"):
        appendtopath = ""

    timestampedfilepath = existingexamsdir + appendtopath + \
                          existingexamsfilename+datetime.now().strftime("%Y%m%d%H%M%S")
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





# Generate PDF from one .tex source, using XeLaTeX
#   *** only use this if you are 100% confident the LaTeX is compilable; otherwise python and xetex both hang
# Parameters:   texsourcefile (string): path to the .tex file to compile
def generatepdf(texsourcefile):
    x = subprocess.call("xelatex " + texsourcefile)
    if x != 0:
        # never seem to get here, even if the source isn't compilable...
        print("something went wrong with file  " + texsourcefile + " ... :(")


# Looks for a command-line argument with the path to a config file;
#   if not found, asks user for input
# Sets random seed
# Returns:  questionspath (string): path to .tsv file containing exam questions
#           signupspath (string): path to .tsv file containing timeslot signup info
#           hassignupslots (boolean): True iff students are scheduled for various days/times (as per signupspath)
#           examtype (string): eg 'final' or 'midterm'
#           examdate (datetime.date): date of exam session (eg midterm or final);
#               None if exam is distributed across signup days/times (as per signupspath)
#           studentgroups (list of list of strings): each sublist indicates students
#               who typically work together and whose exams therefore should not overlap
#           onefileperstudent (boolean): True iff we want one tex/pdf file per student, vs exams batched by day
#           generateexamsuptodate (datetime.date):
#               generate exams scheduled up to and including this date (only relevant for exams with signups)
#           ordering (integer): type of ordering in which to arrange questions (see ORDER_* constants)
#           topics (list of strings): topics to include in exam (one entry per question)
#           difficulties (list of strings): difficulties to include in exam (one entry per question)
#           specifictopicdiffpairs (list of 2-tuples of strings): which topics *must* go with certain difficulties
#           wildcardtopics (list of strings): topics from which to draw wildcard question(s), if applicable
def getconfig():
    configpath = ""
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            configpath = sys.argv[1]
    while configpath == "":
        userinput = input("Enter the name of the config file for this exam (see README for help):\n")
        if os.path.isfile("../config/"+userinput):
            configpath = "../config/"+userinput
        else:
            print("\n" + "File not found in config directory. Please try again.")

    # default values, in case any info is missing from the config file (some are functional / some not)
    randomseed = "wugz"
    questionsfile = ""
    signupsfile = ""
    hassignupslots = True
    course = ""
    examtype = ""
    examdate = None
    studentgroups = []
    generateexamsuptodate = getfriofthisweek(date.today())
    # ordering can be:
    #   1 (in the order in which question topics are specified)
    #   2 (completely random)
    #   3 (one easy or medium question first if applicable, and the rest in random order)
    #   4 (one very hard question last if applicable, and the rest in random order
    ordering = 1
    topics = []
    diffs = []
    topicdiffpairs = []
    wildtopics = []
    rubric = ""

    # info tags that identify each line in the config file
    questionstag = "questions:"
    signupstag = "signups:"
    coursetag = "course:"
    examtypetag = "exam type:"
    studentgroupstag = "student groups:"
    randomseedtag = "random seed:"
    genuptodatetag = "generate up to:"
    orderingtag = "ordering:"
    topictag = "topics:"
    difftag = "difficulties:"
    wildtag = "wildcard topics:"
    rubrictag = "rubric:"

    with io.open(configpath, "r", encoding="utf-8") as cfile:
        cline = cfile.readline()

        while cline != "":
            if cline.startswith(questionstag):
                questionsfile = cline[len(questionstag):].strip()
            elif cline.startswith(signupstag):
                txt = cline[len(signupstag):].strip()
                items = [item.strip() for item in txt.split(" ")]
                if items[0] == "none":
                    # if there are no signups for this exam, we assume that everyone writes on the same day
                    # and that we're just looking for a list of student IDs
                    hassignupslots = False
                    signupsfile = items[1]
                else:
                    # otherwise we should have detailed signups with student ID, day, time
                    signupsfile = items[0]
            elif cline.startswith(coursetag):
                course = cline[len(coursetag):].strip()
            elif cline.startswith(examtypetag):
                txt = cline[len(examtypetag):].strip()
                items = [item.strip() for item in txt.split(" ")]
                examtype = items[0]
                if len(items) > 1:
                    # if there's another entry after the exam type, that's the exam date
                    examdate = makedate(items[1])
            elif cline.startswith(studentgroupstag):
                txt = cline[len(studentgroupstag):].strip()
                grps = [grp.strip() for grp in txt.split(";")]
                for grp in grps:
                    stdts = [stdt.strip() for stdt in grp.split(",")]
                    studentgroups.append(stdts)
            elif cline.startswith(randomseedtag):
                txt = cline[len(randomseedtag):].strip()
                if len(txt) > 0:
                    randomseed = txt
            elif cline.startswith(genuptodatetag):
                txt = cline[len(genuptodatetag):].strip()
                if len(txt) > 0:
                    generateexamsuptodate = makedate(txt)
            elif cline.startswith(orderingtag):
                txt = cline[len(orderingtag):].strip()
                if len(txt) > 0:
                    ordering = int(txt)
            elif cline.startswith(topictag):
                txt = cline[len(topictag):].strip()
                if len(txt) > 0:
                    topics = [item.strip() for item in txt.split(";")]
            elif cline.startswith(difftag):
                txt = cline[len(difftag):].strip()
                if len(txt) > 0:
                    diffswithbrackets = [item.strip() for item in txt.split(";")]
                    for idx, diff in enumerate(diffswithbrackets):
                        # brackets indicate a specific topic/difficulty pair
                        if "[" in diff:
                            d = diff[:diff.index("[")].strip()
                            diffs.append(d)
                            inbrackets = re.findall("\[(.*?)\]", diff)
                            if len(inbrackets) > 0:
                                t = inbrackets[0].strip()
                                if t in topics:
                                    topicdiffpairs.append((t, d))
                        else:
                            diffs.append(diff)
            elif cline.startswith(wildtag):
                txt = cline[len(wildtag):].strip()
                if len(txt) > 0:
                    wildtopics = [item.strip() for item in txt.split(";")]
            elif cline.startswith(rubrictag):
                txt = cline[len(rubrictag):].strip()
                if len(txt) > 0:
                    rubric = txt

            cline = cfile.readline()

    # for repeatable results - currently not using because randomization is helping avoid repeated errors
    # random.seed(randomseed)

    # TODO - should this choice be moved to the config file?
    filestructure = ""
    while filestructure == "":
        userinput = input(
            "Do you want all of one day's exams in a single pdf (enter 'b' for batch) \n" +
            "or would you prefer each student's exam in its own file (enter 's' for separate)? \n"
        )
        if userinput == "b" or userinput == "s":
            filestructure = userinput
        else:
            print("\n" + "Not a valid response. Please try again.")
    onefileperstudent = False
    if filestructure == "s":
        onefileperstudent = True

    return questionsfile, signupsfile, hassignupslots, course, examtype, examdate, \
        studentgroups, onefileperstudent, generateexamsuptodate, ordering, \
        topics, diffs, topicdiffpairs, wildtopics, rubric


# Returns all day/time/student info in file as a dictionary of date --> list of (time,studentid)
#   *** note that if this is for an exam with signups, this will only collect the info for students who've
#   (a) not yet had an exam generated and
#   (b) are signed up for up to and including the value of generateuptodate
# Parameters:   signupsfilepath (string): path to the .tsv file containing exam scheduling data
#               hassignupslots (boolean): True if this exam has scheduled signups (eg for oral exams),
#                   False if not (eg for written exams all in one sitting)
#               examtype (string): eg 'final' or 'midterm'
#               examdate (datetime.date): date of exam (if all students are writing at the same time;
#                   ie, it's not an oral exam, with signup slots)
#               generateuptodate (datetime.date): the date up to which exams should be generated
def readsignupsfromfile(signupsfilepath, hassignupslots, examtype, examdate, generateuptodate):
    signups = {}  # dictionary of date --> list of (time,studentid)

    with io.open(signupsfilepath, "r", encoding="utf-8") as sfile:

        if hassignupslots:

            df = pd.read_csv(sfile, sep="\t", keep_default_na=False)  # read column names from file
            colnames = [cname.lower() for cname in df.columns.values.tolist()]
            df.columns = colnames

            # be somewhat flexible with column names, as long as they start with these strings
            daycol = next(cname for cname in colnames if cname.startswith("day"))
            timecol = next(cname for cname in colnames if cname.startswith("time"))
            sidcol = next(cname for cname in colnames if cname.startswith("sid"))

            for index, row in df.iterrows():
                daystring = str(row[daycol])
                day = makedate(daystring)
                if day is None:
                    print("signup dates must contain strings of form yyyy-mm-dd")
                    print("----- Exiting -----")
                    sys.exit(1)
                time = str(row[timecol])
                stid = str(row[sidcol])

                if makedate(day) <= generateuptodate:
                    if day not in signups.keys():
                        signups[day] = []
                    signups[day].append((time, stid))
        else:
            day = examdate
            time = ""
            signups[day] = []

            df = pd.read_csv(sfile, sep="\t", keep_default_na=False)  # read column names from file
            colnames = [cname.lower() for cname in df.columns.values.tolist()]
            df.columns = colnames

            # be somewhat flexible with column names, as long as they start with these strings
            sidcol = next(cname for cname in colnames if cname.startswith("sid"))

            for index, row in df.iterrows():
                stid = str(row[sidcol])
                signups[day].append((time, stid))

    return signups
