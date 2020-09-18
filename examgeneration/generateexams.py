# -*- coding: utf-8 -*-
"""
written May-July 2020 by Kaili Vesik: kvesik@gmail.com
"""

import subprocess
import os
import sys
import random
import io
import pandas as pd
from Exam import Question, Exam


# midterm exam topics
TRANSCR = "Transcription"
ARTPHON = "Articulatory Phonetics"
SKEWED = "Skewed Distributions"
PHRELAN = "Phonological Relationships and Analysis"
WILD = "Wildcard"
OTHER = "Other"

# final exam topics
ACOUS = "Acoustics"
ALTER = "Alternations"
PHONFT = "Phonological Features"
SYLS = "Syllables"
TONE = "Tone"
DATASET = "Dataset"

# exam types
MIDTERM = "midterm"
FINAL = "final"
numquestions = {MIDTERM: 5, FINAL: 6}

wildcardmidtermtopics = [TRANSCR,ARTPHON,PHRELAN,OTHER]

# to be included on instructor copies
instrnotesprefix = "\n~\\\\\nINSTRUCTOR NOTES: "
RUBRIC = "\\vfill\n"+"Excellent (3) ~~~ Good (2.2) ~~~ Fair (1.7) ~~~ Poor (0)\n"

# this class represents one session of exams 
# (for example, a midterm exam for n students taking place over m days)
class ExamSession:
    
    # Parameters:   examtype (string): which exam this is: midterm or final
    #               allquestions ([list of Questions]): the set of Questions to be drawn from for this exam session
    #               signups (dictionary of date --> [list of (time,studentid)]): timelots and corresponding student ids, grouped by date
    #               studentgroups ([list of [lists of strings]]): groups of students whose exams should not overlap
    # Each of these parameters is likely supplied by getconfig(), readquestionsfromfile(), and/or readsignupsfromfile()
    def __init__(self, examtype=FINAL, allquestions=[], signups={}, studentgroups=[]):
       

        self.examtype = examtype
        self.allquestions = allquestions
        self.signups = signups
        self.exams = {} # dictionary of studentid-->Exam
        self.studentgroups = studentgroups
        

    # Generate LaTeX source for one entire exam day's document; write to file
    # Parameters:   texfilepath (string): path to the .tex file to generate
    #               examdate (string): the day whose exam source to generate
    def generatelatexexams_oneday(self,texfilepath,examdate):
        
        sched = signups[examdate]

        instrfilepath = texfilepath.replace(".tex","_instructorcopy.tex")
        with open(texfilepath,"w",encoding="utf-8") as tf:
            with open(instrfilepath,"w",encoding="utf-8") as inf:
                writedochead(tf,examdate,"ALL EXAMS")
                writedochead(inf,examdate,"ALL EXAMS (with notes)")
                
                exams = {}
                for (time,sid) in sched:
                    if sid == "":
                        writeexamstart(tf,"empty",time)
                        writeexamstart(inf,"empty",time)
                        continue
                    qs = self.collectquestionsforoneexam(sid)
                    
                    thisexam = Exam(sid,examdate,time,qs)
                    exams[sid] = thisexam
                    writeexamstart(tf,sid,time)
                    writeexamstart(inf,sid,time)
                    for qidx in range(0,numquestions[examtype]):
                        writeexamquestion(qidx+1,qs[qidx],tf)
                        writeexamquestion(qidx+1,qs[qidx],inf,instrcopy=True)
                    writeexamend(tf,sid,time)
                    writeexamend(inf,sid,time)
                writedocfoot(tf)
                writedocfoot(inf)

    
        
    # Generate LaTeX source for this entire exam session (could be multiple days); write to file
    def generatelatexexams(self):
                
        # filename info for exam TeX sources to be generated
        texfileprefix = "LING200"+examtype+"-"
        texfilesuffix = ".tex"

        # generate an exam for each day, named after days in schedule
        for day in signups.keys():
            examtex = texfileprefix+day.replace(" ","_")+texfilesuffix
            self.generatelatexexams_oneday(examtex, day)
            
            # only use this if you are 100% confident the latex is compilable; otherwise python and xetex both hang
            # generatepdf(examtex)


    # Returns a list of Questions with the given topic and difficulty level
    # Parameters:   topic (string): the topic from which to collect questions; if empty, all topics will be included
    #               difficulty (string): the difficulty from which to collect questions; if empty, all difficulty levels will be included
    def getquestions(self,topic="",difficulty=""):
        topicqs = {}
        selectedqs = []
        if topic != "":        
            topicqs = self.allquestions[topic]
            if difficulty != "":
                selectedqs = topicqs[difficulty]
            else:
                for diff in topicqs.keys():
                    selectedqs.extend(topicqs[diff])
        else: # no topic given
            for topic in self.allquestions.keys():
                if difficulty != "":
                    selectedqs.extend(self.allquestions[topic][difficulty])
                else: # neither topic nor difficulty given
                    topicqs = self.allquestions[topic]
                    for diff in topicqs.keys():
                        selectedqs.extend(topicqs[diff])
        return selectedqs
                           
    
    # Returns unique Question with the given topic and difficulty level
    # Parameters:   qssofar (list of Questions): the selected question must not already be in this list
    #               otherstudents (list of student ids): the selected question must not already be in any of these students' exams
    #               topic (string): the topic from which to collect questions; if empty, the question could be from any topic
    #               difficulty (string): the difficulty from which to collect questions; if empty, the question could be from any difficulty level
    def getuniquequestion(self,qssofar,otherstudents=[],topic="",difficulty=""):
        
        # if this is the midterm and we're choosing a wildcard question, 
        # pick a topic that has a question at the requested difficulty level
        if topic == WILD:
            # pick a random topic
            topic = random.sample(wildcardmidtermtopics,1)[0]
            # if the difficulty was specified, make sure there is a question of that level for the selected topic
            while difficulty != "" and difficulty not in self.allquestions[topic].keys():
                topic = random.sample(wildcardmidtermtopics,1)[0]
        
        # gather a list of all questions of this topic + difficulty, and pick a random one
        eligibleqs = self.getquestions(topic,difficulty)
        question = random.sample(eligibleqs,1)[0]
        
        qtypes = [q.questiontype for q in qssofar if q.questiontype != ""]
        
        otherstudentquestions = []
        for sid in otherstudents:
            if sid in self.exams.keys():
                otherstudentquestions.extend(self.exams[sid].questions)
        
        # make sure that this question isn't already in this exam,
        # and that we're not putting more than one question of this subtype in this exam
        # and that this student doesn't get a question that someone they worked with also has
        while ((question in qssofar) or (question.questiontype in qtypes) or (question in otherstudentquestions)):
            question = random.sample(eligibleqs,1)[0]
            
        return question
        
    
    # Returns a dictionary of difficulty (string) --> number of questions (int) for this exam session
    def getdiffdistr(self):
        difficultydistribution = {}
        for topic in self.allquestions.keys():
            topicdiffs = self.allquestions[topic]
            for diff in topicdiffs.keys():
                diffQs = topicdiffs[diff]
                if diff not in difficultydistribution.keys():
                    difficultydistribution[diff] = 0
                difficultydistribution[diff] += len(diffQs)
        return difficultydistribution
    

    # Returns a list of Questions that will comprise one exam
    # Parameters:   sid (string): student id for this exam
    def collectquestionsforoneexam(self, sid=""):  
        if examtype == MIDTERM:
            return self.collectmidtermquestions(sid)
        elif examtype == FINAL:
            return self.collectfinalquestions(sid)
        else: # don't know what to do if it's not one of those... no questions for you!
            return []
    
    # Returns a list of student ids who are fellow group members of the given student 
    #   (could involve multiple distinct groups)
    # Parameters:   sid (string): student id whose group members to collect
    def getgroupmembers(self,sid=""):
        others = []
        if sid != "":
            for grp in self.studentgroups:
                if sid in grp:
                    others = [x for x in grp if x != sid]
        return others
    
    
    # Returns a list of Questions that will comprise one student's final exam
    # Parameters:   sid (string): student id whose exam this is
    def collectfinalquestions(self, sid=""):  
        
        # get list of other students who have worked with this student (could be empty)
        otherstudentsingroup = self.getgroupmembers(sid) 
            
        diffsneeded = {Question.EASY:2,Question.MED:2,Question.HARD:1,Question.VHARD:1}
        
        questionsforthisexam = []
        
        DSquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=DATASET, difficulty=Question.VHARD)
        while diffsneeded[DSquestion.difficulty] <= 0:
            DSquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=DATASET, difficulty=Question.VHARD)
        diffsneeded[DSquestion.difficulty] -= 1
        questionsforthisexam.append(DSquestion)
        
        ALquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=ALTER)
        while diffsneeded[ALquestion.difficulty] <= 0:
            ALquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=ALTER)
        diffsneeded[ALquestion.difficulty] -= 1
        questionsforthisexam.append(ALquestion)
        
        TOquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=TONE)
        while diffsneeded[TOquestion.difficulty] <= 0:
            TOquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=TONE)
        diffsneeded[TOquestion.difficulty] -= 1
        questionsforthisexam.append(TOquestion)
        
        SYquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=SYLS)
        while diffsneeded[SYquestion.difficulty] <= 0:
            SYquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=SYLS)
        diffsneeded[SYquestion.difficulty] -= 1
        questionsforthisexam.append(SYquestion)
        
        ACquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=ACOUS)
        while diffsneeded[ACquestion.difficulty] <= 0:
            ACquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=ACOUS)
        diffsneeded[ACquestion.difficulty] -= 1
        questionsforthisexam.append(ACquestion)
        
        PFquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=PHONFT)
        while diffsneeded[PFquestion.difficulty] <= 0:
            PFquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=PHONFT)
        diffsneeded[PFquestion.difficulty] -= 1
        questionsforthisexam.append(PFquestion)
        
        
        # always start with easy
        startingq = None
        foundaneasyone = False
        for q in questionsforthisexam:
            if q.difficulty == Question.EASY and foundaneasyone==False:
                startingq = q
                questionsforthisexam.remove(q)
                foundaneasyone=True
        
        # dataset question is second or third
        questionsforthisexam.remove(DSquestion)
        random.shuffle(questionsforthisexam)
        questionsforthisexam = [startingq] + random.sample([DSquestion, questionsforthisexam[0]],2) + questionsforthisexam[1:]
        
        # make sure distribution is correct
        diffs = {Question.EASY:0,Question.MED:0,Question.HARD:0,Question.VHARD:0}
        for q in questionsforthisexam:
            diffs[q.difficulty] += 1
        if not (diffs[Question.EASY]==2 and diffs[Question.MED]==2 and diffs[Question.HARD]==1 and diffs[Question.VHARD]==1):
            print("fail...",diffs)
                
        return questionsforthisexam
    
    # Returns a list of Questions that will comprise one student's midterm exam
    #   ***     note that this is done in a really picky hard-coded manner because
    #           the topics/difficulties are not fully crossed... it can be improved
    #           if/when all topics have questions at all difficulty levels
    # Parameters:   sid (string): student id whose exam this is
    def collectmidtermquestions(self, sid=""):  
        
        # get list of other students who have worked with this student (could be empty)
        otherstudentsingroup = self.getgroupmembers(sid) 
       
        questionsforthisexam = []
        
        SDquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=SKEWED, difficulty=Question.MED)
        questionsforthisexam.append(SDquestion) 
        
        PRquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=PHRELAN, difficulty = Question.VHARD)
        questionsforthisexam.append(PRquestion)
        
        Tquestion = Question()
        Tdifficulty = ""
        APquestion = Question()
        APdifficulty = ""
        WCquestion = ""
        WCdifficulty = Question()
        
        diffdistr = self.getdiffdistr()
        
        # decide whether to have VH,M,M,M,M or VH,H,M,M,E based on distribution of question difficulty levels
        totalMandH = diffdistr[Question.MED]+diffdistr[Question.HARD]
        proportionM = diffdistr[Question.MED]/totalMandH
        
        if random.uniform(0,1) <= proportionM: # VH,M,M,M,M
            Tdifficulty = Question.MED
            APdifficulty = Question.MED
            WCdifficulty = Question.MED
        else: # VH,H,M,M,E
            if random.uniform(0,1) <= 0.5: # AP will be hard
                APdifficulty = Question.HARD
                if random.uniform(0,1) <= 0.5: # T will be medium / WC easy
                    Tdifficulty = Question.MED
                    WCdifficulty = Question.EASY
                else: # T will be easy / WC medium
                    Tdifficulty = Question.EASY
                    WCdifficulty = Question.MED
            else: # T will be hard
                Tdifficulty = Question.HARD
                # AP will be medium / WC easy
                APdifficulty = Question.MED
                WCdifficulty = Question.EASY
           
        Tquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=TRANSCR, difficulty=Tdifficulty)
        questionsforthisexam.append(Tquestion)
        
        APquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=ARTPHON, difficulty=APdifficulty)
        questionsforthisexam.append(APquestion)
        
        WCquestion = self.getuniquequestion(questionsforthisexam, otherstudentsingroup, topic=WILD, difficulty=WCdifficulty)
        questionsforthisexam.append(WCquestion)
               
        
        # always start with medium; simplest way is to begin always with skewed distributions
        questionsforthisexam = questionsforthisexam[0:1] + random.sample(questionsforthisexam[1:5],4)
        return questionsforthisexam
        
     
    # Generate LaTeX source for all questions for this exam session, sorted by topic (and then difficulty); write to file
    def generatelatexquestionbankbytopic(self):
        
        questionbanktex="LING200"+examtype+"-questionbank.tex"
        
        with open(questionbanktex,"w",encoding="utf-8") as tf:
            writedochead(tf,"ALL QUESTIONS","BY TOPIC")
            
            for topic in self.allquestions.keys():
                for difficulty in self.allquestions[topic].keys():
                    self.writequestionbank(tf,topic,difficulty,self.allquestions[topic][difficulty]) 
            writedocfoot(tf)
            
        # only use this if you are 100% confident the latex is compilable; otherwise python and xetex both hang
        # generatepdf(questionbanktex)
        
    
    # Generate LaTeX markup for one section (topic/difficulty) of the question bank,
    #   including instructor notes (if applicable); write to file
    # Parameters:   texfile (file object, as from io.open()): .tex file being generated
    #               topic (string): the topic for this section
    #               difficulty (string): the difficulty for this section
    #               questionslist (list of Questions): the questions to write for this topic/difficulty section
    def writequestionbank(self,texfile,topic,difficulty,questionslist):
        texfile.write("\\textbf{\\underline{\\huge "+topic+" / "+difficulty+"\\\\}}\n\n")
        for idx,question in enumerate(questionslist):
            texfile.write("~\\\\\n\n{\\large Question "+str(idx+1)+"} - ")
            texfile.write(makequestiontex(question,True))
        texfile.write("\\newpage")

