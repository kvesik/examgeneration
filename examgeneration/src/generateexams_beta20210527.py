# -*- coding: utf-8 -*-
"""
written May-July 2020 by Kaili Vesik: kvesik@gmail.com
updated Sep-Oct 2020 by Kaili Vesik, for use in 2020W1
updated May 2021 by Kaili Vesik, for use in 2021S1
"""

import subprocess
import os
import sys
import random
import io
import pandas as pd
from datetime import date, datetime, timedelta
from src.Exam import Question, Exam
from src import examio_beta20210527 as examio

# exam topics
TRANSCR = "Transcription"
ARTPHON = "Articulatory Phonetics"
SKEWED = "Skewed Distributions"
PHRELAN = "Phonological Relationships and Analysis"
WILD = "Wildcard"
OTHERPRE = "Other (pre-midterm)"
OTHERPOST = "Other (post-midterm)"
ACOUS = "Acoustics"
ALTER = "Alternations"
PHONFT = "Phonological Features"
SYLS = "Syllables"
TONE = "Tone"
DATASET = "Dataset"

# other constants for reference
NUMQS = "number of questions"
TOPICS = "topics"
WILDTOPICS = "wildcard topics"
DIFFS = "difficulty distribution"
T = "\t"
N = "\n"
EXISTINGEXAMSPICKLEPATH = "existingexams_donotedit.dict"

# exam types, topics, difficulty distributions
MIDTERM = "midterm"
midtermtopics = [TRANSCR, ARTPHON, PHONFT, SKEWED, PHRELAN]
# note: next line - midterm wildcard not used in 2020W1 (these were the options for 2020S1)
wildcardmidtermtopics = [TRANSCR, ARTPHON, SKEWED, PHRELAN, OTHERPRE]
midtermdifficulties = {
    Question.EASY: 1,
    Question.MED: 2,
    Question.HARD: 1,
    Question.VHARD: 1
}
FINAL = "final"
finaltopics = [ACOUS, ALTER, SYLS, TONE, DATASET, WILD]
wildcardfinaltopics = [
    TRANSCR,
    ARTPHON,
    PHONFT,
    SKEWED,
    PHRELAN,
    ACOUS,
    ALTER,
    SYLS,
    TONE,
    OTHERPRE,
    # OTHERPOST, # TODO update when there are questions of this topic
]
finaldifficulties = {
    Question.EASY: 1,
    Question.MED: 2,
    Question.HARD: 2,
    Question.VHARD: 1
}
FLASH = "flash"
flashtopics = [WILD, WILD]
wildcardflashtopics = []
flashdifficulties = {
    Question.MED: 1,
    Question.HARD: 1,
}

examcomposition = {
    MIDTERM: {
        NUMQS: len(midtermtopics),
        TOPICS: midtermtopics,
        WILDTOPICS: wildcardmidtermtopics,
        DIFFS: midtermdifficulties
    },
    FINAL: {
        NUMQS: len(finaltopics),
        TOPICS: finaltopics,
        WILDTOPICS: wildcardfinaltopics,
        DIFFS: finaldifficulties
    },
    FLASH: {
        NUMQS: len(flashtopics),
        TOPICS: flashtopics,
        WILDTOPICS: wildcardflashtopics,
        DIFFS: flashdifficulties
    }
}

# to be included on instructor copies
instrnotesprefix = N+"~\\\\"+N+"INSTRUCTOR NOTES: "
RUBRIC = "\\vfill"+N+"Excellent (3) ~~~ Good (2.2) ~~~ Fair (1.7) ~~~ Poor (0)"+N


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


# Returns a (flattened) list of all the Questions in the input, no longer in a hierarchy of topic/difficulty
# Parameters:   qsdict (dictionary of topic --> difficulty --> [list of Questions]): the dictionary to flatten
def flattenqsdict(qsdict):
    flattenedqs = []
    for topic in qsdict.keys():
        for difficulty in qsdict[topic].keys():
            flattenedqs.extend(qsdict[topic][difficulty])
    return flattenedqs


# Returns True iff questionspool contains questions of each t_i & d_i,
#   where t_i is in topics and d_i is in difficulties (ie, zipped pairs of the topics & difficulties lists)
# Parameters:   questionspool (dictionary of topic --> difficulty --> [list of Questions]): questions to check
#               topics (list of strings): topics to pair with difficulties in next argument
#               difficulties (list of strings): difficulties to pair with topics in previous argument
def docombosexist(questionspool, topics, difficulties):
    if isinstance(questionspool, dict):
        questionstocheck = flattenqsdict(questionspool)
    else:  # should be a list if not a dictionary (...?)
        questionstocheck = [q for q in questionspool]
    for i in range(len(topics)):
        success = False
        for q in questionstocheck:
            if q.topic == topics[i] and q.difficulty == difficulties[i]:
                success = True
                questionstocheck.remove(q)
        if success is False:
            return False
    return True


# Returns True iff there is a Question in questions with the given uniqueid
# Parameters:   uniqueid (string): the unique question ID to check for
#               questions (list of Questions): the questions to look through
def isuniqueidinquestions(uniqueid, questions):
    ids = [q.uniqueid for q in questions]
    return uniqueid in ids


# Returns True iff there is a Question in questions with the given source
# Parameters:   source (string): the question source to check for
#               questions (list of Questions): the questions to look through
def isqsourceinquestions(source, questions):
    sources = [q.source for q in questions]
    return source in sources


# Returns True iff one of the questionype tags in potentialqtypes is also in existingqtypes
# Parameters:   potentialqtypes (list of strings): the subtypes of a potential exam question
#               existingqtypes (list of strings): the subtypes already existing in the exam
def isqtypeduplicate(potentialqtypes, existingqtypes):
    questiontypeisduplicate = False
    for questiontype in potentialqtypes:
        if questiontype in existingqtypes:
            questiontypeisduplicate = True
    return questiontypeisduplicate


