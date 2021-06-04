# -*- coding: utf-8 -*-
"""
written Sep-Oct 2020 by Kaili Vesik: kvesik@gmail.com
updated May 2021 by Kaili Vesik
"""

import os
import sys
import examio
import generateexams


# asks user for the path to a certain type ("filetype" string) and checks its validity
def getfilepath(filetype):
    filepath = ""
    while filepath == "":
        userinput = input("Enter the name of the "+filetype+" file (I will look in the 'data' folder): ")
        if os.path.isfile("../data/" + userinput):
            filepath = "../data/" + userinput
        else:
            print("\n"+" ----------Not a valid file path. Please try again. ----------")
    return filepath


# returns a dictionary of examtype --> [list of Questions] for this given student id,
# or None if this student id doesn't have any exams yet
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


# reads most recent dict file
# removes the exam of type examtype for student sid from the set of existing exams
# writes the updated dict file
def removeexamfromexisting(sid, examtype, allexams):
    studentexams = getexamsforonestudent(allexams, sid)
    if studentexams is None:
        return False
    reducedexams = {extype: questions for extype, questions in studentexams.items() if extype != examtype}
    if len(studentexams.keys()) > len(reducedexams.keys()):
        allexams[sid] = reducedexams
        examio.recordexistingexamstofile(allexams, generateexams.EXISTINGEXAMSPICKLEFILE, "../exams")
        return True
    else:
        return False


# get & validate an exam type string from user
def getexamtypefromuser(allexams):
    examtypes = []
    for sid in allexams.keys():
        examtypes.extend(list(allexams[sid].keys()))
    examtypes = list(set(examtypes))
    examtypesstring = ", ".join(["'" + xt + "'" for xt in examtypes])

    selectedtype = ""
    while selectedtype not in examtypes + ["r"]:
        selectedtype = input(
            "What type of exam? Eg " + examtypesstring + " (or 'r' to return to main menu): ")
        if selectedtype not in examtypes + ["r"]:
            print(" ---------- There are no existing exams of that type. ----------")
    if selectedtype == "r":
        main_menu()
    else:
        return selectedtype


# get & validate a student id (5-digit) from user
def getsidfromuser(allexams):
    sids = list(allexams.keys())

    selectedsid = ""
    while selectedsid not in sids + ["r"]:
        selectedsid = input("Enter the student ID (or 'r' to return to main menu): ")
        if selectedsid not in sids + ["r"]:
            print(" ---------- There are no existing exams with that student ID. ----------")
    if selectedsid == "r":
        main_menu()
    else:
        return selectedsid


# get a question ID from user
def getqidfromuser(prompt):
    selectedqid = ""
    while selectedqid == "":
        selectedqid = input(prompt+" (or 'r' to return to main menu): ")
    if selectedqid != "":
        return selectedqid
    else:
        main_menu()


# for sid's exam of type examtype, replace the Question ID'd by qidold with the Question ID'd by qidnew
# gathering Question info from questionsfilepath
def replacequestioninexam(examtype, sid, qidold, qidnew, questionsfilepath, allexams):
    allqs = examio.readquestionsfromfile(questionsfilepath)
    qslist = []
    for topic in allqs.keys():
        for diff in allqs[topic].keys():
            qslist.extend(allqs[topic][diff])
    allqs = qslist

    studentexams = getexamsforonestudent(allexams, sid)
    if studentexams is None:
        return "Student not found."
    elif examtype not in studentexams.keys():
        return "Exam type not found."

    studentqs = studentexams[examtype]

    qtoremove = getquestion(allqs, qidold)
    qtoinsert = getquestion(allqs, qidnew)
    if qtoremove is not None and qtoinsert is not None:
        studentqs_new = replacequestion(studentqs, qtoremove, qtoinsert)
        allexams[sid][examtype] = studentqs_new
        examio.recordexistingexamstofile(allexams, generateexams.EXISTINGEXAMSPICKLEFILE, "../exams")
        return "Done!"
    else:
        return "Question(s) not found."


# get required info from user in order to replace a question in a particular student's particular exam
def replacequestion_gatherinfo(allexams):
    print("OK, let's replace a question.")
    selectedtype = getexamtypefromuser(allexams)
    selectedsid = getsidfromuser(allexams)
    oldqid = getqidfromuser("Enter the unique ID (QU###...) of the question you want to replace")
    newqid = getqidfromuser("Enter the unique ID (QU###...) of the question you would like to use instead")
    questionsfilepath = getfilepath("questions (tsv)")
    confirmation = input("Confirm (y or n): replace " + oldqid+" with "+newqid +
                         " in student #" + selectedsid + "'s " + selectedtype+" exam? ")
    if confirmation == "y" or confirmation == "Y":
        result = replacequestioninexam(selectedtype, selectedsid, oldqid, newqid, questionsfilepath, allexams)
        print("\n---------- " + result + " ----------\n")
    main_menu()


# get required info from user to remove a particular student's particular exam
def removeexam_gatherinfo(allexams):
    print("OK, we'll remove an exam.")
    selectedtype = getexamtypefromuser(allexams)
    selectedsid = getsidfromuser(allexams)
    confirmation = input("Confirm (y or n): removing "+selectedtype+" exam for student #"+selectedsid+"? ")
    if confirmation == "y" or confirmation == "Y":
        success = removeexamfromexisting(selectedsid, selectedtype, allexams)
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
        allexams = examio.readexistingexamsfromfile(generateexams.EXISTINGEXAMSPICKLEFILE, "../exams")
        print("What would you like to do?")
        print("1. Replace a particular question for a particular student on a particular exam\n" +
              "\t(eg if you realized that a question was not appropriate for the date it was originally labeled as).")
        print("2. Remove an entire particular exam for a particular student\n\t" +
              "(eg if they cancelled after their individually-scheduled exam was generated).")
        # print("u. Undo the last batch of exam generation.")
        print("x. Nothing; never mind; I'm just going to go (aka 'exit'). :)")

        userinput = input("Enter your choice: ")

        if userinput == "1":
            replacequestion_gatherinfo(allexams)
        elif userinput == "2":
            removeexam_gatherinfo(allexams)
        # elif userinput == "u":
        #     removebatch_gatherinfo(allexams)
        elif userinput == "x":
            print("OK; bye!")
            sys.exit(0)
        else:
            print("\n---------- That wasn't a valid selection; let's try again. ----------")


#####################
#   do the thing!   #
#####################
main_menu()
