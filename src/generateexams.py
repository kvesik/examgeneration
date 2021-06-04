# -*- coding: utf-8 -*-
"""
written May-July 2020 by Kaili Vesik: kvesik@gmail.com
updated Sep-Oct 2020 by Kaili Vesik
updated May-June 2021 by Kaili Vesik
"""


import os
import sys
import random
from datetime import date, datetime
from Exam import Question
import examio_beta20210603 as examio  # TODO return to just examio
from examio_beta20210603 import WILD

EXISTINGEXAMSPICKLEFILE = "existingexams_donotedit.dict"
ORDER_SPECIFIED = 1
ORDER_RANDOM = 2
ORDER_EASYMEDFIRST = 3
ORDER_VHARDLAST = 4


# this class represents one session of exams
# (for example, a midterm exam for n students taking place over m days)
class ExamSession:

    # Parameters:   course (string): name of the course this exam is for
    #               examtype (string): which exam type is this; eg midterm, final, etc
    #               hassignupslots (boolean): whether students have signed up for specific timeslots for this exam (eg oral exam)
    #               allquestions ([list of Questions]): the set of Questions to be drawn from for this exam session
    #               signups (dictionary of date --> [list of (time,studentid)]): timeslots and corresponding
    #                   student ids, grouped by date
    #               studentgroups ([list of [lists of strings]]): groups of students whose exams should not overlap
    #               existingexams (dictionary of studentid --> examtype --> [list of Questions]):
    #                   questions already seen by various students on previous exams
    #               startdate (date object): date that this ExamSession begins (if not provided, defaults to today)
    #               onefileperstudent (boolean): whether we want one pdf per sid
    #                   (as opposed to the default, each day's exams getting batched together into one tex/pdf file)
    #               topics (list of strings): topic distribution (one per question) - could include "WILD"
    #               diffs (list of strings): difficulty distribution (one per question)
    #               topicdiffpairs (list of 2-tuples of strings):
    #                   pre-specified topic/difficulty combos (selected from above two lists) - could include "WILD"
    #               wildtopics (list of strings): topics eligible for wildcard questions
    #               ordering (integer): type of ordering in which to arrange questions (see ORDER_* constants)
    #                   if not provided, defaults to order in which topics are listed
    # Each of these parameters is likely supplied by getconfig(), readquestionsfromfile(), and/or readsignupsfromfile()
    def __init__(self, course="", examtype="", hassignupslots=False, allquestions={}, signups={}, studentgroups=[], existingexams={},
                 startdate=date.today(), onefileperstudent=False, ordering=ORDER_SPECIFIED,
                 topics=[], diffs=[], topicdiffpairs=[], wildtopics=[]):

        self.course = course
        self.examtype = examtype
        self.hassignupslots = hassignupslots
        self.allquestions = allquestions
        self.signups = signups
        self.studentgroups = studentgroups
        self.existingexams = existingexams
        self.startdate = startdate
        self.onefileperstudent = onefileperstudent
        self.ordering = ordering
        self.topics = topics
        self.difficulties = diffs
        self.topicdiffpairs = topicdiffpairs
        self.wildcardtopics = wildtopics

    # Returns True iff we've already generated an exam of the given type for the given sid
    # Parameters:   sid (string): the student ID to check for
    #               examtype (string): the exam type (final, midterm, etc) to check for
    def thisstudentexamexists(self, sid, examtype):
        if sid in self.existingexams.keys():
            if examtype in self.existingexams[sid].keys():
                return True
        return False

    # Returns a list of the exam types that've already been generated (in saved file OR exams currently being built)
    def getexistingexamtypes(self):
        extypes = []
        for sid in self.existingexams.keys():
            extypes.extend([xt for xt in self.existingexams[sid].keys()])
        return list(set(extypes))

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
            # examtypes = list(examcomposition.keys())
            examtypes = self.getexistingexamtypes()
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
    #               rubric (string): the line of text that should be printed at the bottom of each page
    def generatelatexexams_oneday(self, texfilepath, tsvfilepath, examdate, rubric=""):
        print("generating one day's exams / date", examdate)

        sched = self.signups[examdate]

        instrfilepath = texfilepath.replace(".tex", "_instructorcopy.tex")
        with open(instrfilepath, "w", encoding="utf-8") as inf:
            with open(tsvfilepath, "w", encoding="utf-8") as tsvf:
                writedochead(inf, examdate.strftime("%Y%m%d %A"), "ALL EXAMS (with notes)")
                tsvf.write(
                    "Person" + "\t" +
                    "QuestionID" + "\t" +
                    "Topic" + "\t" +
                    "Difficulty" + "\t" +
                    "Source" + "\t" +
                    "Question_latex" + "\t" +
                    "Image1" + "\t" +
                    "Image1Caption" + "\t" +
                    "Image2" + "\t" +
                    "Image2Caption" + "\n"
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

                            writeexamstart(texf, sid, time)
                            writeexamstart(inf, sid, time)
                            for qidx in range(0, len(self.topics)):
                                writeexamquestiontex(qidx + 1, qs[qidx], texf, rubric=rubric)
                                writeexamquestiontex(qidx + 1, qs[qidx], inf, instrcopy=True, rubric=rubric)
                                writeexamquestiontsv(sid, qs[qidx], tsvf)
                            writeexamend(texf)
                            writeexamend(inf)
                        writedocfoot(texf)

                else:  # each student gets their own file

                    for (time, sid) in sched:
                        sidforfilename = sid if sid != "" else "empty"
                        thissidtexfilepath = texfilepath.replace(".tex", "-sid" + sidforfilename + ".tex")
                        with open(thissidtexfilepath, "w", encoding="utf-8") as texf:
                            writedochead(texf, "", "", onefileperstudent=self.onefileperstudent)
                            if sid == "":
                                writeexamstart(texf, "empty", time)
                                writeexamstart(inf, "empty", time)
                                continue
                            qs = self.collectquestionsforoneexam(sid, examdate)

                            writeexamstart(texf, sid, time)
                            writeexamstart(inf, sid, time)
                            for qidx in range(0, len(self.topics)):
                                writeexamquestiontex(qidx + 1, qs[qidx], texf, rubric=rubric)
                                writeexamquestiontex(qidx + 1, qs[qidx], inf, instrcopy=True, rubric=rubric)
                                writeexamquestiontsv(sid, qs[qidx], tsvf)
                            writeexamend(texf)
                            writedocfoot(texf)
                            writeexamend(inf)

                writedocfoot(inf)

    # Generate LaTeX source for this entire exam session (could be multiple days); write to file
    # Also generate a tsv for this entire exam session (for piping into Canvas); write to file
    # Parameters:   foldername (string): the directory to which exam materials should be generated
    #               generateuptodate (datetime.date): the date up to which exams should be generated
    #                   if empty, defaults to today
    #               rubric (string): the line of text that should be printed at the bottom of each page
    def generatelatexexams(self, foldername, generateuptodate=date.today(), rubric=""):

        # filename info for exam TeX & tsv sources to be generated
        texfileprefix = self.course.replace(" ", "_") + self.examtype.replace(" ", "_") + "-"
        texfilesuffix = ".tex"
        tsvfilesuffix = ".tsv"

        # generate an exam for each day, named after days in schedule
        for thedate in self.signups.keys():  # should be a date object

            # only generate exams if the exam is not scheduled
            if (self.hassignupslots and (thedate <= examio.getfriofthisweek(thedate) or thedate <= generateuptodate)) \
                    or not self.hassignupslots:
                examtex = texfileprefix + thedate.strftime("%Y%m%d%A") + texfilesuffix
                fullpathtotex = foldername + "/" + examtex
                fullpathtotsv = fullpathtotex.replace(texfilesuffix, tsvfilesuffix)
                self.generatelatexexams_oneday(fullpathtotex, fullpathtotsv, thedate, rubric)

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
        if topic != "" and topic in qspool.keys():  # given a specific topic
            topicqs = qspool[topic]
            if difficulty != "" and difficulty in topicqs.keys():  # given a specific difficulty
                selectedqs = topicqs[difficulty]
            else:  # topic  but no difficulty specified
                for diff in topicqs.keys():
                    selectedqs.extend(topicqs[diff])
        else:  # no topic given
            for topic in qspool.keys():
                if difficulty != "" and difficulty in qspool[topic].keys():  # no topic but given a specific difficulty
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
            if sid in self.existingexams.keys():
                sidexams = self.existingexams[sid]
                if self.examtype in sidexams.keys():
                    otherstudentquestions.extend(sidexams[self.examtype])

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
                    # print("group members: ", otherstudents)
                elif isuniqueidinquestions(question.uniqueid, otherstudentquestions):
                    print("couldn't find a question not in a group member's exam for " + question.topic + " / " + question.difficulty+" - going to give up and allow overlap with group members")
                    # print("group members: ", otherstudents)
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
                                   (q.datecompleted is not None and q.datecompleted <= examio.getfrioflastweek(examdate))]
                if len(thistopicdiffqs) > 0:
                    if t not in qsbeforecutoff.keys():
                        qsbeforecutoff[t] = {}
                    if d not in qsbeforecutoff[t].keys():
                        qsbeforecutoff[t][d] = []
                    qsbeforecutoff[t][d].extend(thistopicdiffqs)
        return qsbeforecutoff

    # Returns two lists of strings (ordered topics and difficulties)
    # Parameters:   ordering (integer): type of ordering in which to arrange questions (see ORDER_* constants)
    #               topicslist (list of strings): question topics for this exam;
    #                   WILD not permitted (must have already been assigned a specific wildcard topic)
    #               diffslist (list of strings): corresponding difficulty levels for topics
    def ordertopicsdiffs(self, ordering, topicslist, diffslist):
        topicsorder = []
        diffsorder = []

        if ordering == ORDER_SPECIFIED:
            specifiedorder = self.topics
            topicscountdown = [t for t in topicslist]
            diffscountdown = [d for d in diffslist]

            for t in specifiedorder:
                if t == WILD:
                    # make a place marker and add in the leftover questions once the specific topics have been populated
                    topicsorder.append(WILD)
                    diffsorder.append(WILD)
                else:
                    idx = topicscountdown.index(t)
                    topicsorder.append(topicscountdown.pop(idx))
                    diffsorder.append(diffscountdown.pop(idx))

            # the following only does something if there are some wildcard questions to deal with
            randomwildorder = random.sample(range(len(topicscountdown)), len(topicscountdown))
            for rw in randomwildorder:
                if WILD in topicsorder:
                    idx = topicsorder.index(WILD)
                    topicsorder[idx] = topicscountdown[rw]
                    diffsorder[idx] = diffscountdown[rw]

        elif ordering == ORDER_RANDOM:
            randomwildorder = random.sample(range(len(topicslist)), len(topicslist))
            for rw in randomwildorder:
                topicsorder.append(topicslist[rw])
                diffsorder.append(diffslist[rw])

        elif ordering == ORDER_EASYMEDFIRST:
            # make sure the exam starts with an easy or medium question, if it exists
            #   (check for both in case diffs don't include one or the other)

            topicscountdown = [t for t in topicslist]
            diffscountdown = [d for d in diffslist]
            easyormedfound = False
            idx = 0
            while easyormedfound is False and idx < len(topicslist):
                if diffslist[idx] == Question.MED or diffslist[idx] == Question.EASY:
                    topicsorder = [topicscountdown.pop(idx)]
                    diffsorder = [diffscountdown.pop(idx)]
                    easyormedfound = True
                idx += 1

            # recursively randomize the rest of the questions
            topicscountdown, diffscountdown = self.ordertopicsdiffs(ORDER_RANDOM, topicscountdown, diffscountdown)
            topicsorder.extend(topicscountdown)
            diffsorder.extend(diffscountdown)

        elif ordering == ORDER_VHARDLAST:
            # make sure the exam ends with a very hard question, if it exists

            topicscountdown = [t for t in topicslist]
            diffscountdown = [d for d in diffslist]
            vhardfound = False
            idx = 0
            # identify the very hard question, if it exists
            while vhardfound is False and idx < len(topicslist):
                if diffslist[idx] == Question.VHARD:
                    topicsorder = [topicscountdown.pop(idx)]
                    diffsorder = [diffscountdown.pop(idx)]
                    vhardfound = True
                idx += 1

            # recursively randomize the rest of the questions
            topicscountdown, diffscountdown = self.ordertopicsdiffs(ORDER_RANDOM, topicscountdown, diffscountdown)
            topicsorder.extend(topicscountdown)
            topicsorder.reverse()
            diffsorder.extend(diffscountdown)
            diffsorder.reverse()

        return topicsorder, diffsorder

    # Returns a list of Questions that will comprise one student's exam
    # Parameters:   sid (string): student id whose exam this is
    #               examdate (date object): date of this exam
    def collectquestionsforoneexam(self, sid="", examdate=None):

        # if this student has already had an exam of this type generated, just return those questions
        if self.thisstudentexamexists(sid, self.examtype):
            return self.getthisstudentquestionsseen(sid, self.examtype)
        # get questions that this student has seen on any (potential) previous exama
        alreadyseen = self.getthisstudentquestionsseen(sid, "")
        # get list of other students who have worked with this student (could be empty)
        otherstudentsingroup = self.getgroupmembers(sid)

        questionsforthisexam = []

        questionspool = self.getquestionsbeforestartdate(examdate)
        wildcardtopics = [t for t in questionspool.keys() if t in self.wildcardtopics]
        wildcardtopics = list(set(wildcardtopics))

        topicsavailable = [t for t in questionspool.keys()]
        diffsavailable = []
        for t in topicsavailable:
            diffsavailable.extend(questionspool[t].keys())
        diffsavailable = list(set(diffsavailable))

        # sanity checks - otherwise we may end up in an infinite loop looking for questions that don't exist
        if len(questionspool.keys()) <= 0:
            print("There are no questions within date range to include in an exam dated "
                  + examdate.strftime("%Y-%m-%d"))
            print("----- Exiting -----")
            sys.exit(1)
        topicsnotavailable = []
        for t in self.topics + wildcardtopics:
            if t != WILD and t not in topicsavailable:
                topicsnotavailable.append(t)
        if len(topicsnotavailable) > 0:
            print("Topics requested for this exam but not existing (or not within date range) in question bank:")
            print(list(set(topicsnotavailable)))
            print("----- Exiting -----")
            sys.exit(1)
        diffsnotavailable = []
        for d in self.difficulties:
            if d not in diffsavailable:
                diffsnotavailable.append(d)
        if len(diffsnotavailable) > 0:
            print("Difficulties requested for this exam but not existing (or not within date range) in question bank:")
            print(list(set(diffsnotavailable)))
            print("----- Exiting -----")
            sys.exit(1)
        tdpairsnotavailable = []
        for t, d in self.topicdiffpairs:
            if t != WILD:
                if d not in questionspool[t].keys():
                    tdpairsnotavailable.append((t, d))
        if len(tdpairsnotavailable) > 0:
            print("Specific topic/difficulty pairs requested for this exam but not existing (or not within date range) in question bank:")
            print(list(set(tdpairsnotavailable)))
            print("----- Exiting -----")
            sys.exit(1)

        topicsneeded = [t for t in self.topics]
        diffsneeded = [d for d in self.difficulties]
        # if there is one or more qustions that need specific topic/difficulty combinations,
        # remove those for now while we randomize the other combinations
        for t, d in self.topicdiffpairs:
            topicsneeded.remove(t)
            diffsneeded.remove(d)

        # randomly combine topics (including assigning a wildcard topic if necessary) with difficulties
        #   and make sure that these combinations exist in the eligible questions
        topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)
        numiterations = 0
        while not docombosexist(questionspool, topicslist, diffslist) and numiterations < 100:
            topicslist, diffslist = maketopicdiffcombo(topicsneeded, diffsneeded, wildcardtopics)
            numiterations += 1
        if numiterations >= 100:
            print("Looks like we might be heading into an infite loop looking for topic/difficulty combinations;")
            print("please double-check that your distributions are feasible.")
            print("----- Exiting -----")
            sys.exit(1)

        # if we took out any specific topic/diff combos, add them back in
        for t, d in self.topicdiffpairs:
            thetopic = t
            if t == "WILD":
                # we need to choose actual topics for any of the specific topic/diff combos that were wildcard questions
                thetopic = random.sample(wildcardtopics, 1)[0]
            topicslist.append(thetopic)
            diffslist.append(d)

        topicsorder, diffsorder = self.ordertopicsdiffs(self.ordering, topicslist, diffslist)

        # for i in range(numqs):
        for i, topic in enumerate(topicsorder):
            thequestion = self.getuniquequestion(
                questionsforthisexam,
                topic,  # =topicsorder[i],
                difficulty=diffsorder[i],
                otherstudents=otherstudentsingroup,
                alreadyused=alreadyseen,
                qspool=questionspool
            )
            if thequestion is not None:
                questionsforthisexam.append(thequestion)
            else:
                print("question with index "+str(i)+" is None")
                # TODO - then what?

        # record that this student now has had an exam of this type generated, using these questions
        self.addquestionstoexisting(sid, self.examtype, questionsforthisexam)

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

        questionbanktex = self.course.replace(" ", "_")+"-questionbank.tex"
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
# ^^^ end of ExamSession class ^^^
#


