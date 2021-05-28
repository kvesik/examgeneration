import os, sys, io
import re
import pandas as pd
import pickle
from Exam import Question
import examio

FLASH = "flash"
MIDTERM = "midterm"
FINAL = "final"
extypes = [FLASH, MIDTERM, FINAL]

EXISTINGEXAMSPICKLEPATH = "existingexams_donotedit.dict"


# asks user for the path to a certain type ("filetype" string) and checks its validity
def getfilepath(filetype):
    filepath = ""
    while filepath == "":
        userinput = input("Enter the path to the "+filetype+" file: ")
        if os.path.isfile(userinput):
            filepath = userinput
        else:
            print("\n"+" ----------Not a valid file path. Please try again. ----------")
    return filepath


# returns a dictionary of examtype --> [list of Questions] for this given stid,
# or None if the stid doesn't have any exams yet
def getexamsforonestudent(exams, stid):
    if stid in exams.keys():
        return exams[stid]
    return None


# returns a (potentially) modified version of the input list, in which
# any instance of the qtoremove is replaced with the qtoinsert
def replacequestion(qslist, qtoremove, qtoinsert):
    idtoremove = qtoremove.uniqueid
    newlist = []
    for q in qslist:
        if q.uniqueid == idtoremove:
            newlist.append(qtoinsert)
        else:
            newlist.append(q)
    return newlist


# returns the Queston ID'd by qid from the given list, or None if it doesn't exist
def getquestion(qslist, qid):
    for q in qslist:
        if q.uniqueid == qid:
            return q
    return None


# DEPRECATED
# this functin was custom built and used to deal with some question replacements on Oct 4 2020,
# before the generic utilities menu was available
def questionreplacements20201004():
    allqs = examio.readquestionsfromfile("allquestions.tsv")
    qslist = []
    for topic in allqs.keys():
        for diff in allqs[topic].keys():
            qslist.extend(allqs[topic][diff])
    allqs = qslist
    allexams = examio.readexistingexamsfromfile("existingexams_donotedit_20200930gavetoKathleen.dict")
    print("allexams", allexams)

    for stid in ("38415", "54125"):
        studentexams = getexamsforonestudent(allexams, stid)
        print("-- "+stid+" --")
        for extype in ['flash']:
            print(extype)
            qslist = studentexams[extype]
            print("original questions")
            for q in qslist:
                q.print()
            print("new questions")
            newlist = replacequestion(qslist, getquestion(allqs, "QU1601510604151"), getquestion(allqs, "QU1601510733572"))
            for q in newlist:
                q.print()
        allexams[stid][extype] = newlist

    print(allexams)
    examio.recordexistingexamstofile(allexams, "existingexams_donotedit_20200930gavetoKathleen_UPDATED.dict")
    allexams_new = examio.readexistingexamsfromfile("existingexams_donotedit_20200930gavetoKathleen_UPDATED.dict")
    print("new exam collection, just to double check...")
    print(allexams_new)

    for stid in ("38415", "54125"):
        studentexams = getexamsforonestudent(allexams_new, stid)
        print("-- "+stid+" --")
        for extype in ['flash']:
            print(extype)
            qslist = studentexams[extype]
            print("questions from updated file")
            for q in qslist:
                q.print()

# reads most recent dict file
# removes the exam of type examtype for student sid from all existing exams
# writes the updated dict file
def removeexamfromexisting(sid, examtype):
    allexams = examio.readexistingexamsfromfile(EXISTINGEXAMSPICKLEPATH)
    studentexams = getexamsforonestudent(allexams, sid)
    if studentexams is None:
        return False
    reducedexams = {extype:questions for extype,questions in studentexams.items() if extype != examtype}
    if len(studentexams.keys()) > len(reducedexams.keys()):
        allexams[sid] = reducedexams
        examio.recordexistingexamstofile(allexams, EXISTINGEXAMSPICKLEPATH)
        return True
    else:
        return False

# get & validate an exam type string from user
def getexamtypefromuser():
    selectedtype = ""
    while selectedtype not in extypes:
        selectedtype = input("What type of exam? Enter 'flash', 'midterm', or 'final' (or 'r' to return to main menu): ")
        if selectedtype in extypes:
            return selectedtype
        elif selectedtype == "r":
            main_menu()
        else:
            print(" ----------Hmmm; that wasn't one of the options; let's try again. ----------")


# get & validate a student id (5-digit) from user
def getsidfromuser():
    selectedsid = ""
    while re.match("[0-9]{5}", selectedsid) is None:
        selectedsid = input("Enter the 5-digit student ID (or 'r' to return to main menu): ")
        if re.match("[0-9]{5}", selectedsid) is not None:
            return selectedsid
        elif selectedsid == "r":
            main_menu()
        else:
            print(" ----------Hmmm; that wasn't one of the options; let's try again. ----------")