### end of ExamSession class


# Generate LaTeX preamble and title page markup for one exam day's document; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               title1 (string): first line of title page text
#               title2 (string): second line of title page text
def writedochead(texfile,title1,title2):
    texfile.write("% Ensure that you compile using XeLaTeX !!! PDFTex has problems with some of the packages used\n")
    texfile.write("\\documentclass[12pt]{article}\n")
    texfile.write("\\setlength\\parindent{0pt}\n\n")
    texfile.write("\\usepackage{parskip}\n")
    texfile.write("\\usepackage[margin=0.5in]{geometry}\n")
    texfile.write("\\usepackage{fullpage}\n")
    texfile.write("\\usepackage{moresize}\n")
    
    texfile.write("\\usepackage{graphicx}\n")
    texfile.write("\\usepackage{caption}\n")
    texfile.write("\\usepackage{subcaption}\n")
    texfile.write("\\usepackage{float}\n")
    texfile.write("\\usepackage{xcolor}\n")
    texfile.write("\\usepackage{soul}\n")
    texfile.write("\\usepackage{fontspec}\n")
    texfile.write("\\setmainfont{Doulos SIL}\n\n")
    
    texfile.write("\\begin{document}\n\n")
    
    texfile.write("\\begin{center}\n")
    texfile.write("\\textbf{{\\color{violet}{\\HUGE "+title1+"\\\\}}}\n\n")
    texfile.write("\\textbf{{\\color{violet}{\\HUGE "+title2+"\\\\}}}\n\n")
    texfile.write("\\end{center}\n")
    texfile.write("\\newpage\n\n")
    