#
# vvv helper functions vvv
#

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


# Returns a (flattened) list of all the Questions in the input, no longer in a hierarchy of topic/difficulty
# Parameters:   qsdict (dictionary of topic --> difficulty --> [list of Questions]): the dictionary to flatten
def flattenqsdict(qsdict):
    flattenedqs = []
    for topic in qsdict.keys():
        for difficulty in qsdict[topic].keys():
            flattenedqs.extend(qsdict[topic][difficulty])
    return flattenedqs


# Generate LaTeX markup for one section (topic/difficulty) of the question bank,
#   including instructor notes (if applicable); write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               topic (string): the topic for this section
#               difficulty (string): the difficulty for this section
#               questionslist (list of Questions): the questions to write for this topic/difficulty section
def writequestionbank(texfile, topic, difficulty, questionslist):
    texfile.write("\\textbf{\\underline{\\huge " + topic + " / " + difficulty + "\\\\}}" + "\n\n")
    for idx, question in enumerate(questionslist):
        completedstring = ""
        if question.datecompleted is None:
            completedstring = "-nodate-"
        else:
            completedstring = question.datecompleted.strftime("%Y%m%d")
        texfile.write(
            "~\\\\" + "\n" + "\n" + "{\\large Question " + str(idx + 1) + "} (completed " + completedstring + ") - ")
        texfile.write(makequestiontex(question, True))
    texfile.write("\\newpage")


