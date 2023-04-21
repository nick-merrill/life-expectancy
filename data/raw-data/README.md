These were downloaded from the [CDC's publications](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/NVSR/70-19/).
More data can be found on the [CDC's life expectancy data page](https://www.cdc.gov/nchs/nvss/life-expectancy.htm#data).

To convert one of these to the proper CSV format
1. Remove all but the last header row (the one with `qx`, `lx`, etc.).
2. Name the first column `age`.
3. Export as a CSV. Then you can use that file as an input for the script.