# Generate LaTeX markup for a single exam's title page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               sid (string): student ID for this exam
#               time (string): timeslot for this exam
def writeexamstart(texfile,sid,time):
    texfile.write("\\begin{center}\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE START OF EXAM\\\\}}}\n\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE Student ID: "+sid+"\\\\}}}\n\n")
    texfile.write("\\textbf{{\\color{blue}{\\HUGE "+time+"\\\\}}}\n\n")
    texfile.write("\\end{center}\n")
    texfile.write("\\newpage\n\n")
   
# Generate LaTeX markup for a single exam question, including question number, 
#   instructor notes (if applicable), and rubric; write to file
# Parameters:   questionnum (integer): question number within this exam
#               question (Question): the question to be written
#               texfile (file object, as from io.open()): .tex file being generated
#               instrcopy (Boolean): whether or not we're writing the isntructor copy of an exam
def writeexamquestion(questionnum,question,texfile,instrcopy=False):
    texfile.write("{\\large Question "+str(questionnum)+"}\\\\\n\n")
    texfile.write(makequestiontex(question,instrcopy))
    if instrcopy==True:
        texfile.write(RUBRIC)
    texfile.write("\\newpage\n\n")

# Generate LaTeX markup for a single exam's ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
#               sid (string): student ID for this exam - not currently used
#               time (string): timeslot for this exam - not currently used
def writeexamend(texfile,time,sid):
    texfile.write("\\begin{center}\n")
    texfile.write("\\textbf{{\\color{red}{\\HUGE END OF EXAM}}}\\\\\n\n")
    texfile.write("\\end{center}\n")
    texfile.write("\\newpage\n\n")
    
