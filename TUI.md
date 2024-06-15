# opb-utils question creation TUI
tool for creating question templates for opb stats

### Set-up:
1. create .env file, and copy .env.tui.example there, and fill in.
1. Run `nltk.download('punkt')` and `nltk.download('stopwords')` (there may be something else too, it'll throw an error if you need to download it, and tell you which to download)

### Warning:
Turn `Testing=True` to prevent pushing to the repo. (located at top of `tui.py`)

### Instructions:
1. run `python tui.py`

### How save works:
After you have filled out tui.py, a saved.json file will be created. This allows you to rerun the previous question without having to re-fill out the questions again. I recommend you save a copy, because it will be overwritten each time you run the program.

See `saved.json` for an example of what the file looks like. If you really know what you are doing, you can fill out the file manually if you don't want to input in the TUI.

### Variables
To specify that something is a variable, wrap it in curly braces, and prefix it with "variablename:"

Ex. for the question:

12.6% are age 65 and over. Approximately what percentage of the population are working age adults (above age 17 to age 65)?

I input it as:

{percent_senior:12.6}% are age 65 and over. Approximately what percentage of the population are working age adults (above age 17 to age 65)?

### To exit
1. Pressing `cmd+d` works for me to exit the program.

### DEBUGGING:
Committing to Github + creating PRs is done in `git-pr-first.sh`
If it's not letting you push, and you are certain you want to commit the whole file,
replace `git push -u origin $BRANCH_NAME` with
`git push --force-with-lease -u origin $BRANCH_NAME`
Note, this force-pushing, so will erase all previous commits. Be careful when using this.