# Generate LaTeX preamble and title page markup for one exam day's document; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               title1 (string): first line of title page text
#               title2 (string): second line of title page text
#               onefileperstudent (boolean): whether to write a separate tex/pdf for each student
#                   (as opposed to the default, which is to batch all of one day's exams into one file)
def writedochead(texfile, title1, title2, onefileperstudent=False):
    texfile.write("% Ensure that you compile using XeLaTeX !!! PDFTex has problems with some of the packages used \n")
    texfile.write("\\documentclass[12pt]{article}" + "\n")
    texfile.write("\\setlength\\parindent{0pt}" + "\n\n")
    texfile.write("\\usepackage{parskip}" + "\n")
    texfile.write("\\usepackage[margin=0.5in]{geometry}" + "\n")
    texfile.write("\\usepackage{fullpage}" + "\n")
    texfile.write("\\usepackage{moresize}" + "\n")

    texfile.write("\\usepackage{graphicx}" + "\n")
    texfile.write("\\usepackage{caption}" + "\n")
    texfile.write("\\usepackage{subcaption}" + "\n")
    texfile.write("\\usepackage{float}" + "\n")
    texfile.write("\\usepackage{xcolor}" + "\n")
    texfile.write("\\usepackage{soul}" + "\n")
    texfile.write("\\usepackage{fontspec}" + "\n")
    texfile.write("\\setmainfont{Doulos SIL}" + "\n\n")

    texfile.write("\\begin{document}" + "\n\n")

    if not onefileperstudent:
        texfile.write("\\begin{center}" + "\n")
        texfile.write("\\textbf{{\\color{violet}{\\HUGE " + title1 + "\\\\}}}" + "\n\n")
        texfile.write("\\textbf{{\\color{violet}{\\HUGE " + title2 + "\\\\}}}" + "\n\n")
        texfile.write("\\end{center}" + "\n")
        texfile.write("\\newpage" + "\n\n")