# Generate LaTeX markup for one exam day's document ending page; write to file
# Parameters:   texfile (file object, as from io.open()): .tex file being generated
def writedocfoot(texfile):
    texfile.write("\\end{document}\n\n")

# Generate PDF from one .tex source, using XeLaTeX
#   *** only use this if you are 100% confident the LaTeX is compilable; otherwise python and xetex both hang
# Parameters:   texsourcefile (string): path to the .tex file to compile
def generatepdf(texsourcefile):
    x = subprocess.call("xelatex "+texsourcefile)
    if x != 0:
        # never seem to get here, even if the source isn't compilable...
        print("something went wrong with file  "+texsourcefile+" ... :(")


# Returns LaTeX markup for a single exam question
# Parameters:   question (Question): the question to be written
#               instructorversion (Boolean): whether or not we're writing the isntructor copy of an exam
def makequestiontex(question,instructorversion=False):
    qtext = ""
    qtext += "Source: "+question.source+"\\\\\n\n"
    qtext += question.instructions+"\\\\\n\n"
    if question.data1 != "":# and data1 != "nan" and data1 != None:
        qtext += dealwithescapes(str(question.data1))+"\n\n"
    if question.data2 != "":# and data2 != "nan" and data2 != None:
        qtext += dealwithescapes(str(question.data2))+"\n\n"
    if question.image1 != "":# and image1 != "nan" and image1 != None:
     
        if question.image2 == "": # only image1 is necessary
            qtext += "\\begin{figure}[H]\n"
            qtext += "\\includegraphics{images/"+question.image1+"}\n"
            if question.image1caption != "":
                qtext += "\\caption{"+question.image1caption+"}\n"
            qtext += "\\end{figure}\n"
            
        # otherwise need to include both images arranged as per spreadsheet
        
        elif question.imagearrangement != "horizontal": # default vertical
            qtext += "\\begin{figure}[H]\n"
            qtext += "\\includegraphics{images/"+question.image1+"}\n"
            if question.image1caption != "":
                qtext += "\\caption{"+question.image1caption+"}\n"
            qtext += "\\end{figure}\n"
            
            qtext += "\\begin{figure}[H]\n"
            qtext += "\\includegraphics{images/"+question.image2+"}\n"
            if question.image2caption != "":
                qtext += "\\caption{"+question.image2caption+"}\n"
            qtext += "\\end{figure}\n"
            
        else: # side by side
            qtext += "\\begin{figure}[H]\n"
            qtext += "\\begin{subfigure}{.5\\textwidth}\n"
            qtext += "\\centering\n"
            qtext += "\\includegraphics[width=.9\\linewidth]{images/"+question.image1+"}\n"
            if question.image1caption != "":
                qtext += "\\caption{"+question.image1caption+"}\n"
            qtext += "\\end{subfigure}\n"
            qtext += "\\begin{subfigure}{.5\\textwidth}\n"
            qtext += "\\centering\n"
            qtext += "\\includegraphics[width=.9\\linewidth]{images/"+question.image2+"}\n"
            if question.image1caption != "":
                qtext += "\\caption{"+question.image2caption+"}\n"
            qtext += "\\end{subfigure}\n"
            qtext += "\\end{figure}\n"
            
    if instructorversion == True:
        qtext += instrnotesprefix+question.instrnotes+"\n\n"
    qtext += "\n"
    return qtext
                    
