#!/bin/bash

PL_QUESTION_PATH=/Users/christinayang/Documents/GitHub/OPB/pl-opb-ind100/questions/FM
WRITE_PATH=/Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank/source/unsorted

array[0]="Kipkeu"
array[1]="KafkaNoNeko"
array[2]="Bluesy1"
array[3]="alebuiles"

size=${#array[@]}
LINK=https://ca.prairielearn.com/pl/course_instance/4024/instructor/course_admin/questions

DIR=w-ready
for FILE in $DIR/*/*.md;
do
    echo $FILE
    cd /Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank
    echo $FILE
    git reset --hard origin/main
    echo $FILE
    out="$(basename $FILE .md)"
    BRANCH_NAME="auto_$(basename $FILE .md)"
    INFO_PATH=/Users/christinayang/Documents/GitHub/OPB/opb-utils/info/$out
    ASSIGN=$(cat $INFO_PATH/assign.txt)
    ISSUE_NUMBER=$(cat $INFO_PATH/issue_number.txt)
    TITLE=$(cat $INFO_PATH/title.txt)
    index=$(($RANDOM % $size))
    REVIEWER=${array[$index]}
    echo "REVIEWER: $REVIEWER"
    echo $ASSIGN
    echo $TITLE
    echo $ISSUE_NUMBER
    echo $BRANCH_NAME
    git checkout -B $BRANCH_NAME
    cp -R /Users/christinayang/Documents/GitHub/OPB/opb-utils/$DIR/$out $WRITE_PATH
    echo "ADDING $WRITE_PATH/$out"
    git add $WRITE_PATH/$out
    git commit -m "Ready for review"
    git push --force-with-lease -u origin $BRANCH_NAME
    echo "PUSHED $FILE SUCCESSFULLY"
    gh pr reopen $BRANCH_NAME
    gh pr edit $BRANCH_NAME --add-label "check_syntax" --add-reviewer $REVIEWER
    # TODO: add "OPB 000: $LINK, Title: $TITLE" + link https://ca.prairielearn.com/pl/course_instance/4024/instructor
    # gh pr comment $BRANCH_NAME --body "OPB 000: $LINK, Title: $TITLE"
    gh pr ready $BRANCH_NAME
    sleep 60
done