# Generate LaTeX markup for a single exam's title page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               sid (string): student ID for this exam
#               time (string): timeslot for this exam
def writeexamstart(texfile, sid, time):
    texfile.write("\\begin{center}" + "\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE START OF EXAM\\\\}}}" + "\n\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE Student ID: " + sid + "\\\\}}}" + "\n\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE " + time + "\\\\}}}" + "\n\n")
    texfile.write("\\end{center}" + "\n")
    texfile.write("\\newpage" + "\n\n")


# Generate LaTeX markup for a single exam question, including question number,
#   instructor notes (if applicable), and rubric; write to file
# Parameters:   questionnum (integer): question number within this exam
#               question (Question): the question to be written
#               texfile (file object, as from io.open()): .tex file being generated
#               instrcopy (Boolean): whether or not we're writing the isntructor copy of an exam
#               rubric (string): the line of text that should be printed at the bottom of each page
def writeexamquestiontex(questionnum, question, texfile, instrcopy=False, rubric=""):
    texfile.write("{\\large Question " + str(questionnum) + "}\\\\" + "\n\n")
    texfile.write(makequestiontex(question, instrcopy, texortsv="tex"))
    texfile.write("\\vfill" + "\n" + rubric + "\n")
    texfile.write("\\newpage" + "\n\n")