# Returns the given text such that square brackets will be displayed verbatim 
#   (as for IPA transcriptions) rather than trying to interpret them as LaTeX markup
# Parameters:   datatext (string): the text to be checked for []
def dealwithescapes(datatext):
    datatext = datatext.replace("[","{[")
    datatext = datatext.replace("]","]}")
    return datatext    


# Looks for a command-line argument with the path to a config file;
#   if not found, asks user for input
# Sets random seed
# Returns:  questionspath (string): path to .tsv file containing exam questions
#           signupspath (string): path to .tsv file containing timeslot signup info
#           examtype (string): final or midterm
#           studentgroups (list of list of strings): each sublist indicates students 
#               who typically work together and whose exams therefore should not overlap 
#               (currently not in use)
def getconfig():
    configpath = ""
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            configpath = sys.argv[1]
    while configpath == "":
        userinput = input("Enter the path to the config file for this exam (see README for help): \n")
        if os.path.isfile(userinput):
            configpath = userinput
        else:
            print("\nNot a valid file path. Please try again.")
            
    randomseed = "wugz"
    questionspath = ""
    signupspath = ""
    examtype = ""
    studentgroups = []
    
    questionstag = "questions:"
    signupstag = "signups:"
    examtypetag = "exam type:"
    studentgroupstag = "student groups:"
    randomseedtag = "random seed:"
    with io.open(configpath,"r",encoding="utf-8") as cfile:
        cline = cfile.readline()
        
        while cline != "":
            if cline.startswith(questionstag):
                questionspath = cline[len(questionstag):].strip()
            elif cline.startswith(signupstag):
                signupspath = cline[len(signupstag):].strip()
            elif cline.startswith(examtypetag):
                examtype = cline[len(examtypetag):].strip()
            elif cline.startswith(studentgroupstag):
                txt = cline[len(studentgroupstag):].strip()
                grps = [grp.strip() for grp in txt.split(";")]
                for grp in grps:
                    stdts = [stdt.strip() for stdt in grp.split(",")]
                    studentgroups.append(stdts)
            elif cline.startswith(randomseedtag):
                randomseed = cline[len(randomseedtag):].strip()
                
            
            cline = cfile.readline()
    
    # for repeatable results (I think)
    random.seed(randomseed)
                
    return questionspath, signupspath, examtype, studentgroups

            
