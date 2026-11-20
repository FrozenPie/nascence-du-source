cd C:/Nascence
python docs/lab/J-3550_widen_replay.py judge gemma4:12b http://127.0.0.1:11439 > docs/lab/J-3550_data/judge_gemma4.out 2>&1 &
python docs/lab/J-3550_widen_replay.py judge falcon3:7b http://127.0.0.1:11440 > docs/lab/J-3550_data/judge_falcon3.out 2>&1 &
wait
echo ALLDONE > docs/lab/J-3550_data/judges_done.flag