# Write a line to tsv of exam questions - to be used with Canvas, eg
#   Each line includes columns for student number, topic, difficulty, source, question TeX markup (including images),
#   and if applicable: image1 filename, image1 caption, image2 filename, image2 caption
# Parameters:   stid (string): student whose question this is
#               question (Question object): question to be written as part of this student's exam
#               tsvfile (file object, as from io.open()): .tsv file being generated
def writeexamquestiontsv(stid, question, tsvfile):
    tsvfile.write(
        stid + "\t" +
        question.uniqueid + "\t" +
        question.topic + "\t" +
        question.difficulty + "\t" +
        question.source + "\t" +
        makequestiontex(question, instructorversion=False, texortsv="tsv") + "\t" +
        question.image1 + "\t" +
        question.image1caption + "\t" +
        question.image2 + "\t" +
        question.image2caption + "\n"
    )


# Generate LaTeX markup for a single exam's ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
def writeexamend(texfile):
    texfile.write("\\begin{center}" + "\n")
    texfile.write("\\textbf{{\\color{red}{\\HUGE END OF EXAM}}}\\\\" + "\n\n")
    texfile.write("\\end{center}" + "\n")
    texfile.write("\\newpage" + "\n\n")


# Generate LaTeX markup for one exam day's document ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
def writedocfoot(texfile):
    texfile.write("\\end{document}" + "\n\n")