# Returns all exam questions in file as a dictionary of topic-->difficulty-->[list of Questions]
# Parameters:   questionsfilepath (string): path to the .tsv file containing exam question data
def readquestionsfromfile(questionsfilepath):
    allquestions = {} # dictionary of topic-->difficulty-->[list of Questions]
    with io.open(questionsfilepath,"r",encoding="utf-8") as qfile:
        df = pd.read_csv(qfile, sep="\t", header=0, names=["topic","difficulty","source","questiontype","instructions","data1","data2","image1","image1caption","image2","image2caption","imagearrangement","notes","omit","instructornotes"], keep_default_na=False)
        for index,row in df.iterrows():
            topic = row["topic"]
            difficulty = row["difficulty"]
            source = row["source"]
            questiontype = row["questiontype"]
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
            if omit == True:
                continue
            
            if topic not in allquestions.keys():
                allquestions[topic] = {}
            if difficulty not in allquestions[topic].keys():
                allquestions[topic][difficulty] = []
 
            currentq = Question(topic,difficulty,source,questiontype,instr,data1,data2,image1,image1caption,image2,image2caption,imagearrangement,notes,omit,instrnotes)
            allquestions[topic][difficulty].append(currentq)
            
    return allquestions
        
# Returns all day/time/student info in file as a dictionary of date --> list of (time,studentid)
# Parameters:   signupsfilepath (string): path to the .tsv file containing exam scheduling data
def readsignupsfromfile(signupsfilepath):
    signups = {} # dictionary of date --> list of (time,studentid)
    
    with io.open(signupsfilepath,"r",encoding="utf-8") as sfile:
        df = pd.read_csv(sfile, sep="\t", header=1, names=["day","time","stid"], keep_default_na=False)
        for index,row in df.iterrows():
            day = str(row["day"])
            time = str(row["time"])
            stid = str(row["stid"])
            
            if day not in signups.keys():
                signups[day] = []
            signups[day].append((time,stid))
 
    return signups        
        

###########################################
# Here it is! The main event!
###########################################

# read metadata from config file
questionspath, signupspath, examtype, studentgroups = getconfig()
# collect questions from file
allqs = readquestionsfromfile(questionspath)
# collect scheduling info from file
signups = readsignupsfromfile(signupspath)

thisexamsession = ExamSession(examtype, allqs, signups, studentgroups)

# generate all exams for this session (one file for each day, containing all students' exams for that day)
thisexamsession.generatelatexexams()

# generate a question bank of all (non-omitted) questions in the .tsv
thisexamsession.generatelatexquestionbankbytopic()


 