# get & (somewhat) validate a question ID from user
def getqidfromuser(prompt):
    selectedqid = ""
    while re.match("QU[0-9]+", selectedqid) is None:
        selectedqid = input(prompt+" (or 'r' to return to main menu): ")
        if re.match("QU[0-9]+", selectedqid) is not None:
            return selectedqid
        elif selectedqid == "r":
            main_menu()
        else:
            print(" ----------Hmmm; that wasn't one of the options; let's try again. ----------")


# for sid's exam of type examtype, replace the Question ID'd by qidold with the Question ID'd by qidnew
# gathering Question info from questionsfilepath
def replacequestioninexam(examtype,sid,qidold,qidnew,questionsfilepath):
    allqs = examio.readquestionsfromfile(questionsfilepath)
    qslist = []
    for topic in allqs.keys():
        for diff in allqs[topic].keys():
            qslist.extend(allqs[topic][diff])
    allqs = qslist

    allexams = examio.readexistingexamsfromfile(EXISTINGEXAMSPICKLEPATH)
    studentexams = getexamsforonestudent(allexams, sid)
    if studentexams is None or examtype not in studentexams.keys():
        return False

    studentqs = studentexams[examtype]

    qtoremove = getquestion(allqs, qidold)
    qtoinsert = getquestion(allqs, qidnew)
    if qtoremove is not None and qtoinsert is not None:
        studentqs_new = replacequestion(studentqs, qtoremove, qtoinsert)
        allexams[sid][examtype] = studentqs_new
        examio.recordexistingexamstofile(allexams, EXISTINGEXAMSPICKLEPATH)
        return True
    else:
        return False


# get required info from user in order to replace a question in a particular student's particular exam
def replacequestion_gatherinfo():
    print("OK, let's replace a question.")
    selectedtype = getexamtypefromuser()
    selectedsid = getsidfromuser()
    oldqid = getqidfromuser("Enter the unique ID (QU###...) of the question you want to replace")
    newqid = getqidfromuser("Enter the unique ID (QU###...) of the question you would like to use instead")
    questionsfilepath = getfilepath("questions (tsv)")  # input("Enter the path to the questions file (.tsv): ")
    confirmation = input("Confirm (y or n): replace "+oldqid+" with "+newqid+" in student #"+selectedsid+"'s "+selectedtype+" exam? ")
    if confirmation == "y" or confirmation == "Y":
        success = replacequestioninexam(selectedtype,selectedsid,oldqid,newqid,questionsfilepath)
        if success is True:
            print("\n---------- Done! ----------\n")
        else:
            print("\n---------- Didn't find such a question(s). ----------\n")
    main_menu()


# get required info from user to remove a particular student's particular exam
def removeexam_gatherinfo():
    print("OK, we'll remove an exam.")
    selectedtype = getexamtypefromuser()
    selectedsid = getsidfromuser()
    confirmation = input("Confirm (y or n): removing "+selectedtype+" exam for student #"+selectedsid+"? ")
    if confirmation == "y" or confirmation == "Y":
        success = removeexamfromexisting(selectedsid,selectedtype)
        if success is True:
            print("\n---------- Done! ----------\n")
        else:
            print("\n---------- Didn't find such an exam. ----------\n")
    main_menu()


# haven't implemented this yet because I think it's reasonably efficient just to manually delete the dict
# generated folder for the (most recent) batch you don't want
# TODO however if we want to remove a batch of exams that's *not* the most recent then this might come in handy...
# def removebatch_gatherinfo():


# provides a console-based menu to get user input re what they want to do to change the existing exam collection
def main_menu():

    while True:
        print("What would you like to do?")
        print("1. Replace a particular question for a particular student on a particular exam\n\t(eg if you realized that a question was not appropriate for the date it was originally labeled as).")
        print("2. Remove an entire particular exam for a particular student\n\t(eg if they cancelled after their flash exam was generated).")
        # print("u. Undo the last batch of exam generation.")
        print("x. Nothing; never mind; I'm just going to go (aka 'exit'). :)")

        userinput = input("Enter your choice: ")

        if userinput == "1":
            replacequestion_gatherinfo()
        elif userinput == "2":
            removeexam_gatherinfo()
        # elif userinput == "u":
        #     removebatch_gatherinfo()
        elif userinput == "x":
            print("OK; bye!")
            sys.exit(0)
        else:
            print("\n---------- That wasn't a valid selection; let's try again. ----------")


#####################
### do the thing! ###
#####################
main_menu()

