---
name: what-to-demo
description: Review notes from the past two weeks to determine what could be demoed.
---

BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`

Look at the notes of the past 2 weeks in the directory `{BASE_DIR}` and determine what could be demoed.
Write the output to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.what-to-demo.md`.