# this class represents one session of exams
# (for example, a midterm exam for n students taking place over m days)
class ExamSession:

    # Parameters:   examtype (string): which exam this is: midterm, final, or flash
    #               allquestions ([list of Questions]): the set of Questions to be drawn from for this exam session
    #               signups (dictionary of date --> [list of (time,studentid)]): timeslots and corresponding
    #                   student ids, grouped by date
    #               studentgroups ([list of [lists of strings]]): groups of students whose exams should not overlap
    #               existingexams (dictionary of studentif --> examtype --> [list of Questions]):
    #                   questions already seen by various students on previous exams
    #               startdate (date object): date that this ExamSession begins (if not provided, defaults to today)
    #               onefileperstudent (boolean): whether we want one pdf per sid
    #                   (as opposed to the default, each day's exams getting batched together into one tex/pdf file)
    # Each of these parameters is likely supplied by getconfig(), readquestionsfromfile(), and/or readsignupsfromfile()
    def __init__(self, examtype=FINAL, allquestions={}, signups={}, studentgroups=[], existingexams={},
                 startdate=date.today(), onefileperstudent=False):

        self.examtype = examtype
        self.allquestions = allquestions
        self.signups = signups
        self.exams = {}  # dictionary of studentid-->Exam
        self.studentgroups = studentgroups
        self.existingexams = existingexams
        self.startdate = startdate
        self.onefileperstudent = onefileperstudent

    # Returns True iff we've already generated an exam of the given type for the given sid
    # Parameters:   sid (string): the student ID to check for
    #               examtype: the exam type (final, midterm, flash) to check for
    def thisstudentexamexists(self, sid, examtype):
        if sid in self.existingexams.keys():
            if examtype in self.existingexams[sid].keys():
                return True
        return False

    # Returns a list of Questions that this student has seen before on previous exams
    # Parameters:   sid (string): student id whose exam questions to collect
    #                   (default "": return questions for all students)
    #               examptype (string): examtype whose questions to collect
    #                   (default "": return questions for all examtypes)
    def getthisstudentquestionsseen(self, sid="", examtype=""):
        examtypes = []
        if examtype != "":
            examtypes = [examtype]
        else:
            examtypes = list(examcomposition.keys())
        qsseen = []
        if sid == "":
            # if no student specified, return all questions seen by everyone so far, for specified examtype(s)
            for stdt in self.existingexams.keys():
                for extype in self.existingexams[stdt].keys():
                    if extype in examtypes:
                        qsseen.extend(self.existingexams[stdt][extype])
        elif sid in self.existingexams.keys():
            # if this student has had some exams generated so far, collect this student's questions seen so far,
            #   for specified examtype(s)
            for extype in self.existingexams[sid].keys():
                if extype in examtypes:
                    qsseen.extend(self.existingexams[sid][extype])
        # else we are looking for a specific student but they haven't had any exams generated yet; leave the list empty
        return qsseen

    # Generate LaTeX source for one entire exam day's document; write to file
    # Also generate a tsv for one entire exam day (for piping into Canvas); write to file
    # Parameters:   texfilepath (string): path to the .tex file to generate
    #               tsvfilepath (string): path to the .tsv file that will be used to pipe questions into Canvas quizzes
    #               examdate (date): the date whose exam source to generate
    def generatelatexexams_oneday(self, texfilepath, tsvfilepath, examdate):
        print("generating one day's exams / date",examdate) # TODO

        sched = self.signups[examdate]

        instrfilepath = texfilepath.replace(".tex", "_instructorcopy.tex")
        with open(instrfilepath, "w", encoding="utf-8") as inf:
            with open(tsvfilepath, "w", encoding="utf-8") as tsvf:
                writedochead(inf, examdate.strftime("%Y%m%d %A"), "ALL EXAMS (with notes)")
                tsvf.write(
                    "Person" + T +
                    "Topic" + T +
                    "Difficulty" + T +
                    "Source" + T +
                    "Question_latex" + T +
                    "Image1" + T +
                    "Image1Caption" + T +
                    "Image2" + T +
                    "Image2Caption" + N
                )

                if not self.onefileperstudent:  # entire day's exams batched into one file
                    with open(texfilepath, "w", encoding="utf-8") as texf:
                        writedochead(texf, examdate.strftime("%Y%m%d %A"), "ALL EXAMS")

                        for (time, sid) in sched:
                            if sid == "":
                                writeexamstart(texf, "empty", time)
                                writeexamstart(inf, "empty", time)
                                continue
                            qs = self.collectquestionsforoneexam(sid, examdate)

                            thisexam = Exam(sid, examdate, time, qs)
                            writeexamstart(texf, sid, time)
                            writeexamstart(inf, sid, time)
                            for qidx in range(0, examcomposition[self.examtype][NUMQS]):
                                writeexamquestiontex(qidx + 1, qs[qidx], texf)
                                writeexamquestiontex(qidx + 1, qs[qidx], inf, instrcopy=True)
                                writeexamquestiontsv(sid, qs[qidx], tsvf)
                            writeexamend(texf)
                            writeexamend(inf)
                        writedocfoot(texf)

                else:  # each student gets their own file

                    for (time, sid) in sched:
                        sidforfilename = sid if sid != "" else "empty"
                        thissidtexfilepath = texfilepath.replace(".tex","-sid"+sidforfilename+".tex")
                        with open(thissidtexfilepath, "w", encoding="utf-8") as texf:
                            writedochead(texf, "", "", onefileperstudent=self.onefileperstudent)
                            if sid == "":
                                writeexamstart(texf, "empty", time)
                                writeexamstart(inf, "empty", time)
                                continue
                            qs = self.collectquestionsforoneexam(sid, examdate)

                            thisexam = Exam(sid, examdate, time, qs)
                            writeexamstart(texf, sid, time)
                            writeexamstart(inf, sid, time)
                            for qidx in range(0, examcomposition[self.examtype][NUMQS]):
                                writeexamquestiontex(qidx + 1, qs[qidx], texf)
                                writeexamquestiontex(qidx + 1, qs[qidx], inf, instrcopy=True)
                                writeexamquestiontsv(sid, qs[qidx], tsvf)
                            writeexamend(texf)
                            writedocfoot(texf)
                            writeexamend(inf)

                writedocfoot(inf)

    # Generate LaTeX source for this entire exam session (could be multiple days); write to file
    # Also generate a tsv for this entire exam session (for piping into Canvas); write to file
    # TODO params
    def generatelatexexams(self, foldername, generateuptodate=date.today()):

        # filename info for exam TeX & tsv sources to be generated
        texfileprefix = "LING200" + self.examtype + "-"
        texfilesuffix = ".tex"
        tsvfilesuffix = ".tsv"

        print("generating latex exams up to date", generateuptodate) # TODO

        # generate an exam for each day, named after days in schedule
        for thedate in self.signups.keys():  # should be a date object

            # if (self.examtype == FLASH and thedate <= getfriofthisweek(thedate)) or self.examtype != FLASH:
            if (self.examtype == FLASH and (thedate <= getfriofthisweek(thedate) or thedate <= generateuptodate)) \
                    or self.examtype != FLASH:
                examtex = texfileprefix + thedate.strftime("%Y%m%d%A") + texfilesuffix
                fullpathtotex = foldername + "/" + examtex
                fullpathtotsv = fullpathtotex.replace(texfilesuffix, tsvfilesuffix)
                self.generatelatexexams_oneday(fullpathtotex, fullpathtotsv, thedate)

                # only use this if you are 100% confident the latex is compilable;
                # otherwise python and xelatex both hang
                # generatepdf(fullpathtotex)

    # Returns a list of Questions with the given topic and difficulty level
    # Parameters:   topic (string): the topic from which to collect questions; if empty, all topics will be included
    #               difficulty (string): the difficulty from which to collect questions;
    #                   if empty, all difficulty levels will be included
    #               qspool (dictionary of topic --> difficulty --> [list of Questions]): questions to draw from
    def getquestions(self, topic="", difficulty="", qspool={}):

        if len(qspool.keys()) == 0:
            qspool = self.allquestions

        topicqs = {}
        selectedqs = []
        if topic != "":  # given a specific topic
            topicqs = qspool[topic]
            if difficulty != "":  # given a specific difficulty
                selectedqs = topicqs[difficulty]
            else:  # topic  but no difficulty specified
                for diff in topicqs.keys():
                    selectedqs.extend(topicqs[diff])
        else:  # no topic given
            for topic in qspool.keys():
                if difficulty != "":  # no topic but given a specific difficulty
                    selectedqs.extend(qspool[topic][difficulty])
                else:  # neither topic nor difficulty given
                    topicqs = qspool[topic]
                    for diff in topicqs.keys():
                        selectedqs.extend(topicqs[diff])
        return selectedqs

    # Returns unique Question with the given topic and difficulty level
    # Parameters:   qssofar (list of Questions): the selected question must not already be in this list
    #               topic (string): the topic from which to collect questions -- must be specified
    #                   (ie, not WILD nor empty)
    #               difficulty (string): the difficulty from which to collect questions;
    #                   if empty, the question could be from any difficulty level
    #               otherstudents (list of student ids): the selected question must not already be
    #                   in any of these students' exams
    #               alreadyused (list of Questions): the selected question must not be in this list
    #                   (of questions this student has already seen on a previous exam)
    #               qspool (dictionary of topic --> difficulty --> [list of Questions]): questions to draw from -
    #                   should already be date-restricted if applicable
    def getuniquequestion(self, qssofar, topic, difficulty="", otherstudents=[], alreadyused=[], qspool={}):

        if len(qspool.keys()) == 0:
            qspool = self.allquestions

        # gather a list of all (appropriately dated) questions of this topic + difficulty, and pick a random one
        # questions in qspool should already be restricted by date
        eligibleqs = self.getquestions(topic, difficulty, qspool)
        question = random.sample(eligibleqs, 1)[0]

        # gather a list of questions that are on exams of students who this student works with
        otherstudentquestions = []
        for sid in otherstudents:
            if sid in self.exams.keys():
                otherstudentquestions.extend(self.exams[sid].questions)

        # gather a list of question (sub) types (eg signlanguage, morphology, UR, etc) already on this exam
        qtypessofar = []
        for q in qssofar:
            for qtype in q.questiontypes:
                qtypessofar.append(qtype)

        # make sure that this question isn't already in this exam,
        # and that we're not putting more than one question of this subtype in this exam
        # and that this student doesn't get the exam same question that someone they worked with also has
        # and that this student hasn't seen another question from this source on a previous exam
        numtries = 0
        while (question in qssofar) \
                or isqtypeduplicate(question.questiontypes, qtypessofar) \
                or (isuniqueidinquestions(question.uniqueid, otherstudentquestions)) \
                or (isqsourceinquestions(question.source, alreadyused)):
            if numtries > 50:
                # this has to do with too many specific subtypes & too few questions of some topic/difficulty combos
                if isqsourceinquestions(question.source, alreadyused):
                    print("couldn't find a unique source for " + question.topic + " / " + question.difficulty+" - going to give up and allow overlap with group members")
                elif isuniqueidinquestions(question.uniqueid, otherstudentquestions):
                    print("couldn't find a question not in a group member's exam for " + question.topic + " / " + question.difficulty+" - going to give up and allow overlap with group members")
                print("group members: ", otherstudents)
                break
            question = random.sample(eligibleqs, 1)[0]
            numtries += 1

        numtries2 = 0
        while (question in qssofar) \
                or isqtypeduplicate(question.questiontypes, qtypessofar) \
                or (isqsourceinquestions(question.source, alreadyused)):
                # no longer care about questions overlapping with group members
            if numtries2 > 50:
                # this has to do with too many specific subtypes & too few questions of some topic/difficulty combos
                if isqsourceinquestions(question.source, alreadyused):
                    print("couldn't find a unique source for " + question.topic + " / " + question.difficulty+" - going to give up and just request unique question instead")
                break
            question = random.sample(eligibleqs, 1)[0]
            numtries2 += 1

        numtries3 = 0
        while (question in qssofar) \
                or isqtypeduplicate(question.questiontypes, qtypessofar) \
                or (isuniqueidinquestions(question.uniqueid, alreadyused)):
                # no longer care about unique source among this student's questions,
                # as long as exact question isn't repeated
            if numtries3 > 50:
                # this has to do with too many specific subtypes & too few questions of some topic/difficulty combos
                if isuniqueidinquestions(question.uniqueid, alreadyused):
                    print("couldn't find a unique source for " + question.topic + " / " + question.difficulty+" - going to give up and allow repetition of question subtype")
                break
            question = random.sample(eligibleqs, 1)[0]
            numtries3 += 1

        numtries4 = 0
        while (question in qssofar) \
                or isuniqueidinquestions(question.uniqueid, alreadyused):
                # no longer care about doubling up of question subtypes
            if numtries4 > 50:
                # this has to do with too many specific subtypes & too few questions of some topic/difficulty combos
                if isuniqueidinquestions(question.uniqueid, alreadyused):
                    print("couldn't find a unique source for " + question.topic + " / " + question.difficulty+" - going to give up and just take whatever question we've got on hand")
                    print("\n\t*** no, seriously-- this is worth paying attention to *** \n")
                break
            question = random.sample(eligibleqs, 1)[0]
            numtries4 += 1

        return question

    # Returns a dictionary of difficulty (string) --> number of questions (int) for this exam session
    def getdiffdistr(self):
        difficultydistribution = {}
        for topic in self.allquestions.keys():
            topicdiffs = self.allquestions[topic]
            for diff in topicdiffs.keys():
                diffqs = topicdiffs[diff]
                if diff not in difficultydistribution.keys():
                    difficultydistribution[diff] = 0
                difficultydistribution[diff] += len(diffqs)
        return difficultydistribution

    # Returns a list of Questions that will comprise one exam
    # Parameters:   sid (string): student id for this exam
    def collectquestionsforoneexam(self, sid="", examdate=None):
        if self.examtype == FLASH:
            print("collecting flash questions for sid ",sid," on date ",examdate) # TODO
            return self.collectflashquestions(sid, examdate)
        else:  # midterm or final
            return self.collectmidtermorfinalquestions(self.examtype, sid, examdate)

    # Returns a list of student ids who are fellow group members of the given student
    #   (could involve multiple distinct groups)
    # Parameters:   sid (string): student id whose group members to collect
    def getgroupmembers(self, sid=""):
        others = []
        if sid != "":
            for grp in self.studentgroups:
                if sid in grp:
                    others = [x for x in grp if x != sid]
        return others

    # Returns a dictionary of topic-->difficulty-->[list of Questions] that are dated no later than
    #   the last Friday strictly before examdate
    # Parameters:   examdate (date object): date for which we're prepping questions
    #                   if None, defaults to the date of this ExamSession
    def getquestionsbeforestartdate(self, examdate=None):
        if examdate is None:
            examdate = self.startdate

        qsbeforecutoff = {}

        for t in self.allquestions.keys():
            thistopicqs = self.allquestions[t]
            for d in thistopicqs.keys():
                thisdiffqs = thistopicqs[d]
                thistopicdiffqs = [q for q in thisdiffqs if
                                   (q.datecompleted is not None and q.datecompleted <= getfrioflastweek(examdate))]
                if len(thistopicdiffqs) > 0:
                    if t not in qsbeforecutoff.keys():
                        qsbeforecutoff[t] = {}
                    if d not in qsbeforecutoff[t].keys():
                        qsbeforecutoff[t][d] = []
                    qsbeforecutoff[t][d].extend(thistopicdiffqs)
        return qsbeforecutoff

    # Returns a list of Questions that will comprise one student's flash exam
    # Parameters:   sid (string): student id whose exam this is
    def collectflashquestions(self, sid="", examdate=None):

        # if this student has already had a flash exam generated, just return those questions
        if self.thisstudentexamexists(sid, FLASH):
            return self.getthisstudentquestionsseen(sid, FLASH)

        # get questions that this student has seen on a (potential) previous exam; ie midterm exam
        alreadyseen = self.getthisstudentquestionsseen(sid=sid, examtype="")
        # get list of other students who have worked with this student (could be empty)
        otherstudentsingroup = self.getgroupmembers(sid)

        diffsdict = examcomposition[FLASH][DIFFS]
        # transform difficulties from dictionary of (difficulty --> number) to
        #   list of question difficulties needed (could be duplicates)
        diffsneeded = []
        for diff in diffsdict.keys():
            for i in range(diffsdict[diff]):
                diffsneeded.append(diff)
        numqs = len(diffsneeded)
        topicsneeded = examcomposition[FLASH][TOPICS]
        # wildcardtopics = examcomposition[FLASH][WILDTOPICS]

        questionsforthisexam = []

        print(examdate) # TODO
        questionspool = self.getquestionsbeforestartdate(examdate)
        if len(questionspool.keys()) <= 0:
            print("There are no questions in the database whose date is early enough to include in an exam dated "+examdate.strftime("%Y-%m-%d"))
            print("Exiting...")
            exit(1)
        wildcardtopics = [t for t in questionspool.keys() if t != DATASET]
        wildcardtopics = list(set(wildcardtopics))

        # randomly combine topics (including assigning a wildcard topic if necessary) with difficulties
        # and make sure that these combinations exist in the eligible questions
        topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)
        while not docombosexist(questionspool, topicslist, diffslist):
            topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)

        for i in range(numqs):
            thequestion = self.getuniquequestion(
                questionsforthisexam,
                topic=topicslist[i],
                difficulty=diffslist[i],
                otherstudents=otherstudentsingroup,
                alreadyused=alreadyseen,
                qspool=questionspool
            )
            if thequestion is not None:
                questionsforthisexam.append(thequestion)
            else:
                print("question with index " + str(i) + " is None")
                # TODO what?

        # record that this student now has had an exam of this type generated, using these questions
        self.addquestionstoexisting(sid, FLASH, questionsforthisexam)

        return questionsforthisexam

    # Returns a list of Questions that will comprise one student's midterm or final exam
    # Parameters:   sid (string): student id whose exam this is
    #               examdate (date object): date of this exam
    def collectmidtermorfinalquestions(self, extype, sid="", examdate=None):

        # if this student has already had an exam of this type generated, just return those questions
        if self.thisstudentexamexists(sid, extype):
            return self.getthisstudentquestionsseen(sid, extype)
        # get questions that this student has seen on a (potential) previous exam; ie flash exam
        alreadyseen = self.getthisstudentquestionsseen(sid, "")
        # get list of other students who have worked with this student (could be empty)
        otherstudentsingroup = self.getgroupmembers(sid)

        diffsdict = examcomposition[extype][DIFFS]
        # transform difficulties from dictionary of (difficulty --> number) to
        #   list of question difficulties needed (could be duplicates)
        diffsneeded = []
        for diff in diffsdict.keys():
            for i in range(diffsdict[diff]):
                diffsneeded.append(diff)
        numqs = len(diffsneeded)
        topicsneeded = [t for t in examcomposition[extype][TOPICS]]
        wildcardtopics = [wt for wt in examcomposition[extype][WILDTOPICS]]

        questionsforthisexam = []

        # TODO - comment first line below / uncomment second to test midterm/final exam generation
        #  with all questions (not restricted by date)
        questionspool = self.getquestionsbeforestartdate(examdate)

        # since Phonological Relationships questions and Dataset questions are always Very Hard,
        #   remove those for the time being while we randomize the other combinations
        vhardtopic = ""
        vharddiff = Question.VHARD
        if PHRELAN in topicsneeded:
            vhardtopic = PHRELAN
            topicsneeded.remove(PHRELAN)
            diffsneeded.remove(Question.VHARD)
        elif DATASET in topicsneeded:
            vhardtopic = DATASET
            topicsneeded.remove(DATASET)
            diffsneeded.remove(Question.VHARD)

        # randomly combine topics (including assigning a wildcard topic if necessary) with difficulties
        #   and make sure that these combinations exist in the eligible questions
        topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)
        while not docombosexist(questionspool, topicslist, diffslist):
            topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)

        # if we took out a very hard question/topic, add it back in
        if vhardtopic != "":
            topicslist.append(vhardtopic)
            diffslist.append(vharddiff)

        # 20201025 - changed from order by easy/med first, then everything else, to...
        # order in which topics were taught
        topicsorder = []
        if extype == MIDTERM:
            topicsorder = midtermtopics
        else:
            topicsorder = finaltopics
        temptopics = []
        tempdiffs = []
        for topic in topicsorder:
            if topic in topicslist:
                idx = topicslist.index(topic)
                tempdiffs.append(diffslist.pop(idx))
                temptopics.append(topicslist.pop(idx))
        if len(topicslist) > 0:
            temptopics.extend(topicslist)
            tempdiffs.extend(diffslist)
        topicslist = temptopics
        diffslist = tempdiffs

        # 20201025 - changed from order by easy/med first, then everything else, to...
        # order in which topics were taught
        # # make sure the exam starts with an easy or medium question
        # #   (check for both in case diffs don't include one or the other)
        # easyormedfound = False
        # idx = 0
        # while easyormedfound is False and idx < numqs:
        #     if diffslist[idx] == Question.MED or diffslist[idx] == Question.EASY:
        #         reordereddiffs = diffslist
        #         diffslist = [reordereddiffs.pop(idx)]
        #         diffslist.extend(reordereddiffs)
        #         reorderedtopics = topicslist
        #         topicslist = [reorderedtopics.pop(idx)]
        #         topicslist.extend(reorderedtopics)
        #         easyormedfound = True
        #     idx += 1

        for i in range(numqs):
            thequestion = self.getuniquequestion(
                questionsforthisexam,
                topic=topicslist[i],
                difficulty=diffslist[i],
                otherstudents=otherstudentsingroup,
                alreadyused=alreadyseen,
                qspool=questionspool
            )
            if thequestion is not None:
                questionsforthisexam.append(thequestion)
            else:
                print("question with index "+str(i)+" is None")
                # TODO what?

        # record that this student now has had an exam of this type generated, using these questions
        self.addquestionstoexisting(sid, extype, questionsforthisexam)

        return questionsforthisexam

    # Adds this sid, exam type, and questions list combination to the collection of existing exams/questions
    # Parameters:   sid (string): the student number whose exam questions we're recording
    #               extype (string): the exam type that the questions are associated with
    #               questions ([list of Questions]): the questions on this student's exam
    def addquestionstoexisting(self, sid, extype, questions):
        if sid not in self.existingexams.keys():
            self.existingexams[sid] = {}
        if extype not in self.existingexams[sid].keys():
            self.existingexams[sid][extype] = []
        self.existingexams[sid][extype].extend(questions)

    # Generate LaTeX source for all questions for this exam session, sorted by topic (and then difficulty);
    #   write to file
    def generatelatexquestionbankbytopic(self, foldername):

        questionbanktex = "LING200-questionbank.tex"
        fullpathtofile = foldername + "/" + questionbanktex

        with open(fullpathtofile, "w", encoding="utf-8") as tf:
            writedochead(tf, "ALL QUESTIONS", "BY TOPIC")

            for topic in self.allquestions.keys():
                for difficulty in self.allquestions[topic].keys():
                    writequestionbank(tf, topic, difficulty, self.allquestions[topic][difficulty])
            writedocfoot(tf)

        # only use this if you are 100% confident the latex is compilable; otherwise python and xetex both hang
        # generatepdf(fullpathtofile)

