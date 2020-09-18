# -*- coding: utf-8 -*-
"""
written May-July 2020 by Kaili Vesik: kvesik@gmail.com
"""

# this class represents one exam, consisting of a set of questions assigned to 
# a particular student on a particular day at a particular time
class Exam:

    # Parameters:   studentid (string): the ID of the student whose exam this is
    #               date (string): the date for which this student's exam is scheduled
    #               time (string): the timeslot for which this student's exam is scheduled
    #               questions (list of Questions): the questions for this student's exam
    def __init__(self, studentid="", date="", time="", questions=[]):
       

        self.studentid = studentid
        self.date = date
        self.time = time
        self.questions = questions


# this class represents one question, with characteristics as drawn from the questions spreadsheet
class Question:

    # class (static) variables 
    EASY = "easy"
    MED = "medium"
    HARD = "hard"
    VHARD = "very hard"

    def __init__(self, topic="", difficulty="", source="", questiontype="", instructions="",data1 = "", data2 = "", image1 = "", image1caption = "", image2 = "", image2caption = "", imagearrangement = "vertical", notes = "", omit = False, instrnotes = ""):
       

        self.topic = topic
        self.difficulty = difficulty
        self.source = source
        self.questiontype = questiontype
        self.instructions = instructions
        self.data1 = data1
        self.data2 = data2
        self.image1 = image1
        self.image1caption = image1caption
        self.image2 = image2
        self.image2caption = image2caption
        self.imagearrangement = imagearrangement
        self.notes = notes
        self.omit = omit
        self.instrnotes = instrnotes

    