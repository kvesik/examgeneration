# Getting started with Python, GitHub, and $\LaTeX$

*Under construction -- check back soon!*

There are a few options when it comes to deciding how you will download/run the exam generator software, and subsequently typeset the generated $\LaTeX$ files to create PDFs. The list below describes these options and highlights which ones are recommended if you have not used any of these tools before.

 1. Download the Exam Generator source code and directory structure.
    - (a) Recommended approach (slightly more complex to set up than option b, but will allow you to receive future software updates more easily): [Download/install/configure GitHub Desktop](#downloadinstallconfigure-github-desktop).
    - (b) Alternative approach (less complex to set up than option a, but will be trickier to access future software updates): [Download repository from GitHub](#download-repository-from-github).
 3. [Download/install/configure Python](#downloadinstallconfigure-python).
 4. [Download/install Python dependencies](#downloadinstall-python-dependencies).
 5. TODO continued



## Download/install/configure GitHub Desktop

### GitHub Desktop for Windows users

 1. Go to https://desktop.github.com/ and download the latest version via the big purple button:
 <!-- ![Download for Windows (64bit)](images/download-github-windows.png) -->
 <img src="https://github.com/kvesik/examgeneration/blob/master/images/download-github-windows.png"  alt="Download for Windows (64bit)" width="300">
 3. Run the installer by double-clicking the .exe file (probably named something like `GitHubDesktopSetup-x64.exe`) in your Downloads folder.
 4. GitHub Desktop should install itself and then automatically open when it’s done.
 <!-- ![GitHub Desktop is being installed. It'll launch once it is done.](images/install-github.png) -->
 <img src="https://github.com/kvesik/examgeneration/blob/master/images/install-github.png"  alt="GitHub Desktop is being installed. It'll launch once it is done." width="300">
 6. At this point you’ll need to sign in with your GitHub credentials.
    - (a) If you don’t yet have an account, you can click the "Create your free account" link or set one up via the "Sign Up" button in the top right corner at https://github.com/. When it starts asking you questions about who you’re working with, what you’ll be using it for, etc, you can just click "skip personalization" at the bottom of the screen.
    - (b) Once your account is up and running, flip back to GitHub Desktop and sign in via the "Sign in to GitHub.com" button. You’ll be asked to sign in via web browser and then authenticate GitHub Desktop. You should now be logged in via the GitHub Desktop window.
 7. Finally, you’ll need to configure GitHub Desktop to access the Exam Generation code so that you can run it (and keep it up-to-date) on your machine. In GitHub Desktop...
    - (a) Click "Clone a repository from the internet" on the welcome screen.
    - (b) Click the "URL" tab.
    - (c) Copy and paste kvesik/examgeneration into the top field ("Repository URL or GitHub username and repository"), and in the bottom field ("Local path") select a folder for the code to live in on your computer. Click "Clone."
    - (d) Clicking the "Fetch Origin" button at the top right is what refreshes your local copy of the code with any recent updates that have been made by the programmers. If it changes to "Pull Origin" after you click "Fetch Origin" you should click it again. "Fetch" checks to see if there are any updates, and "Pull" means there are in fact new updates that do need to be downloaded onto your computer. ![Fetch origin](images/fetch-github.png) You should open GitHub Desktop and fetch/pull every once in a while (monthly, maybe?). Other than that, though, you likely won’t need to use GitHub Desktop for much.

### GitHub Desktop for Mac users

 1. Go to https://desktop.github.com/ and download the latest version via the big purple button:
 <!-- ![Download for macOS](images/download-github-mac.png) -->
 <img src="https://github.com/kvesik/examgeneration/blob/master/images/download-github-mac.png"  alt="Download for macOS" width="300">
 5. Unzip the installer by double-clicking the .zip file (probably named something like `GitHubDesktop-x64.zip`) in your Downloads folder.
 6. Once it has unzipped, double-click the GitHub Desktop.app file.
 7. GitHub Desktop should install itself and then automatically open when it’s done.
 <!-- ![GitHub Desktop is being installed. It'll launch once it is done.](images/install-github.png) -->
 <img src="https://github.com/kvesik/examgeneration/blob/master/images/install-github.png"  alt="GitHub Desktop is being installed. It'll launch once it is done." width="300">
 6. At this point you’ll need to sign in with your GitHub credentials.
    - (a) If you don’t yet have an account, you can click the "Create your free account" link or set one up via the "Sign Up" button in the top right corner at https://github.com/. When it starts asking you questions about who you’re working with, what you’ll be using it for, etc, you can just click "skip personalization" at the bottom of the screen.
    - (b) Once your account is up and running, flip back to GitHub Desktop and sign in via the "Sign in to GitHub.com" button. You’ll be asked to sign in via web browser and then authenticate GitHub Desktop. You should now be logged in via the GitHub Desktop window.
 7. Finally, you’ll need to configure GitHub Desktop to access the Exam Generation code so that you can run it (and keep it up-to-date) on your machine. In GitHub Desktop...
    - (a) Click "Clone a repository from the internet" on the welcome screen.
    - (b) Click the "URL" tab.
    - (c) Copy and paste kvesik/examgeneration into the top field ("Repository URL or GitHub username and repository"), and in the bottom field ("Local path") select a folder for the code to live in on your computer. Click "Clone."
    - (d) Clicking the "Fetch Origin" button at the top right is what refreshes your local copy of the code with any recent updates that have been made by the programmers. If it changes to "Pull Origin" after you click "Fetch Origin" you should click it again. "Fetch" checks to see if there are any updates, and "Pull" means there are in fact new updates that do need to be downloaded onto your computer.
![Fetch origin](images/fetch-github.png) You should open GitHub Desktop and fetch/pull every once in a while (monthly, maybe?). Other than that, though, you likely won’t need to use GitHub Desktop for much.

## Download repository from GitHub

 1. Go to https://github.com/kvesik/examgeneration , click on the green "Code" button on the right, and select "Download ZIP" from the menu that opens.
    <!-- ![Code / Download ZIP](images/download-code.png) -->
    <img src="https://github.com/kvesik/examgeneration/blob/master/images/download-code.png"  alt="Code / Download ZIP" width="400">
 2. TODO

## Download/install/configure Python

### Python for Windows users

1. Go to https://www.python.org/downloads/ and download the latest version as per the big yellow button (3.11.1 in this case):
![Download the latest version for Windows](images/download-python-windows.png)
3. Run the installer by double-clicking the .exe file (probably named something like `python-3.11.1-amd64.exe`) in your Downloads folder. BUT WAIT! ...
4. Make sure the two boxes below are checked, then click "Install Now": 
![User admin privileges when installing py.exe / Add python.exe to PATH](images/install-python-windows.png)
5. Python should install itself and then display a success message.

### Python for Mac users

1. Go to https://www.python.org/downloads/ and download the latest version as per the big yellow button (3.9.4 in this case): 
![Download the latest version for Mac OS X](images/download-python-mac.png)
3. Run the installer by double-clicking the package file (probably named something like `python-3.11.1-macos11.pkg`) in your Downloads folder.
4. Proceed through the installation.
5. Python should install itself and then display a success message.

## Download/install Python dependencies

### Python dependences for Windows users

TODO

### Python dependences for Mac users

TODO