#
# end of ExamSession class
#


# Returns (topicslist, diffslist) where each is randomly ordered and
#   where any WILD topics in the topics list have been replaced by an actual topic
# Parameters:   topicsneeded (list of strings): topics to arrange
#               diffsneeded (list of strings): difficulties to arrange
#               wildtopicslist (list of strings): possible wildcard topics to use
def maketopicdiffcombo(topicsneeded, diffsneeded, wildtopicslist):
    wildcardtopicsused = []
    # randomly combine topics (including assigning a wildcard topic if necessary) with difficulties
    # and make sure that these combinations exist in the eligible questions
    for t in topicsneeded:
        if t == WILD:
            curwildtopic = random.sample(wildtopicslist, 1)[0]
            while curwildtopic in wildcardtopicsused:
                curwildtopic = random.sample(wildtopicslist, 1)[0]
            wildcardtopicsused.append(curwildtopic)
    topicslist = [t for t in topicsneeded if t != WILD]
    topicslist.extend(wildcardtopicsused)
    topicslist = random.sample(topicslist, len(topicslist))
    diffslist = random.sample(diffsneeded, len(diffsneeded))

    return topicslist, diffslist


# Generate LaTeX markup for one section (topic/difficulty) of the question bank,
#   including instructor notes (if applicable); write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               topic (string): the topic for this section
#               difficulty (string): the difficulty for this section
#               questionslist (list of Questions): the questions to write for this topic/difficulty section
def writequestionbank(texfile, topic, difficulty, questionslist):
    texfile.write("\\textbf{\\underline{\\huge " + topic + " / " + difficulty + "\\\\}}" + N + N)
    for idx, question in enumerate(questionslist):
        completedstring = ""
        if question.datecompleted is None:
            completedstring = "-nodate-"
        else:
            completedstring = question.datecompleted.strftime("%Y%m%d")
        texfile.write(
            "~\\\\" + N + N + "{\\large Question " + str(idx + 1) + "} (completed " + completedstring + ") - ")
        texfile.write(makequestiontex(question, True))
    texfile.write("\\newpage")


