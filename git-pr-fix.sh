#!/bin/bash

PL_QUESTION_PATH=/Users/christinayang/Documents/GitHub/OPB/pl-opb-ind100/questions/FM
WRITE_PATH=/Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank/source/unsorted

DIR=w-fix
for FILE in $DIR/*/*.md;
do
    echo $FILE
    cd /Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank
    echo $FILE
    git reset --hard origin/main
    echo $FILE
    out="$(basename $FILE .md)"
    BRANCH_NAME="$(basename $FILE .md)"
    INFO_PATH=/Users/christinayang/Documents/GitHub/OPB/opb-utils/info/$out
    ASSIGN=$(cat $INFO_PATH/assign.txt)
    ISSUE_NUMBER=$(cat $INFO_PATH/issue_number.txt)
    echo $ASSIGN
    echo $ISSUE_NUMBER
    echo $BRANCH_NAME
    git checkout -B $BRANCH_NAME
    cp -R /Users/christinayang/Documents/GitHub/OPB/opb-utils/$DIR/$out $WRITE_PATH
    echo "ADDING $WRITE_PATH/$out"
    ls
    git add $WRITE_PATH/$out
    git commit -m "Fixes"
    git push --force-with-lease -u origin $BRANCH_NAME
    echo "PUSHED $FILE SUCCESSFULLY"
    gh pr reopen $BRANCH_NAME
    gh pr edit $BRANCH_NAME --remove-label "check_syntax"
    sleep 5
    gh pr edit $BRANCH_NAME --add-label "check_syntax"
    gh pr ready $BRANCH_NAME
done
