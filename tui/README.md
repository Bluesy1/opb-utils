# opb-utils question creation TUI
tool for creating question templates for opb stats

### Set-up:
1. create .env file, and copy .env.tui.example there, and fill in.

### Instructions:
1. run `python -m tui --help` from the directory above this one to see what arguments the tui accepts.
1. run `python -m tui` with the appropriate arguments to launch the tui.

> [!WARNING]  
> If you are using `--gpt`, you will need to have credits available to the OpenAI key you are using.

### How save works:
After you have run the tui, a `saved.json` file will be created. This allows you to rerun the previous question without having to re-fill out the questions again. I recommend you save a copy, because it will be overwritten each time you run the program.

See `saved.json` for an example of what the file looks like. If you really know what you are doing, you can fill out the file manually if you don't want to input in the TUI.

### Variables
To specify that something is a variable, wrap it in curly braces, and prefix it with "variablename:"

Ex. for the question:

12.6% are age 65 and over. Approximately what percentage of the population are working age adults (above age 17 to age 65)?

I input it as:

{percent_senior:12.6}% are age 65 and over. Approximately what percentage of the population are working age adults (above age 17 to age 65)?

### To exit

Use `ctrl/cmd+D` to exit/abort the tui.