# Generate LaTeX preamble and title page markup for one exam day's document; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               title1 (string): first line of title page text
#               title2 (string): second line of title page text
#               onefileperstudent (boolean): whether to write a separate tex/pdf for each student
#                   (as opposed to the default, which is to batch all of one day's exams into one file)
def writedochead(texfile, title1, title2, onefileperstudent=False):
    texfile.write("% Ensure that you compile using XeLaTeX !!! PDFTex has problems with some of the packages used" + N)
    texfile.write("\\documentclass[12pt]{article}" + N)
    texfile.write("\\setlength\\parindent{0pt}" + N + N)
    texfile.write("\\usepackage{parskip}" + N)
    texfile.write("\\usepackage[margin=0.5in]{geometry}" + N)
    texfile.write("\\usepackage{fullpage}" + N)
    texfile.write("\\usepackage{moresize}" + N)

    texfile.write("\\usepackage{graphicx}" + N)
    texfile.write("\\usepackage{caption}" + N)
    texfile.write("\\usepackage{subcaption}" + N)
    texfile.write("\\usepackage{float}" + N)
    texfile.write("\\usepackage{xcolor}" + N)
    texfile.write("\\usepackage{soul}" + N)
    texfile.write("\\usepackage{fontspec}" + N)
    texfile.write("\\setmainfont{Doulos SIL}" + N + N)

    texfile.write("\\begin{document}" + N + N)

    if not onefileperstudent:
        texfile.write("\\begin{center}" + N)
        texfile.write("\\textbf{{\\color{violet}{\\HUGE " + title1 + "\\\\}}}" + N + N)
        texfile.write("\\textbf{{\\color{violet}{\\HUGE " + title2 + "\\\\}}}" + N + N)
        texfile.write("\\end{center}" + N)
        texfile.write("\\newpage" + N + N)


