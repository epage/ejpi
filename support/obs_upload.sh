cp $3/$1_*.dsc $3/$1_*.tar.gz  ../../osc/home:epage:$2/$1

pushd ../../osc/home:epage:$2/$1

osc addremove && osc commit

popd