# Returns LaTeX markup for a single exam question
# Parameters:   question (Question): the question to be written
#               instructorversion (Boolean): whether or not we're writing the instructor copy of an exam
def makequestiontex(question, instructorversion=False, texortsv="tex"):
    qtext = ""
    if texortsv == "tex":
        qtext += "Topic: " + question.topic + "\\\\" + "\n"
        qtext += "Source: " + question.source + "\\\\" + "\n\n"
    qtext += question.instructions + "\\\\" + "\n\n"
    if question.data1 != "":
        qtext += dealwithescapes(str(question.data1)) + "\n\n"
    if question.data2 != "":
        qtext += dealwithescapes(str(question.data2)) + "\n\n"
    if question.image1 != "":
        if question.image2 == "":  # only image1 is necessary
            qtext += "\\begin{figure}[H]" + "\n"
            qtext += "\\includegraphics{../images/" + question.image1 + "}" + "\n"
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + "\n"
            qtext += "\\end{figure}" + "\n"

        # otherwise need to include both images arranged as per spreadsheet

        elif question.imagearrangement != "horizontal":  # default vertical
            qtext += "\\begin{figure}[H]" + "\n"
            qtext += "\\includegraphics{../images/" + question.image1 + "}" + "\n"
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + "\n"
            qtext += "\\end{figure}" + "\n"

            qtext += "\\begin{figure}[H]" + "\n"
            qtext += "\\includegraphics{../images/" + question.image2 + "}" + "\n"
            if question.image2caption != "":
                qtext += "\\caption{" + question.image2caption + "}" + "\n"
            qtext += "\\end{figure}" + "\n"

        else:  # side by side
            qtext += "\\begin{figure}[H]" + "\n"
            qtext += "\\begin{subfigure}{.5\\textwidth}" + "\n"
            qtext += "\\centering" + "\n"
            qtext += "\\includegraphics[width=.9\\linewidth]{images/" + question.image1 + "}" + "\n"
            if question.image1caption != "":
                qtext += "\\caption{" + question.image1caption + "}" + "\n"
            qtext += "\\end{subfigure}" + "\n"
            qtext += "\\begin{subfigure}{.5\\textwidth}" + "\n"
            qtext += "\\centering" + "\n"
            qtext += "\\includegraphics[width=.9\\linewidth]{images/" + question.image2 + "}" + "\n"
            if question.image1caption != "":
                qtext += "\\caption{" + question.image2caption + "}" + "\n"
            qtext += "\\end{subfigure}" + "\n"
            qtext += "\\end{figure}" + "\n"

    if instructorversion is True:
        qtext += "\n" + "~\\\\" + "\n" + "INSTRUCTOR NOTES: " + question.instrnotes + "\n\n"
    qtext += "\n"
    if texortsv == "tsv":  # don't want any newlines in the latex that gets stored in a tsv
        qtext = qtext.replace("\n\n", "~\\\\")
        qtext = qtext.replace("\n", " ")
    return qtext