# Generate LaTeX markup for a single exam's title page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               sid (string): student ID for this exam
#               time (string): timeslot for this exam
def writeexamstart(texfile, sid, time):
    texfile.write("\\begin{center}" + N)
    texfile.write("\\textbf{{\\color{blue}{\\HUGE START OF EXAM\\\\}}}" + N + N)
    texfile.write("\\textbf{{\\color{blue}{\\HUGE Student ID: " + sid + "\\\\}}}" + N + N)
    texfile.write("\\textbf{{\\color{blue}{\\HUGE " + time + "\\\\}}}" + N + N)
    texfile.write("\\end{center}" + N)
    texfile.write("\\newpage" + N + N)


# Generate LaTeX markup for a single exam question, including question number,
#   instructor notes (if applicable), and rubric; write to file
# Parameters:   questionnum (integer): question number within this exam
#               question (Question): the question to be written
#               texfile (file object, as from io.open()): .tex file being generated
#               instrcopy (Boolean): whether or not we're writing the isntructor copy of an exam
def writeexamquestiontex(questionnum, question, texfile, instrcopy=False):
    texfile.write("{\\large Question " + str(questionnum) + "}\\\\" + N + N)
    texfile.write(makequestiontex(question, instrcopy, texortsv="tex"))
    if instrcopy is True:
        texfile.write(RUBRIC)
    texfile.write("\\newpage" + N + N)


