#!/bin/bash

DIR_IN=$1
ptos_tmp_dir=$2
for f in $(ls ${DIR_IN}*.txt);
do
     ./procesar.sh $f $ptos_tmp_dir
done