# Returns the given text such that square brackets will be displayed verbatim
#   (as for IPA transcriptions) rather than trying to interpret them as LaTeX markup
# Parameters:   datatext (string): the text to be checked for []
def dealwithescapes(datatext):
    datatext = datatext.replace("[", "{[")
    datatext = datatext.replace("]", "]}")
    return datatext


###########################################
# Here it is! The main event!
###########################################
def main():
    # read metadata from config file
    questionsfile, signupsfile, hassignupslots, course, examtype, examdate, \
        studentgroups, onefileperstudent, generateexamsuptodate, ordering, \
        topics, diffs, topicdiffpairs, wildtopics, rubric \
        = examio.getconfig()

    # collect questions from file
    allqs = examio.readquestionsfromfile("../data/" + questionsfile)
    # collect info from file re which exams have been made for which students already
    existingexams = examio.readexistingexamsfromfile(EXISTINGEXAMSPICKLEFILE, "../exams")

    # collect scheduling info from file
    signups = examio.readsignupsfromfile("../data/" + signupsfile,
                                         hassignupslots, examtype, examdate, generateexamsuptodate)
    signupdates = [examio.makedate(d) for d in signups.keys()]
    signupdates = [d for d in signupdates if d is not None]
    startdate = date.today()
    if len(signupdates) > 0:
        startdate = min(signupdates)
    # create an ExamSession instance based on info read from config etc
    thisexamsession = ExamSession(course, examtype, hassignupslots, allqs, signups, studentgroups, existingexams, startdate,
                                  onefileperstudent, ordering, topics, diffs, topicdiffpairs, wildtopics)

    # create folder in which to store the generated exams + question bank for this session
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    foldername = "../exams/" + course.replace(" ", "_") + examtype.replace(" ", "_") + "-exams_generated_" + timestamp
    if not os.path.exists(foldername):
        os.makedirs(foldername)

    # generate all exams for this session (one file for each day, containing all students' exams for that day)
    thisexamsession.generatelatexexams(foldername, generateexamsuptodate, rubric)

    # generate a question bank of all (non-omitted) questions in the .tsv
    thisexamsession.generatelatexquestionbankbytopic(foldername)

    # save a record of which students have seen which questions (on which exams)
    examio.recordexistingexamstofile(thisexamsession.existingexams, EXISTINGEXAMSPICKLEFILE, "../exams")


if __name__ == "__main__":
    main()