# Write a line to tsv of midterm or final exam questions - to be used with Canvas
#   Each line includes columns for student number, topic, difficulty, source, question TeX markup (including images),
#   and if applicable: image1 filename, image1 caption, image2 filename, image2 caption
# Parameters:   stid (string): student whose question this is
#               question (Question object): question to be written as part of this student's exam
#               tsvfile (file object, as from io.open()): .tsv file being generated
def writeexamquestiontsv(stid, question, tsvfile):
    tsvfile.write(
        stid + T +
        question.topic + T +
        question.difficulty + T +
        question.source + T +
        makequestiontex(question, instructorversion=False, texortsv="tsv") + T +
        question.image1 + T +
        question.image1caption + T +
        question.image2 + T +
        question.image2caption + N
    )


# Generate LaTeX markup for a single exam's ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
def writeexamend(texfile):
    texfile.write("\\begin{center}" + N)
    texfile.write("\\textbf{{\\color{red}{\\HUGE END OF EXAM}}}\\\\" + N + N)
    texfile.write("\\end{center}" + N)
    texfile.write("\\newpage" + N + N)


# Generate LaTeX markup for one exam day's document ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
def writedocfoot(texfile):
    texfile.write("\\end{document}" + N + N)


# Generate PDF from one .tex source, using XeLaTeX
#   *** only use this if you are 100% confident the LaTeX is compilable; otherwise python and xetex both hang
# Parameters:   texsourcefile (string): path to the .tex file to compile
def generatepdf(texsourcefile):
    x = subprocess.call("xelatex " + texsourcefile)
    if x != 0:
        # never seem to get here, even if the source isn't compilable...
        print("something went wrong with file  " + texsourcefile + " ... :(")


