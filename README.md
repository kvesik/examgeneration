# Linguistics random-sampled exam generator

Take a look at [our slides](TODO) from June 4 2021 at ACL|CLA 2021, introducing this project and the pedagogical concepts it's based on.

## Quick Start - how to run samples
1.	Branch or download repo.
2.	Run generateexams.py; this creates .tex files and .tsv files.
   a) It will ask you for the name of the config file, which it will assume is in the `data/` directory.
   b) It will also ask you whether you want to create your exams as one file per *student* or one per *day*.
3.	Open generated .tex sources (generated in a timestamped subdirectory under `exams/`) and compile into pdfs using your favourite LaTeX editor (or you could uncomment the pdf generation lines in the python script, but be aware that these don't handle compilation errors at all gracefully and you could end up with both latex and python processes hanging). Note that you have to use the XeLaTeX engine in order for IPA fonts to work correctly.

## Which files can be copied/edited/customized for your purposes
1. [Question bank](#Question-bank)
2. [Config file](#TODO): info re course, exam type, date(s), topic/difficulty distribution, question order, etc TODO link
3. [Signups schedule](#TODO): for exams where students sign up for individual time slots (eg for an oral exam)
4. [Student IDs list](#TODO): for typical exams (ie done by an entire course or section in one sitting)
5. [Images](#Images): for incorporation into exam questions

TODO
*** As of Sep 20 2020, all four tsvs in "examgeneration" directory are correctly formatted and functional.
5.	Update/save questions spreadsheet as tsv (see comments below in [Updating question bank tsvs](#Updating-question-bank-tsvs))
6.	Save signups spreadsheet as tsv - TODO update this after talking to Kathleen 20200921
7.	Customize config file as per instructions in next section
8.	Run generateexams.py (it looks for a command-line argument with the name of the config file, but if it doesn't find one will ask you for input). This creates .tex files.
9.	Open generated .tex sources (generated in a timestamped subdirectory) and compile into 

### Config file formatting TODO
* Can be named whatever you like.
* Properties can go in any order (ie, entire lines can switch spots).
* Required properties: 
  * questions
  * signups
* Optional properties: 
  * exam type (default = final)
  * student groups (default = none / separate ids with comma / separate groups with semicolon / spaces are ok)
  * random seed (default = wugz)
* Property keys and values must be typed as shown in this example:
```
questions: pathtoquestionsfile_dontusespaces.
signups: pathtosignupsfile/couldbenested.tsv
exam type: midterm
student groups: 1234,3456;8846,2345,1220
random seed: whateveryoulike could have spaces
```

### Current midterm exam characteristics TODO
* 5 questions total: one each from topics transcription, articulatory phonetics, skewed distributions, phonological relationships, and "wild" (wildcard question randomly selected from transcription, articulatory phonetics, phonological relationships, or other).
* Difficulty distribution is either (1x very hard, 5x medium), or (1x very hard, 1x hard, 2x medium, 1x easy).
* Because of the fact that there is a not a full crossing of difficulty & topic, the choosing of questions for midterms is done in an annoyingly hard-coded way. If the question coverage were to improve, we could use the more elegant (and more random) algorithm that's used for the final exams.

### Current final exam characteristics TODO
* 6 questions total: one each from topics acoustics, alternations,  phonological features, syllables, tone, and dataset.
* Difficulty distribution is (2, easy, 2x medium, 1x hard, and 1x very hard). Very hard always comes from the dataset questions.
* The non-dataset topics fully cross the difficulty levels easy/medium/hard, so there's lots of opportunity for randomness in terms of which topics get which difficulties, etc.

### Shared characteristics TODO
* Any students who are grouped together in the config file (eg, who worked together on assignments) will not have any overlap in exam questions (TODO though could have overlap in sources, just with different actual data).
* No individual student's exam will have more than one question with the same question type (eg morphology, signlanguage, etc), based on optional entries in the "QuestionType" column of the questions spreadsheet.

### LaTeX compiling
In order to make it easy to use verbatim input of ipa characters, I am using font packages that require compilation with xelatex. **pdflatex will not work**.

### Student groups TODO
* Any students listed in a group together (see config) will *not* have overlap in their exam questions, but could have overlap in their question sources. For example, the following is currently possible within a group:
  * From source "Day 2 Handout, Question 6" student A gets "Provide the IPA transcription for the word 'grilled'."
  * From source "Day 2 Handout, Question 6" student B gets "Provide the IPA transcription for the word 'cheese'."
  
### Question bank
Our question bank is updated and maintained in Google Sheets, and downloaded/saved as .tsv whenever we want to run the exam generator. You are welcome to do the same, or try a different method. In order for the script to succeed, you *must* have column headers matching the following case-insensitive names (but they can be arranged in any order)...

Columns whose titles must be included AND whose cells must not be empty:
* `uniqueid` - This is used to identify specific questions so we don't have to worry about small edits to question text resulting in an earlier and a later copy of a question being identified as unequal. I use a Google Sheets add-on to auto-generate these (adapted from [this blog post](https://yagisanatode.com/2019/02/09/google-apps-script-create-custom-unique-ids-in-google-sheets/) by Yagisanatode). 
* `topic` - Broad topic for this question (could correspond to the idea of a chapter; eg "Articulatory Phonetics").
* `difficulty` - Difficulty level for this question (you get to choose your own scale; eg "easy", "medium", "hard", "very hard").
* Starts with `source` (eg "source2020term1") - source of this question (eg "Handout 4 Question 8" or "Day 12 Discussion"). There can be more than one source column, but the furthest right one is the onlyone that will be used.
* `datecompleted` - The date this question was addressed in class, in yyyy-mm-dd format. This is handy if you have a full database of questions for the course (eg from last year), but you want to make sure that only the questions covered up to the Friday before any given exam are actually eligible for inclusion.

Columns whose titles must be included BUT whose cells can be left empty:
* `questiontype` - If a value is entered in this column (eg "UR" or "signlanguage" or even "UR,signlanguage"), then no student will get more than one of any of those comma-separated question types on one exam. 
* `instructions` - The main text of the question. The contents must be formatted in a pseudo-LaTeX manner; see [Formatting data for LaTeX](#Formatting data for LaTeX) for details.
* `data1` - Any additional text to be presented below the main text of the question. See [Formatting data for LaTeX](#Formatting data for LaTeX).
* `data2` - Yet more additional text to be presented below the main text of the question. See [Formatting data for LaTeX](#Formatting data for LaTeX).
* `image1` - The filename of an image (no spaces) stored in `exams/images/`, to be presented below instructions and additional data. See [Image sizes](#Image sizes) for details.
* `image2` - The filename of a second image (no spaces) stored in `exams/images/`, to be presented below instructions and additional data. See [Image sizes](#Image sizes) for details.
* `image1caption` - The caption to be displayed for `image1`. See [Formatting data for LaTeX](#Formatting data for LaTeX).
* `image2caption` - The caption to be displayed for `image2`. See [Formatting data for LaTeX](#Formatting data for LaTeX).
* `imagearrangement` - How images (if there are two) should be arranged. Entering "horizontal" in this column will produce side-by-side images; anything else (including empty) will result in image2 being displayed below image1. 
* `omit` - Whether to omit this question from generated exams. Entering "omit" in this column will prevent the question from being used; leaving it blank will include it in the pool of questions to be random-sampled. Generally handy to mark questions as "omit" rather than deleting them completely because equality comparisons across exams/students are done by question ID rather than question text, source, or any other attribute.
* `instructorcomments` - Any additional comments to be displayed on the instructor copy, below the rest of the question text/data/images. See [Formatting data for LaTeX](#Formatting data for LaTeX).

Other columns:
* You can add as many as you want! But they'll be just for your information as you peruse your question bank; this script won't do anything with them (unless their names start with any of the strings above... then things might get weird).

Note of caution: don't leave empty lines anywhere (including the end) in the tsv.

### Images
Images to be used for specific questions are identified in the [Question bank](#Question-bank), and should be stored in `exams\images\`.
* If images are to be placed horizontally next to each other (as per "imagearrangement" column in spreadsheet), they will be auto-scaled so that each takes up half the page.
* If images are placed vertically (default), they are not scaled at all. This means that you should aim for max widths of about 900px.

### Formatting data for LaTeX
Any of the spreadsheet values that will be displayed as text in the exam document must be LaTeX-aware.
* Relevant columns: source, instructions, data1&2, image captions, instructor comments.

What do I mean by "LaTeX-aware"? ...
* Lists should be created using \begin{itemize} \item text 1 \item text 2 \end{itemize}   (or enumerate instead of itemize)
* If you want to see curly braces { } appear in the doc, they need to be escaped \{ \}
* Ampersands and underscores must be escaped: \& \_
* Exception: square brackets are assumed to be around transcriptions; they will be auto-escaped by the python script. This means you *cannot* use them to pass any arguments to commands (eg \item[a.] )
* The font packages I'm using don't permit italics, so use \ul{text to underline} to emphasize text.
* If you want to use quotes, make sure to use `` '' or ` '
* Non-IPA subscripts must be entered using $_{text}$; superscripts get $^{text}$
* Use \\ for line breaks.
* I hope I got them all...

On the bright side: you get to copy/paste IPA symbols instead of having to code them. Yay!

### TODO notes from 20210530 email to KCH
for organizational (eg sharing with the public) purposes, I've adjusted the directory structure of the project
all data files (questions tsv, signups, student id lists, etc) go in data/
all config files go in config/
all images go in exams/images
all exams will be generated into exams/
all source code is in src/
new additions (note additions to sample config files):
for flash exams, you can enter any date up to which to generate exams. the script will go with the later of this coming friday (as before) or the specified date. if you leave out the "generate up to" line from the config, default is this coming friday (as before).
for any kind of exam, you have 4 choices of question ordering (more flexible options coming later!). 
1 (in the order in which question topics are specified - currently hardcorded)
2 (completely random)
3 (one easy or medium question first if applicable, and the rest in random order)
4 (one very hard question last if applicable, and the rest in random order
note that for option 1, if there is more than one "wild" question (eg in flash exams), the order is not guaranteed




