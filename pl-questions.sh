#!/bin/bash
PL_QUESTION_PATH=/Users/christinayang/Documents/GitHub/OPB/pl-opb-ind100/questions/FM
CHECKQ=/Users/christinayang/Documents/GitHub/OPB/instructor_stats_bank/scripts/checkq.py
CHECKQ=/Users/christinayang/Documents/GitHub/OPB/opb-utils/checkq.py
WRITE_PATH=/Users/christinayang/Documents/GitHub/instructor_stats_bank/source/unsorted

# # python $CHECKQ $WRITE_PATH/q01_case_study_using_stents_to_prevent_strokes.md $PL_QUESTION_PATH
# python $CHECKQ ./questions/q01_case_study_using_stents_to_prevent_strokes/q01_case_study_using_stents_to_prevent_strokes.md --output_root $PL_QUESTION_PATH
# # python $CHECKQ ../instructor_stats_bank/source/001.Math/Algebra/Smudge/Smudge.md --output_root $PL_QUESTION_PATH
# python $CHECKQ ./questions/q03_data_basics/q03_data_basics.md --output_root $PL_QUESTION_PATH

# opb-utils/questions/q03_data_basics/q03_data_basics.md

for FILE in questions/*/*.md; 
do python $CHECKQ $FILE --output_root $PL_QUESTION_PATH
# do echo $FILE; 
done