# Returns LaTeX markup for a single exam question
# Parameters:   question (Question): the question to be written
#               instructorversion (Boolean): whether or not we're writing the instructor copy of an exam
def makequestiontex(question, instructorversion=False, texortsv="tex"):
    qtext = ""
    if texortsv == "tex":
        qtext += "Topic: " + question.topic + "\\\\" + N
        qtext += "Source: " + question.source + "\\\\" + N + N
    qtext += question.instructions + "\\\\" + N + N
    if question.data1 != "":
        qtext += dealwithescapes(str(question.data1)) + N + N
    if question.data2 != "":
        qtext += dealwithescapes(str(question.data2)) + N + N
    if question.image1 != "":
        if question.image2 == "":  # only image1 is necessary
            qtext += "\\begin{figure}[H]" + N
            qtext += "\\includegraphics{../images/" + question.image1 + "}" + N
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + N
            qtext += "\\end{figure}" + N

        # otherwise need to include both images arranged as per spreadsheet

        elif question.imagearrangement != "horizontal":  # default vertical
            qtext += "\\begin{figure}[H]" + N
            qtext += "\\includegraphics{../images/" + question.image1 + "}" + N
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + N
            qtext += "\\end{figure}" + N

            qtext += "\\begin{figure}[H]" + N
            qtext += "\\includegraphics{../images/" + question.image2 + "}" + N
            if question.image2caption != "":
                qtext += "\\caption{" + question.image2caption + "}" + N
            qtext += "\\end{figure}" + N

        else:  # side by side
            qtext += "\\begin{figure}[H]" + N
            qtext += "\\begin{subfigure}{.5\\textwidth}" + N
            qtext += "\\centering" + N
            qtext += "\\includegraphics[width=.9\\linewidth]{images/" + question.image1 + "}" + N
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + N
            qtext += "\\end{subfigure}" + N
            qtext += "\\begin{subfigure}{.5\\textwidth}" + N
            qtext += "\\centering" + N
            qtext += "\\includegraphics[width=.9\\linewidth]{images/" + question.image2 + "}" + N
            if question.image1caption != "":
                qtext += "\\caption{" + question.image2caption + "}" + N
            qtext += "\\end{subfigure}" + N
            qtext += "\\end{figure}" + N

    if instructorversion is True:
        qtext += instrnotesprefix + question.instrnotes + N + N
    qtext += N
    if texortsv == "tsv":  # don't want any newlines in the latex that gets stored in a tsv
        qtext = qtext.replace(N + N, "~\\\\")
        qtext = qtext.replace(N, " ")
    return qtext


# Returns the given text such that square brackets will be displayed verbatim
#   (as for IPA transcriptions) rather than trying to interpret them as LaTeX markup
# Parameters:   datatext (string): the text to be checked for []
def dealwithescapes(datatext):
    datatext = datatext.replace("[", "{[")
    datatext = datatext.replace("]", "]}")
    return datatext


