#!/bin/bash

PL_QUESTION_PATH=/Users/christinayang/Documents/GitHub/OPB/pl-opb-ind100/questions/FM
WRITE_PATH=/Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank/source/unsorted

size=${#array[@]}
LINK=https://ca.prairielearn.com/pl/course_instance/4024/instructor/course_admin/questions

DIR=w-fix
for FILE in $DIR/*/*.md;
do
    echo $FILE
    cd /Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank
    echo $FILE
    git reset --hard origin/main
    echo $FILE
    out="$(basename $FILE .md)"
    # BRANCH_NAME="$(basename $FILE .md)"
    BRANCH_NAME="auto_$(basename $FILE .md)"

    INFO_PATH=/Users/christinayang/Documents/GitHub/OPB/opb-utils/info/$out

    git checkout main
    git pull origin main
    git checkout -B $BRANCH_NAME
    git pull origin $BRANCH_NAME
    cp -R /Users/christinayang/Documents/GitHub/OPB/opb-utils/$DIR/$out $WRITE_PATH
    git add $WRITE_PATH/$out
    git commit -m "small fixes"
    git push -u origin $BRANCH_NAME
    echo "PUSHED $FILE SUCCESSFULLY"

    gh pr edit $BRANCH_NAME --remove-label "check_syntax"
    sleep 5
    gh pr edit $BRANCH_NAME --add-label "check_syntax"

    # hub pull-request -m "$BRANCH_NAME" -m "This resolves #$ISSUE_NUMBER
    # OPB 000: $LINK, Title: $TITLE" --assign $ASSIGN
    # # gh pr reopen $BRANCH_NAME
    # gh pr edit $BRANCH_NAME --add-label "check_syntax" # --add-reviewer $REVIEWER
    # # gh pr ready $BRANCH_NAME
    sleep 30
done