# Looks for a command-line argument with the path to a config file;
#   if not found, asks user for input
# Sets random seed
# Returns:  questionspath (string): path to .tsv file containing exam questions
#           signupspath (string): path to .tsv file containing timeslot signup info
#           hasschedule (boolean): True iff students are scheduled for various days/times (as per signupspath)
#           examtype (string): final or midterm
#           examdate (datetime.date): date of exam session (eg midterm or final);
#               None if exam is distributed across signup days/times (as per signupspath)
#           studentgroups (list of list of strings): each sublist indicates students
#               who typically work together and whose exams therefore should not overlap
#               (TODO currently not in use??)
#           onefileperstudent (boolean): True iff we want one tex/pdf file per student, vs exams batched by day
#           generateexamsuptodate (datetime.date): generate exams scheduled up to and including this date (could be None) TODO only for flash?
#           TODO qstartdate (datetime:date): earliest date that questions should be included from
#           TODO qenddate (datetime:date): latest date that questions should be included from
#           TODO topics (list of strings): topics to include in exam (could have duplicates - one entry per question)
#           TODO difficulties (list of strings): difficulties to include in exam (could have duplicates - one entry per question)
def getconfig():
    configpath = ""
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            configpath = sys.argv[1]
    while configpath == "":
        userinput = input("Enter the name of the config file for this exam (see README for help): "+N)
        if os.path.isfile("../config/"+userinput):
            configpath = "../config/"+userinput
        else:
            print(N+"File not found in config directory. Please try again.")

    # default values, in case any info is missing from the config file (some are functional / some not)
    randomseed = "wugz"
    questionsfile = ""
    signupsfile = ""
    hasschedule = True
    examtype = ""
    examdate = None
    studentgroups = []
    qstartdate = None # TODO
    qenddate = None # TODO
    topics = [] # TODO
    diffs = [] # TODO
    generateexamsuptodate = getfriofthisweek(examio.date.today()) # TODO None

    # info tags that identify each line in the config file
    questionstag = "questions:"
    signupstag = "signups:"
    examtypetag = "exam type:"
    studentgroupstag = "student groups:"
    randomseedtag = "random seed:"
    qstarttag = "questions start:" # TODO
    qendtag = "questions end:" # TODO
    topictag = "topics:" # TODO
    difftag = "difficulties:" # TODO
    genuptodatetag = "generate up to:"

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
                    hasschedule = False
                    signupsfile = items[1]
                else:
                    # otherwise we should have detailed signups with student ID, day, time
                    signupsfile = items[0]
            elif cline.startswith(examtypetag):
                txt = cline[len(examtypetag):].strip()
                items = [item.strip() for item in txt.split(" ")]
                examtype = items[0]
                if len(items) > 1:
                    # if there's another entry after the exam type, that's the exam date
                    examdate = examio.makedate(items[1])
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
                    generateexamsuptodate = examio.makedate(txt)
                # else:
                #     generateexamsuptodate = getfriofthisweek(examio.date.today())
            # TODO include / not?
            # elif cline.startswith(qstarttag):
            #     txt = cline[len(qstarttag):].strip()
            #     if len(txt) > 0:
            #         qstartdate = examio.makedate(txt)
            #     else:
            #         qstartdate = examio.makedate("2000-01-01")
            # elif cline.startswith(qendtag):
            #     txt = cline[len(qendtag):].strip()
            #     if len(txt) > 0:
            #         qenddate = examio.makedate(txt)
            #     else:
            #         qenddate = date.today()
            # TODO include / not?
            # elif cline.startswith(topictag):
            #     txt = cline[len(topictag):].strip()
            #     if len(txt) > 0:
            #         topics = [item.strip() for item in txt.split(", ")]
            # elif cline.startswith(difftag):
            #     txt = cline[len(difftag):].strip()
            #     if len(txt) > 0:
            #         difficulties = [item.strip() for item in txt.split(", ")]

            cline = cfile.readline()

    # for repeatable results (I think)
    # currently not using because actual (pseudo)randomization is helping avoid repeated errors
    # random.seed(randomseed)

    filestructure = ""
    while filestructure == "":
        userinput = input(
            "Do you want all of one day's exams in a single pdf (enter 'b' for batch) " + N +
            "or would you prefer each student's exam in its own file (enter 's' for separate)?" + N
        )
        if userinput == "b" or userinput == "s":
            filestructure = userinput
        else:
            print(N+"Not a valid response. Please try again.")
    onefileperstudent = False
    if filestructure == "s":
        onefileperstudent = True

    return questionsfile, signupsfile, hasschedule, examtype, examdate, studentgroups, onefileperstudent, generateexamsuptodate # qstartdate, qenddate  #, topics, difficulties


# Returns all day/time/student info in file as a dictionary of date --> list of (time,studentid)
#   *** note that if this is for a flash exam, this will only collect the info for students who've
#   (a) not yet had an exam generated and
#   (b) are signed up for up to and including the current week
# Parameters:   signupsfilepath (string): path to the .tsv file containing exam scheduling data
#               hasschedule (boolean): True if this exam has scheduled signups (eg 2020W1 flash exams),
#                   False if not (eg 2020W1 MT/final)
#               examtype (string): see constants FINAL MIDTERM and FLASH
#               examdate (datetime.date): the date that the exam is written (if all students are writing at the same time;
#                   ie, it's not an oral exam, with signup slots)
# TODO
def readsignupsfromfile(signupsfilepath, hasschedule, examtype, examdate, generateuptodate):
    signups = {}  # dictionary of date --> list of (time,studentid)

    with io.open(signupsfilepath, "r", encoding="utf-8") as sfile:

        if hasschedule is True:
            df = pd.read_csv(sfile, sep=T, header=0, usecols=["Day", "Time", "SID-5"], keep_default_na=False)
            for index, row in df.iterrows():
                daystring = str(row["Day"])
                day = examio.makedate(daystring)
                if day is None:
                    print("failing: signup dates must contain strings of form yyyy-mm-dd")
                    sys.exit(1)
                time = str(row["Time"])
                stid = str(row["SID-5"])

                dontuse = examtype == FLASH and examio.makedate(day) > generateuptodate # TODO getfriofthisweek(date.today())
                if not dontuse:
                    if day not in signups.keys():
                        signups[day] = []
                    signups[day].append((time, stid))
        else:
            day = examdate
            time = ""
            signups[day] = []
            df = pd.read_csv(sfile, sep=T, header=0, usecols=["SID-5"], keep_default_na=False)
            for index, row in df.iterrows():
                stid = str(row["SID-5"])
                signups[day].append((time, stid))

    return signups


###########################################
# Here it is! The main event!
###########################################

# read metadata from config file
questionsfile, signupsfile, hasschedule, examtype, examdate, studentgroups, onefileperstudent, generateexamsuptodate = getconfig()
# collect questions from file
allqs = examio.readquestionsfromfile("../data/"+questionsfile)
# collect info from file re which exams have been made for which students already
existingexams = examio.readexistingexamsfromfile(EXISTINGEXAMSPICKLEPATH, "../exams")

# collect scheduling info from file
signups = readsignupsfromfile("../data/"+signupsfile, hasschedule, examtype, examdate, generateexamsuptodate)
signupdates = [examio.makedate(d) for d in signups.keys()]
signupdates = [d for d in signupdates if d is not None]
startdate = date.today()
if len(signupdates) > 0:
    startdate = min(signupdates)
# create an ExamSession instance based on info read from config etc
thisexamsession = ExamSession(examtype, allqs, signups, studentgroups, existingexams, startdate, onefileperstudent)

# create folder in which to store the generated exams + question bank for this session
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
foldername = "../exams/"+examtype+"-exams_generated_"+timestamp
if not os.path.exists(foldername):
    os.makedirs(foldername)


# generate all exams for this session (one file for each day, containing all students' exams for that day)
thisexamsession.generatelatexexams(foldername, generateexamsuptodate)

# generate a question bank of all (non-omitted) questions in the .tsv
thisexamsession.generatelatexquestionbankbytopic(foldername)

# save a record of which students have seen which questions (on which exams)
examio.recordexistingexamstofile(thisexamsession.existingexams, EXISTINGEXAMSPICKLEPATH, "../exams")
